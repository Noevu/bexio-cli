"""Tests for order commands."""

import io
import json
import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from tests.helpers import capture_with_responses

ORDER = {
    "id": 47,
    "document_nr": "0047-000200",
    "title": "Hosting & Seed Service Paket",
    "is_recurring": True,
    "total": "3113.300000",
    "kb_item_status_id": 5,
}

REPETITION = {
    "start": "2026-01-01",
    "repetition": {"type": "yearly", "interval": 1},
}

INVOICE_CREATED = {"id": 123, "document_nr": "RE-00123"}


class TestOrdersList(unittest.TestCase):
    def test_shows_order_nr_and_title(self):
        out = capture_with_responses(["orders", "list"], [[ORDER]])
        self.assertIn("0047-000200", out)
        self.assertIn("Hosting & Seed Service Paket", out)

    def test_recurring_flag_in_url(self):
        captured = []

        def fake_request(self, method, path, params=None, body=None):
            captured.append((method, path, params))
            return [ORDER]

        with patch("bexio.client.BexioClient._request", fake_request), \
             patch("bexio.auth.get_token", return_value="FAKE"), \
             patch("sys.argv", ["bexio", "orders", "list", "--recurring"]), \
             patch("sys.stdout", io.StringIO()):
            from bexio.cli import main
            main()

        params = captured[0][2] or {}
        self.assertEqual(params.get("is_recurring"), "true")

    def test_json_output(self):
        out = capture_with_responses(["--json", "orders", "list"], [[ORDER]])
        parsed = json.loads(out)
        self.assertEqual(parsed[0]["id"], 47)

    def test_empty_list_no_crash(self):
        out = capture_with_responses(["orders", "list"], [[]])
        self.assertEqual(out, "")


class TestOrdersShow(unittest.TestCase):
    def test_shows_all_fields(self):
        out = capture_with_responses(["orders", "show", "47"], [ORDER, REPETITION])
        self.assertIn("0047-000200", out)
        self.assertIn("3113.30", out)
        self.assertIn("yearly", out)
        self.assertIn("2026-01-01", out)

    def test_json_output(self):
        out = capture_with_responses(["--json", "orders", "show", "47"], [ORDER, REPETITION])
        parsed = json.loads(out)
        self.assertIn("order", parsed)
        self.assertIn("repetition", parsed)
        self.assertEqual(parsed["order"]["id"], 47)


class TestOrdersCreateInvoice(unittest.TestCase):
    def test_shows_invoice_id_and_url(self):
        out = capture_with_responses(["orders", "create-invoice", "47"], [INVOICE_CREATED])
        self.assertIn("123", out)
        self.assertIn("RE-00123", out)
        self.assertIn("office.bexio.com", out)

    def test_posts_to_correct_endpoint(self):
        captured = []

        def fake_request(self, method, path, params=None, body=None):
            captured.append((method, path))
            return INVOICE_CREATED

        with patch("bexio.client.BexioClient._request", fake_request), \
             patch("bexio.auth.get_token", return_value="FAKE"), \
             patch("sys.argv", ["bexio", "orders", "create-invoice", "47"]), \
             patch("sys.stdout", io.StringIO()):
            from bexio.cli import main
            main()

        self.assertIn(("POST", "/kb_order/47/create_invoice"), captured)

    def test_json_output(self):
        out = capture_with_responses(["--json", "orders", "create-invoice", "47"], [INVOICE_CREATED])
        parsed = json.loads(out)
        self.assertEqual(parsed["id"], 123)


class TestOrdersSearch(unittest.TestCase):
    def test_shows_matching_order(self):
        out = capture_with_responses(["orders", "search", "Hosting"], [[ORDER]])
        self.assertIn("Hosting & Seed Service Paket", out)

    def test_posts_search_body(self):
        captured = []

        def fake_request(self, method, path, params=None, body=None, base=None, accept="application/json"):
            captured.append((method, path, body))
            return [ORDER]

        with patch("bexio.client.BexioClient._request", fake_request), \
             patch("bexio.auth.get_token", return_value="FAKE"), \
             patch("sys.argv", ["bexio", "orders", "search", "Hosting"]), \
             patch("sys.stdout", io.StringIO()):
            from bexio.cli import main
            main()

        method, path, body = captured[0]
        self.assertEqual(method, "POST")
        self.assertIn("kb_order/search", path)
        self.assertEqual(body[0]["field"], "name")
        self.assertEqual(body[0]["value"], "Hosting")
        self.assertEqual(body[0]["criteria"], "like")

    def test_empty_results(self):
        out = capture_with_responses(["orders", "search", "zzz"], [[]])
        self.assertIn("No orders", out)


class TestOrdersDelete(unittest.TestCase):
    def test_prints_confirmation(self):
        out = capture_with_responses(["orders", "delete", "47"], [{"success": True}])
        self.assertIn("deleted", out)
        self.assertIn("47", out)

    def test_deletes_correct_endpoint(self):
        captured = []

        def fake_request(self, method, path, params=None, body=None, base=None, accept="application/json"):
            captured.append((method, path))
            return {"success": True}

        with patch("bexio.client.BexioClient._request", fake_request), \
             patch("bexio.auth.get_token", return_value="FAKE"), \
             patch("sys.argv", ["bexio", "orders", "delete", "47"]), \
             patch("sys.stdout", io.StringIO()):
            from bexio.cli import main
            main()

        self.assertIn(("DELETE", "/kb_order/47"), captured)


class TestOrdersPdf(unittest.TestCase):
    def test_saves_file(self):
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            tmp = f.name
        os.unlink(tmp)

        def fake_request(self, method, path, params=None, body=None, base=None, accept="application/json"):
            return b"FAKEPDF"

        with patch("bexio.client.BexioClient._request", fake_request), \
             patch("bexio.auth.get_token", return_value="FAKE"), \
             patch("sys.argv", ["bexio", "orders", "pdf", "47", "--output", tmp]), \
             patch("sys.stdout", io.StringIO()):
            from bexio.cli import main
            main()

        self.assertTrue(os.path.exists(tmp))
        with open(tmp, "rb") as f:
            self.assertEqual(f.read(), b"FAKEPDF")
        os.unlink(tmp)

    def test_default_filename(self):
        default_file = "order_47.pdf"
        if os.path.exists(default_file):
            os.unlink(default_file)

        def fake_request(self, method, path, params=None, body=None, base=None, accept="application/json"):
            return b"FAKEPDF"

        with patch("bexio.client.BexioClient._request", fake_request), \
             patch("bexio.auth.get_token", return_value="FAKE"), \
             patch("sys.argv", ["bexio", "orders", "pdf", "47"]), \
             patch("sys.stdout", io.StringIO()):
            from bexio.cli import main
            main()

        self.assertTrue(os.path.exists(default_file))
        os.unlink(default_file)

    def test_custom_output_flag(self):
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            tmp = f.name
        os.unlink(tmp)

        def fake_request(self, method, path, params=None, body=None, base=None, accept="application/json"):
            return b"FAKEPDF"

        buf = io.StringIO()
        with patch("bexio.client.BexioClient._request", fake_request), \
             patch("bexio.auth.get_token", return_value="FAKE"), \
             patch("sys.argv", ["bexio", "orders", "pdf", "47", "--output", tmp]), \
             patch("sys.stdout", buf):
            from bexio.cli import main
            main()

        out = buf.getvalue()
        self.assertIn("Saved to", out)
        self.assertIn(tmp, out)
        if os.path.exists(tmp):
            os.unlink(tmp)


# ─── orders create / set-repetition ─────────────────────────────────────

CREATED_ORDER = {
    "id": 50,
    "document_nr": "0050-000223",
    "title": "Grow Service Paket",
}

VALID_ORDER_BODY = {
    "contact_id": 269,
    "user_id": 1,
    "title": "Grow Service Paket",
    "positions": [
        {"type": "KbPositionCustom",
         "text": "<strong>Grow</strong><br />Monthly service",
         "unit_price": "349.00", "amount": "1"},
    ],
}


class TestOrdersCreate(unittest.TestCase):
    def test_creates_from_file(self):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(VALID_ORDER_BODY, f)
            tmp = f.name
        try:
            out = capture_with_responses(["orders", "create", "--file", tmp], [CREATED_ORDER])
            self.assertIn("50", out)
            self.assertIn("0050-000223", out)
            self.assertIn("office.bexio.com/index.php/kb_order/show/id/50", out)
        finally:
            os.unlink(tmp)

    def test_rejects_markdown_in_header(self):
        bad = dict(VALID_ORDER_BODY, header="Hallo **Andreas**")
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(bad, f)
            tmp = f.name
        try:
            with patch("bexio.auth.get_token", return_value="FAKE"), \
                 patch("sys.argv", ["bexio", "orders", "create", "--file", tmp]), \
                 patch("sys.stdout", io.StringIO()):
                from bexio.cli import main
                with self.assertRaises(SystemExit) as cm:
                    main()
            self.assertIn("HTML, not Markdown", str(cm.exception))
        finally:
            os.unlink(tmp)

    def test_rejects_show_position_nr(self):
        bad = dict(VALID_ORDER_BODY, show_position_nr=True)
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(bad, f)
            tmp = f.name
        try:
            with patch("bexio.auth.get_token", return_value="FAKE"), \
                 patch("sys.argv", ["bexio", "orders", "create", "--file", tmp]), \
                 patch("sys.stdout", io.StringIO()):
                from bexio.cli import main
                with self.assertRaises(SystemExit) as cm:
                    main()
            self.assertIn("show_position_nr", str(cm.exception))
        finally:
            os.unlink(tmp)


class TestOrdersSetRepetition(unittest.TestCase):
    def test_explicit_flags_monthly(self):
        captured = []

        def fake_request(self, method, path, params=None, body=None, base=None, accept="application/json"):
            captured.append((method, path, body))
            return {"start": "2026-06-01",
                    "repetition": {"type": "monthly", "interval": 1, "schedule": "fixed_day"}}

        argv = ["bexio", "orders", "set-repetition", "50",
                "--start", "2026-06-01",
                "--type", "monthly", "--schedule", "fixed_day"]
        with patch("bexio.client.BexioClient._request", fake_request), \
             patch("bexio.auth.get_token", return_value="FAKE"), \
             patch("sys.argv", argv), \
             patch("sys.stdout", io.StringIO()):
            from bexio.cli import main
            main()

        method, path, body = captured[0]
        self.assertEqual(method, "POST")
        self.assertEqual(path, "/kb_order/50/repetition")
        self.assertEqual(body["start"], "2026-06-01")
        self.assertEqual(body["repetition"]["type"], "monthly")
        self.assertEqual(body["repetition"]["schedule"], "fixed_day")

    def test_monthly_without_schedule_fails(self):
        argv = ["bexio", "orders", "set-repetition", "50",
                "--start", "2026-06-01", "--type", "monthly"]
        with patch("bexio.auth.get_token", return_value="FAKE"), \
             patch("sys.argv", argv), \
             patch("sys.stdout", io.StringIO()):
            from bexio.cli import main
            with self.assertRaises(SystemExit) as cm:
                main()
        self.assertIn("--schedule", str(cm.exception))

    def test_weekly_with_weekdays(self):
        captured = []

        def fake_request(self, method, path, params=None, body=None, base=None, accept="application/json"):
            captured.append(body)
            return {"start": "2026-06-01",
                    "repetition": {"type": "weekly", "interval": 1,
                                   "weekdays": ["monday", "wednesday"]}}

        argv = ["bexio", "orders", "set-repetition", "50",
                "--start", "2026-06-01",
                "--type", "weekly", "--weekdays", "monday,wednesday"]
        with patch("bexio.client.BexioClient._request", fake_request), \
             patch("bexio.auth.get_token", return_value="FAKE"), \
             patch("sys.argv", argv), \
             patch("sys.stdout", io.StringIO()):
            from bexio.cli import main
            main()

        self.assertEqual(captured[0]["repetition"]["weekdays"], ["monday", "wednesday"])

    def test_from_file(self):
        body = {"start": "2026-06-01", "end": None,
                "repetition": {"type": "monthly", "interval": 1, "schedule": "fixed_day"}}
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(body, f)
            tmp = f.name
        try:
            captured = []

            def fake_request(self, method, path, params=None, body=None, base=None, accept="application/json"):
                captured.append((method, path, body))
                return {"start": "2026-06-01",
                        "repetition": {"type": "monthly", "interval": 1, "schedule": "fixed_day"}}

            argv = ["bexio", "orders", "set-repetition", "50", "--file", tmp]
            with patch("bexio.client.BexioClient._request", fake_request), \
                 patch("bexio.auth.get_token", return_value="FAKE"), \
                 patch("sys.argv", argv), \
                 patch("sys.stdout", io.StringIO()):
                from bexio.cli import main
                main()

            self.assertEqual(captured[0][1], "/kb_order/50/repetition")
            self.assertEqual(captured[0][2]["repetition"]["schedule"], "fixed_day")
        finally:
            os.unlink(tmp)


class TestOrdersUnsetRepetition(unittest.TestCase):
    def test_calls_delete_endpoint(self):
        captured = []

        def fake_request(self, method, path, params=None, body=None, base=None, accept="application/json"):
            captured.append((method, path))
            return {"success": True}

        with patch("bexio.client.BexioClient._request", fake_request), \
             patch("bexio.auth.get_token", return_value="FAKE"), \
             patch("sys.argv", ["bexio", "orders", "unset-repetition", "52"]), \
             patch("sys.stdout", io.StringIO()):
            from bexio.cli import main
            main()

        self.assertEqual(captured, [("DELETE", "/kb_order/52/repetition")])

    def test_human_output(self):
        out = capture_with_responses(
            ["orders", "unset-repetition", "52"], [{"success": True}]
        )
        self.assertIn("Order 52 recurrence removed", out)

    def test_json_output(self):
        out = capture_with_responses(
            ["--json", "orders", "unset-repetition", "52"], [{"success": True}]
        )
        parsed = json.loads(out)
        self.assertTrue(parsed["success"])

"""Tests for invoice commands."""

import io
import json
import os
import tempfile
import unittest
from unittest.mock import patch

from tests.helpers import capture_with_responses

INVOICE = {
    "id": 123,
    "document_nr": "RE-00123",
    "title": "Hosting Paket",
    "is_valid_from": "2026-05-01",
    "is_valid_to": "2026-05-31",
    "total": "3113.300000",
    "kb_item_status_id": 7,
}


class TestInvoiceList(unittest.TestCase):
    def test_table_shows_key_fields(self):
        out = capture_with_responses(["invoices", "list"], [[INVOICE]])
        self.assertIn("RE-00123", out)
        self.assertIn("Open", out)
        self.assertIn("3113.30", out)

    def test_status_filter_maps_to_id(self):
        captured = []

        def fake_request(self, method, path, params=None, body=None):
            captured.append(params or {})
            return []

        with patch("bexio.client.BexioClient._request", fake_request), \
             patch("bexio.auth.get_token", return_value="FAKE"), \
             patch("sys.argv", ["bexio", "invoices", "list", "--status", "open"]), \
             patch("sys.stdout", io.StringIO()):
            from bexio.cli import main
            main()

        self.assertEqual(captured[0].get("kb_item_status_id"), 7)

    def test_all_statuses_have_labels(self):
        from bexio.commands.invoices import STATUS_MAP, STATUS_LABELS
        for status_id in STATUS_MAP.values():
            self.assertIn(status_id, STATUS_LABELS)

    def test_json_output(self):
        out = capture_with_responses(["--json", "invoices", "list"], [[INVOICE]])
        parsed = json.loads(out)
        self.assertEqual(parsed[0]["id"], 123)

    def test_empty_list_no_crash(self):
        out = capture_with_responses(["invoices", "list"], [[]])
        self.assertEqual(out, "")


class TestInvoiceShow(unittest.TestCase):
    def test_shows_all_fields(self):
        out = capture_with_responses(["invoices", "show", "123"], [INVOICE])
        self.assertIn("123", out)
        self.assertIn("RE-00123", out)
        self.assertIn("Open", out)
        self.assertIn("3113.30", out)
        self.assertIn("office.bexio.com", out)

    def test_json_output(self):
        out = capture_with_responses(["--json", "invoices", "show", "123"], [INVOICE])
        parsed = json.loads(out)
        self.assertEqual(parsed["id"], 123)


class TestInvoiceSend(unittest.TestCase):
    def test_posts_to_send_endpoint(self):
        captured = []

        def fake_request(self, method, path, params=None, body=None):
            captured.append((method, path))
            return {}

        with patch("bexio.client.BexioClient._request", fake_request), \
             patch("bexio.auth.get_token", return_value="FAKE"), \
             patch("sys.argv", ["bexio", "invoices", "send", "123"]), \
             patch("sys.stdout", io.StringIO()):
            from bexio.cli import main
            main()

        self.assertIn(("POST", "/kb_invoice/123/send"), captured)

    def test_prints_confirmation(self):
        out = capture_with_responses(["invoices", "send", "123"], [{}])
        self.assertIn("123", out)
        self.assertIn("sent", out)


class TestInvoiceMarkSent(unittest.TestCase):
    def test_posts_to_mark_as_sent_endpoint(self):
        captured = []

        def fake_request(self, method, path, params=None, body=None):
            captured.append((method, path))
            return {}

        with patch("bexio.client.BexioClient._request", fake_request), \
             patch("bexio.auth.get_token", return_value="FAKE"), \
             patch("sys.argv", ["bexio", "invoices", "mark-sent", "123"]), \
             patch("sys.stdout", io.StringIO()):
            from bexio.cli import main
            main()

        self.assertIn(("POST", "/kb_invoice/123/mark_as_sent"), captured)


class TestInvoiceCancel(unittest.TestCase):
    def test_posts_to_cancel_endpoint(self):
        captured = []

        def fake_request(self, method, path, params=None, body=None):
            captured.append((method, path))
            return {}

        with patch("bexio.client.BexioClient._request", fake_request), \
             patch("bexio.auth.get_token", return_value="FAKE"), \
             patch("sys.argv", ["bexio", "invoices", "cancel", "123"]), \
             patch("sys.stdout", io.StringIO()):
            from bexio.cli import main
            main()

        self.assertIn(("POST", "/kb_invoice/123/cancel"), captured)


class TestInvoiceIssue(unittest.TestCase):
    def test_posts_to_issue_endpoint(self):
        captured = []

        def fake_request(self, method, path, params=None, body=None):
            captured.append((method, path))
            return {}

        with patch("bexio.client.BexioClient._request", fake_request), \
             patch("bexio.auth.get_token", return_value="FAKE"), \
             patch("sys.argv", ["bexio", "invoices", "issue", "123"]), \
             patch("sys.stdout", io.StringIO()):
            from bexio.cli import main
            main()

        self.assertIn(("POST", "/kb_invoice/123/issue"), captured)


class TestInvoicesSearch(unittest.TestCase):
    def test_shows_matching_invoice(self):
        out = capture_with_responses(["invoices", "search", "Hosting"], [[INVOICE]])
        self.assertIn("RE-00123", out)

    def test_posts_search_body(self):
        captured = []

        def fake_request(self, method, path, params=None, body=None, base=None, accept="application/json"):
            captured.append((method, path, body))
            return [INVOICE]

        with patch("bexio.client.BexioClient._request", fake_request), \
             patch("bexio.auth.get_token", return_value="FAKE"), \
             patch("sys.argv", ["bexio", "invoices", "search", "Hosting"]), \
             patch("sys.stdout", io.StringIO()):
            from bexio.cli import main
            main()

        method, path, body = captured[0]
        self.assertEqual(method, "POST")
        self.assertIn("kb_invoice/search", path)
        self.assertEqual(body[0]["field"], "title")
        self.assertEqual(body[0]["value"], "Hosting")
        self.assertEqual(body[0]["criteria"], "like")

    def test_empty_results(self):
        out = capture_with_responses(["invoices", "search", "zzz"], [[]])
        self.assertIn("No invoices", out)


class TestInvoicesDelete(unittest.TestCase):
    def test_prints_confirmation(self):
        out = capture_with_responses(["invoices", "delete", "123"], [{"success": True}])
        self.assertIn("deleted", out)
        self.assertIn("123", out)

    def test_deletes_correct_endpoint(self):
        captured = []

        def fake_request(self, method, path, params=None, body=None, base=None, accept="application/json"):
            captured.append((method, path))
            return {"success": True}

        with patch("bexio.client.BexioClient._request", fake_request), \
             patch("bexio.auth.get_token", return_value="FAKE"), \
             patch("sys.argv", ["bexio", "invoices", "delete", "123"]), \
             patch("sys.stdout", io.StringIO()):
            from bexio.cli import main
            main()

        self.assertIn(("DELETE", "/kb_invoice/123"), captured)


class TestInvoicesCopy(unittest.TestCase):
    def test_prints_new_id(self):
        out = capture_with_responses(["invoices", "copy", "123"], [{"id": 456, "document_nr": "RE-00456"}])
        self.assertIn("456", out)

    def test_posts_copy_endpoint(self):
        captured = []

        def fake_request(self, method, path, params=None, body=None, base=None, accept="application/json"):
            captured.append((method, path))
            return {"id": 456}

        with patch("bexio.client.BexioClient._request", fake_request), \
             patch("bexio.auth.get_token", return_value="FAKE"), \
             patch("sys.argv", ["bexio", "invoices", "copy", "123"]), \
             patch("sys.stdout", io.StringIO()):
            from bexio.cli import main
            main()

        self.assertIn(("POST", "/kb_invoice/123/copy"), captured)


class TestInvoicesPdf(unittest.TestCase):
    def test_saves_file(self):
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            tmp = f.name
        os.unlink(tmp)

        def fake_request(self, method, path, params=None, body=None, base=None, accept="application/json"):
            return b"FAKEPDF"

        with patch("bexio.client.BexioClient._request", fake_request), \
             patch("bexio.auth.get_token", return_value="FAKE"), \
             patch("sys.argv", ["bexio", "invoices", "pdf", "123", "--output", tmp]), \
             patch("sys.stdout", io.StringIO()):
            from bexio.cli import main
            main()

        self.assertTrue(os.path.exists(tmp))
        with open(tmp, "rb") as f:
            self.assertEqual(f.read(), b"FAKEPDF")
        os.unlink(tmp)

    def test_default_filename(self):
        default_file = "invoice_123.pdf"
        if os.path.exists(default_file):
            os.unlink(default_file)

        def fake_request(self, method, path, params=None, body=None, base=None, accept="application/json"):
            return b"FAKEPDF"

        with patch("bexio.client.BexioClient._request", fake_request), \
             patch("bexio.auth.get_token", return_value="FAKE"), \
             patch("sys.argv", ["bexio", "invoices", "pdf", "123"]), \
             patch("sys.stdout", io.StringIO()):
            from bexio.cli import main
            main()

        self.assertTrue(os.path.exists(default_file))
        os.unlink(default_file)


class TestInvoicesRevertIssue(unittest.TestCase):
    def test_prints_confirmation(self):
        out = capture_with_responses(["invoices", "revert-issue", "123"], [{"success": True}])
        self.assertIn("123", out)
        self.assertIn("draft", out)

    def test_posts_correct_endpoint(self):
        captured = []

        def fake_request(self, method, path, params=None, body=None, base=None, accept="application/json"):
            captured.append((method, path))
            return {"success": True}

        with patch("bexio.client.BexioClient._request", fake_request), \
             patch("bexio.auth.get_token", return_value="FAKE"), \
             patch("sys.argv", ["bexio", "invoices", "revert-issue", "123"]), \
             patch("sys.stdout", io.StringIO()):
            from bexio.cli import main
            main()

        self.assertIn(("POST", "/kb_invoice/123/revert_issue"), captured)


# ─── invoices create ────────────────────────────────────────────────────

import json as _json
import os as _os
import tempfile as _tempfile

CREATED_INV = {"id": 200, "document_nr": "RE-00200", "title": "Test Invoice"}
VALID_INVOICE_BODY = {
    "contact_id": 269,
    "user_id": 1,
    "title": "Test Invoice",
    "is_valid_from": "2026-05-04",
    "positions": [
        {"type": "KbPositionCustom",
         "text": "<strong>Item</strong><br />Desc",
         "unit_price": "100.00", "amount": "1"},
    ],
}


class TestInvoicesCreate(unittest.TestCase):
    def test_creates_from_file(self):
        with _tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            _json.dump(VALID_INVOICE_BODY, f)
            tmp = f.name
        try:
            out = capture_with_responses(["invoices", "create", "--file", tmp], [CREATED_INV])
            self.assertIn("200", out)
            self.assertIn("RE-00200", out)
            self.assertIn("kb_invoice/show/id/200", out)
        finally:
            _os.unlink(tmp)

    def test_rejects_markdown_in_header(self):
        bad = dict(VALID_INVOICE_BODY, header="**Bold**")
        with _tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            _json.dump(bad, f)
            tmp = f.name
        try:
            with patch("bexio.auth.get_token", return_value="FAKE"), \
                 patch("sys.argv", ["bexio", "invoices", "create", "--file", tmp]), \
                 patch("sys.stdout", io.StringIO()):
                from bexio.cli import main
                with self.assertRaises(SystemExit) as cm:
                    main()
            self.assertIn("HTML, not Markdown", str(cm.exception))
        finally:
            _os.unlink(tmp)

    def test_missing_is_valid_from(self):
        bad = {k: v for k, v in VALID_INVOICE_BODY.items() if k != "is_valid_from"}
        with _tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            _json.dump(bad, f)
            tmp = f.name
        try:
            with patch("bexio.auth.get_token", return_value="FAKE"), \
                 patch("sys.argv", ["bexio", "invoices", "create", "--file", tmp]), \
                 patch("sys.stdout", io.StringIO()):
                from bexio.cli import main
                with self.assertRaises(SystemExit) as cm:
                    main()
            self.assertIn("is_valid_from", str(cm.exception))
        finally:
            _os.unlink(tmp)

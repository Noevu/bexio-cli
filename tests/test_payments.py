"""Tests for payment commands."""

import io
import json
import unittest
from unittest.mock import patch

from tests.helpers import capture_with_responses

PAYMENT = {
    "id": 10,
    "date": "2024-03-01",
    "value": "100.00",
    "payment_type_id": 1,
    "kb_bill_id": 99,
    "bank_account_id": None,
}


class TestPaymentsList(unittest.TestCase):
    def test_shows_payment_amount(self):
        out = capture_with_responses(["payments", "list", "5"], [[PAYMENT]])
        self.assertIn("100.00", out)

    def test_shows_payment_date(self):
        out = capture_with_responses(["payments", "list", "5"], [[PAYMENT]])
        self.assertIn("2024-03-01", out)

    def test_json_output(self):
        out = capture_with_responses(["--json", "payments", "list", "5"], [[PAYMENT]])
        parsed = json.loads(out)
        self.assertEqual(parsed[0]["id"], 10)

    def test_empty_list_no_crash(self):
        out = capture_with_responses(["payments", "list", "5"], [[]])
        self.assertEqual(out, "")


class TestPaymentsShow(unittest.TestCase):
    def test_shows_id_and_amount(self):
        out = capture_with_responses(["payments", "show", "5", "10"], [PAYMENT])
        self.assertIn("10", out)
        self.assertIn("100.00", out)

    def test_shows_date(self):
        out = capture_with_responses(["payments", "show", "5", "10"], [PAYMENT])
        self.assertIn("2024-03-01", out)

    def test_json_output(self):
        out = capture_with_responses(["--json", "payments", "show", "5", "10"], [PAYMENT])
        parsed = json.loads(out)
        self.assertEqual(parsed["id"], 10)


class TestPaymentsCreate(unittest.TestCase):
    def test_prints_confirmation(self):
        response = {"id": 10, **PAYMENT}
        out = capture_with_responses(
            ["payments", "create", "5", "--amount", "100.00", "--date", "2024-03-01"],
            [response],
        )
        self.assertIn("created", out)

    def test_posts_correct_body(self):
        captured = []

        def fake_request(self, method, path, params=None, body=None, base=None, accept="application/json"):
            captured.append({"method": method, "path": path, "body": body})
            return {"id": 10, **PAYMENT}

        with patch("bexio.client.BexioClient._request", fake_request), \
             patch("bexio.auth.get_token", return_value="FAKE"), \
             patch("sys.argv", ["bexio", "payments", "create", "5",
                                "--amount", "100.00", "--date", "2024-03-01",
                                "--payment-type-id", "1"]), \
             patch("sys.stdout", io.StringIO()):
            from bexio.cli import main
            main()

        self.assertEqual(len(captured), 1)
        body = captured[0]["body"]
        self.assertEqual(body["value"], "100.00")
        self.assertEqual(body["date"], "2024-03-01")
        self.assertEqual(body["payment_type_id"], 1)
        self.assertIn("/kb_invoice/5/payment", captured[0]["path"])

    def test_required_args_missing(self):
        out = capture_with_responses(["payments", "create", "5", "--date", "2024-03-01"], [{}])
        # --amount is required; argparse should exit (captured as SystemExit)
        # The output is irrelevant — just ensure it doesn't crash with an unhandled exception
        # (capture_with_responses swallows SystemExit)
        self.assertIsInstance(out, str)

    def test_missing_amount_exits(self):
        import sys as _sys
        buf = io.StringIO()
        with patch("sys.argv", ["bexio", "payments", "create", "5", "--date", "2024-03-01"]), \
             patch("bexio.auth.get_token", return_value="FAKE"), \
             patch("sys.stderr", buf):
            with self.assertRaises(SystemExit):
                from bexio.cli import main
                # Re-import to avoid cached parse
                import importlib
                import bexio.cli as cli_mod
                importlib.reload(cli_mod)
                cli_mod.main()


class TestPaymentsDelete(unittest.TestCase):
    def test_prints_confirmation(self):
        out = capture_with_responses(["payments", "delete", "5", "10"], [{}])
        self.assertIn("10", out)
        self.assertIn("deleted", out)

    def test_deletes_correct_endpoint(self):
        captured = []

        def fake_request(self, method, path, params=None, body=None, base=None, accept="application/json"):
            captured.append({"method": method, "path": path})
            return {}

        with patch("bexio.client.BexioClient._request", fake_request), \
             patch("bexio.auth.get_token", return_value="FAKE"), \
             patch("sys.argv", ["bexio", "payments", "delete", "5", "10"]), \
             patch("sys.stdout", io.StringIO()):
            from bexio.cli import main
            main()

        self.assertEqual(captured[0]["method"], "DELETE")
        self.assertIn("/kb_invoice/5/payment/10", captured[0]["path"])

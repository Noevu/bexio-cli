"""Tests for payment_types commands."""

import json
import unittest

from tests.helpers import capture_with_responses

PAYMENT_TYPE = {
    "id": 1,
    "name": "Bank Transfer",
}

PAYMENT_TYPE_2 = {
    "id": 2,
    "name": "Cash",
}


class TestPaymentTypesList(unittest.TestCase):
    def test_table_output_shows_id_and_name(self):
        out = capture_with_responses(["payment-types", "list"], [[PAYMENT_TYPE]])
        self.assertIn("1", out)
        self.assertIn("Bank Transfer", out)

    def test_table_shows_multiple_rows(self):
        out = capture_with_responses(["payment-types", "list"], [[PAYMENT_TYPE, PAYMENT_TYPE_2]])
        self.assertIn("Bank Transfer", out)
        self.assertIn("Cash", out)

    def test_json_flag(self):
        out = capture_with_responses(["--json", "payment-types", "list"], [[PAYMENT_TYPE]])
        parsed = json.loads(out)
        self.assertEqual(parsed[0]["id"], 1)
        self.assertEqual(parsed[0]["name"], "Bank Transfer")

    def test_empty_list_no_crash(self):
        out = capture_with_responses(["payment-types", "list"], [[]])
        # Should not raise; output may be empty or a message — just no exception
        self.assertIsInstance(out, str)


class TestPaymentTypesShow(unittest.TestCase):
    def test_shows_id_and_name(self):
        out = capture_with_responses(["payment-types", "show", "1"], [PAYMENT_TYPE])
        self.assertIn("1", out)
        self.assertIn("Bank Transfer", out)

    def test_correct_endpoint_called(self):
        captured = []

        def fake_request(self, method, path, params=None, body=None):
            captured.append((method, path))
            return PAYMENT_TYPE

        import io
        from unittest.mock import patch
        buf = io.StringIO()
        with patch("sys.argv", ["bexio", "payment-types", "show", "1"]), \
             patch("bexio.auth.get_token", return_value="FAKE"), \
             patch("bexio.client.BexioClient._request", fake_request), \
             patch("sys.stdout", buf):
            from bexio.cli import main
            main()

        self.assertEqual(len(captured), 1)
        method, path = captured[0]
        self.assertEqual(method, "GET")
        self.assertIn("/payment_type/1", path)

    def test_json_flag(self):
        out = capture_with_responses(["--json", "payment-types", "show", "1"], [PAYMENT_TYPE])
        parsed = json.loads(out)
        self.assertEqual(parsed["id"], 1)
        self.assertEqual(parsed["name"], "Bank Transfer")

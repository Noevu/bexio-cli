"""Tests for order commands."""

import io
import json
import sys
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

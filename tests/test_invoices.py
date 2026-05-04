"""Tests for invoice commands."""

import io
import json
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

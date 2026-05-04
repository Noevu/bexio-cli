"""Tests for bills commands."""

import io
import json
import unittest
from unittest.mock import patch

from tests.helpers import capture_with_responses

BILL = {
    "id": "bill-uuid-001",
    "document_no": "RG-2024-001",
    "title": "Server Hosting Q1",
    "total_gross": "1200.00",
    "total_net": "1111.11",
    "currency_code": "CHF",
    "status": "draft",
    "vendor_ref": None,
    "contact_id": 42,
    "is_pending_payment": False,
    "created_at": "2024-01-15T10:00:00Z",
    "updated_at": "2024-01-15T10:00:00Z",
}

V4_BASE = "https://api.bexio.com/4.0"


class TestBillsList(unittest.TestCase):
    def test_shows_bill_title(self):
        out = capture_with_responses(["bills", "list"], [[BILL]])
        self.assertIn("Server Hosting Q1", out)

    def test_shows_document_no(self):
        out = capture_with_responses(["bills", "list"], [[BILL]])
        self.assertIn("RG-2024-001", out)

    def test_shows_total(self):
        out = capture_with_responses(["bills", "list"], [[BILL]])
        self.assertIn("1200.00", out)

    def test_json_output(self):
        out = capture_with_responses(["--json", "bills", "list"], [[BILL]])
        parsed = json.loads(out)
        self.assertEqual(parsed[0]["id"], "bill-uuid-001")

    def test_uses_v4_endpoint(self):
        captured = []

        def fake_request(self, method, path, params=None, body=None, base=None, accept="application/json"):
            captured.append(base)
            return []

        with patch("bexio.client.BexioClient._request", fake_request), \
             patch("bexio.auth.get_token", return_value="FAKE"), \
             patch("sys.argv", ["bexio", "bills", "list"]), \
             patch("sys.stdout", io.StringIO()):
            from bexio.cli import main
            main()

        self.assertEqual(captured[0], V4_BASE)

    def test_empty_list_shows_no_bills(self):
        out = capture_with_responses(["bills", "list"], [[]])
        self.assertIn("No bills found", out)


class TestBillsShow(unittest.TestCase):
    def test_shows_id_and_title(self):
        out = capture_with_responses(["bills", "show", "bill-uuid-001"], [BILL])
        self.assertIn("bill-uuid-001", out)
        self.assertIn("Server Hosting Q1", out)

    def test_shows_total(self):
        out = capture_with_responses(["bills", "show", "bill-uuid-001"], [BILL])
        self.assertIn("1200.00", out)

    def test_json_output(self):
        out = capture_with_responses(["--json", "bills", "show", "bill-uuid-001"], [BILL])
        parsed = json.loads(out)
        self.assertEqual(parsed["id"], "bill-uuid-001")


class TestBillsCreate(unittest.TestCase):
    def test_prints_confirmation(self):
        out = capture_with_responses(["bills", "create", "--title", "Test Bill"], [BILL])
        self.assertIn("bill-uuid-001", out)
        self.assertIn("created", out)

    def test_posts_correct_body(self):
        captured = []

        def fake_request(self, method, path, params=None, body=None, base=None, accept="application/json"):
            captured.append((method, path, body))
            return BILL

        with patch("bexio.client.BexioClient._request", fake_request), \
             patch("bexio.auth.get_token", return_value="FAKE"), \
             patch("sys.argv", ["bexio", "bills", "create", "--title", "My Bill", "--total", "500.00", "--contact-id", "10"]), \
             patch("sys.stdout", io.StringIO()):
            from bexio.cli import main
            main()

        method, path, body = captured[0]
        self.assertEqual(method, "POST")
        self.assertEqual(path, "/purchase/bills")
        self.assertEqual(body["title"], "My Bill")
        self.assertEqual(body["total_gross"], "500.00")
        self.assertEqual(body["contact_id"], 10)

    def test_uses_v4_endpoint(self):
        captured = []

        def fake_request(self, method, path, params=None, body=None, base=None, accept="application/json"):
            captured.append(base)
            return BILL

        with patch("bexio.client.BexioClient._request", fake_request), \
             patch("bexio.auth.get_token", return_value="FAKE"), \
             patch("sys.argv", ["bexio", "bills", "create", "--title", "Test"]), \
             patch("sys.stdout", io.StringIO()):
            from bexio.cli import main
            main()

        self.assertEqual(captured[0], V4_BASE)


class TestBillsEdit(unittest.TestCase):
    def test_prints_confirmation(self):
        out = capture_with_responses(["bills", "edit", "bill-uuid-001", "--title", "Updated"], [BILL])
        self.assertIn("bill-uuid-001", out)
        self.assertIn("updated", out)

    def test_puts_correct_endpoint(self):
        captured = []

        def fake_request(self, method, path, params=None, body=None, base=None, accept="application/json"):
            captured.append((method, path, body))
            return BILL

        with patch("bexio.client.BexioClient._request", fake_request), \
             patch("bexio.auth.get_token", return_value="FAKE"), \
             patch("sys.argv", ["bexio", "bills", "edit", "bill-uuid-001", "--title", "New Title"]), \
             patch("sys.stdout", io.StringIO()):
            from bexio.cli import main
            main()

        method, path, body = captured[0]
        self.assertEqual(method, "PUT")
        self.assertEqual(path, "/purchase/bills/bill-uuid-001")
        self.assertEqual(body["title"], "New Title")

    def test_uses_v4_endpoint(self):
        captured = []

        def fake_request(self, method, path, params=None, body=None, base=None, accept="application/json"):
            captured.append(base)
            return BILL

        with patch("bexio.client.BexioClient._request", fake_request), \
             patch("bexio.auth.get_token", return_value="FAKE"), \
             patch("sys.argv", ["bexio", "bills", "edit", "bill-uuid-001", "--title", "X"]), \
             patch("sys.stdout", io.StringIO()):
            from bexio.cli import main
            main()

        self.assertEqual(captured[0], V4_BASE)


class TestBillsDelete(unittest.TestCase):
    def test_prints_confirmation(self):
        out = capture_with_responses(["bills", "delete", "bill-uuid-001"], [{}])
        self.assertIn("bill-uuid-001", out)
        self.assertIn("deleted", out)

    def test_deletes_correct_endpoint(self):
        captured = []

        def fake_request(self, method, path, params=None, body=None, base=None, accept="application/json"):
            captured.append((method, path))
            return {}

        with patch("bexio.client.BexioClient._request", fake_request), \
             patch("bexio.auth.get_token", return_value="FAKE"), \
             patch("sys.argv", ["bexio", "bills", "delete", "bill-uuid-001"]), \
             patch("sys.stdout", io.StringIO()):
            from bexio.cli import main
            main()

        method, path = captured[0]
        self.assertEqual(method, "DELETE")
        self.assertEqual(path, "/purchase/bills/bill-uuid-001")

    def test_uses_v4_endpoint(self):
        captured = []

        def fake_request(self, method, path, params=None, body=None, base=None, accept="application/json"):
            captured.append(base)
            return {}

        with patch("bexio.client.BexioClient._request", fake_request), \
             patch("bexio.auth.get_token", return_value="FAKE"), \
             patch("sys.argv", ["bexio", "bills", "delete", "bill-uuid-001"]), \
             patch("sys.stdout", io.StringIO()):
            from bexio.cli import main
            main()

        self.assertEqual(captured[0], V4_BASE)


class TestBillsMarkPaid(unittest.TestCase):
    def test_prints_confirmation(self):
        out = capture_with_responses(["bills", "mark-paid", "bill-uuid-001"], [{}])
        self.assertIn("bill-uuid-001", out)
        self.assertIn("paid", out)

    def test_posts_actions_endpoint(self):
        captured = []

        def fake_request(self, method, path, params=None, body=None, base=None, accept="application/json"):
            captured.append((method, path))
            return {}

        with patch("bexio.client.BexioClient._request", fake_request), \
             patch("bexio.auth.get_token", return_value="FAKE"), \
             patch("sys.argv", ["bexio", "bills", "mark-paid", "bill-uuid-001"]), \
             patch("sys.stdout", io.StringIO()):
            from bexio.cli import main
            main()

        method, path = captured[0]
        self.assertEqual(method, "POST")
        self.assertTrue(path.endswith("/actions"), f"Expected path to end with /actions, got: {path}")

    def test_posts_mark_as_paid_action(self):
        captured = []

        def fake_request(self, method, path, params=None, body=None, base=None, accept="application/json"):
            captured.append(body)
            return {}

        with patch("bexio.client.BexioClient._request", fake_request), \
             patch("bexio.auth.get_token", return_value="FAKE"), \
             patch("sys.argv", ["bexio", "bills", "mark-paid", "bill-uuid-001"]), \
             patch("sys.stdout", io.StringIO()):
            from bexio.cli import main
            main()

        self.assertEqual(captured[0]["action"], "mark_as_paid")

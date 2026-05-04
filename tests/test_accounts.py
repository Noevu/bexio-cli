"""Tests for accounts and account-groups commands."""

import io
import json
import unittest
from unittest.mock import patch

from tests.helpers import capture_with_responses

ACCOUNT = {
    "id": 1,
    "account_no": "1000",
    "name": "Kasse",
    "account_type": 1,
    "is_active": True,
    "tax_id": None,
}

ACCOUNT_INACTIVE = {
    "id": 2,
    "account_no": "1001",
    "name": "Bank (inaktiv)",
    "account_type": 1,
    "is_active": False,
    "tax_id": None,
}

ACCOUNT_GROUP = {
    "id": 10,
    "account_no": "1",
    "name": "Aktiven",
    "is_active": True,
}


class TestAccountsList(unittest.TestCase):
    def test_table_output(self):
        out = capture_with_responses(["accounts", "list"], [[ACCOUNT]])
        self.assertIn("1000", out)
        self.assertIn("Kasse", out)

    def test_active_filter_removes_inactive(self):
        out = capture_with_responses(
            ["accounts", "list", "--active"], [[ACCOUNT, ACCOUNT_INACTIVE]]
        )
        self.assertIn("Kasse", out)
        self.assertNotIn("Bank (inaktiv)", out)

    def test_active_filter_keeps_active(self):
        out = capture_with_responses(
            ["accounts", "list", "--active"], [[ACCOUNT, ACCOUNT_INACTIVE]]
        )
        self.assertIn("Kasse", out)

    def test_json_flag(self):
        out = capture_with_responses(["--json", "accounts", "list"], [[ACCOUNT]])
        parsed = json.loads(out)
        self.assertEqual(parsed[0]["id"], 1)


class TestAccountsShow(unittest.TestCase):
    def test_fields_shown(self):
        out = capture_with_responses(["accounts", "show", "1"], [ACCOUNT])
        self.assertIn("1", out)
        self.assertIn("1000", out)
        self.assertIn("Kasse", out)

    def test_correct_endpoint(self):
        captured = []

        def fake_request(self, method, path, params=None, body=None):
            captured.append((method, path))
            return ACCOUNT

        with patch("bexio.client.BexioClient._request", fake_request), \
             patch("bexio.auth.get_token", return_value="FAKE"), \
             patch("sys.argv", ["bexio", "accounts", "show", "1"]), \
             patch("sys.stdout", io.StringIO()):
            from bexio.cli import main
            main()

        _, path = captured[0]
        self.assertIn("/accounts/1", path)

    def test_json_flag(self):
        out = capture_with_responses(["--json", "accounts", "show", "1"], [ACCOUNT])
        parsed = json.loads(out)
        self.assertEqual(parsed["id"], 1)
        self.assertEqual(parsed["account_no"], "1000")


class TestAccountsSearch(unittest.TestCase):
    def test_posts_search_body(self):
        captured = []

        def fake_request(self, method, path, params=None, body=None):
            captured.append((method, path, body))
            return [ACCOUNT]

        with patch("bexio.client.BexioClient._request", fake_request), \
             patch("bexio.auth.get_token", return_value="FAKE"), \
             patch("sys.argv", ["bexio", "accounts", "search", "Kasse"]), \
             patch("sys.stdout", io.StringIO()):
            from bexio.cli import main
            main()

        method, path, body = captured[0]
        self.assertEqual(method, "POST")
        self.assertIn("accounts/search", path)
        self.assertEqual(body[0]["value"], "Kasse")
        self.assertEqual(body[0]["field"], "name")
        self.assertEqual(body[0]["criteria"], "like")

    def test_no_results_message(self):
        out = capture_with_responses(["accounts", "search", "xyz"], [[]])
        self.assertIn("No accounts", out)

    def test_json_flag(self):
        out = capture_with_responses(["--json", "accounts", "search", "Kasse"], [[ACCOUNT]])
        parsed = json.loads(out)
        self.assertEqual(parsed[0]["id"], 1)


class TestAccountGroupsList(unittest.TestCase):
    def test_table_output(self):
        out = capture_with_responses(["account-groups", "list"], [[ACCOUNT_GROUP]])
        self.assertIn("10", out)
        self.assertIn("Aktiven", out)

    def test_json_flag(self):
        out = capture_with_responses(["--json", "account-groups", "list"], [[ACCOUNT_GROUP]])
        parsed = json.loads(out)
        self.assertEqual(parsed[0]["id"], 10)
        self.assertEqual(parsed[0]["name"], "Aktiven")

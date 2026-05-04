"""Tests for accounting commands: taxes, accounts, account-groups, vat-periods."""

import io
import json
import unittest
from unittest.mock import patch

from tests.helpers import capture_with_responses

TAX = {
    "id": 1,
    "uuid": "deadbeef-0000-0000-0000-000000000001",
    "name": "MWST 8.1%",
    "code": "UN 8.1",
    "digit": "200",
    "type": "tax_type_expenditure",
    "is_active": True,
    "display_name": "MWST 8.1%",
    "net_tax_value": "8.1",
    "value": "8.1",
    "account_id": 10,
    "tax_settlement_type": "tax_settlement_type_not_applicable",
    "start_year": None,
    "end_year": None,
    "start_month": None,
    "end_month": None,
    "is_deletable": False,
}

TAX2 = {
    "id": 2,
    "uuid": "deadbeef-0000-0000-0000-000000000002",
    "name": "MWST 2.6%",
    "code": "LS 2.6",
    "digit": "201",
    "type": "tax_type_expenditure",
    "is_active": True,
    "display_name": "MWST 2.6%",
    "net_tax_value": "2.6",
    "value": "2.6",
    "account_id": 11,
    "tax_settlement_type": "tax_settlement_type_not_applicable",
    "start_year": None,
    "end_year": None,
    "start_month": None,
    "end_month": None,
    "is_deletable": False,
}

ACCOUNT = {
    "id": 100,
    "account_no": "1000",
    "name": "Kasse",
    "account_group_id": 10,
    "account_type": "1",
    "tax_id": None,
    "is_active": True,
    "is_locked": False,
}

ACCOUNT_GROUP = {
    "id": 10,
    "account_no": "10",
    "name": "Umlaufvermögen",
    "parent_fibu_account_group_id": None,
    "is_active": True,
    "is_locked": False,
}

VAT_PERIOD = {
    "id": 5,
    "start": "2024-01-01",
    "end": "2024-12-31",
    "status": "vat_period_status_closed",
}


# ─── taxes list ──────────────────────────────────────────────────────────────

class TestTaxesList(unittest.TestCase):
    def test_shows_tax_name(self):
        out = capture_with_responses(["taxes", "list"], [[TAX]])
        self.assertIn("MWST 8.1%", out)

    def test_shows_multiple_taxes(self):
        out = capture_with_responses(["taxes", "list"], [[TAX, TAX2]])
        self.assertIn("MWST 8.1%", out)
        self.assertIn("MWST 2.6%", out)

    def test_shows_tax_value(self):
        out = capture_with_responses(["taxes", "list"], [[TAX]])
        self.assertIn("8.1", out)

    def test_json_output(self):
        out = capture_with_responses(["--json", "taxes", "list"], [[TAX]])
        parsed = json.loads(out)
        self.assertEqual(parsed[0]["id"], 1)

    def test_uses_v3_endpoint(self):
        captured = []

        def fake_request(self, method, path, params=None, body=None, base=None):
            captured.append((method, path, base))
            return [TAX]

        buf = io.StringIO()
        with patch("bexio.client.BexioClient._request", fake_request), \
             patch("bexio.auth.get_token", return_value="FAKE"), \
             patch("sys.argv", ["bexio", "taxes", "list"]), \
             patch("sys.stdout", buf):
            from bexio.cli import main
            main()

        _, path, base = captured[0]
        self.assertIn("/taxes", path)
        self.assertEqual(base, "https://api.bexio.com/3.0")

    def test_empty_list_shows_no_taxes(self):
        out = capture_with_responses(["taxes", "list"], [[]])
        self.assertIn("No taxes", out)


# ─── taxes show ──────────────────────────────────────────────────────────────

class TestTaxesShow(unittest.TestCase):
    def test_shows_id_and_name(self):
        out = capture_with_responses(["taxes", "show", "1"], [TAX])
        self.assertIn("1", out)
        self.assertIn("MWST 8.1%", out)

    def test_shows_value(self):
        out = capture_with_responses(["taxes", "show", "1"], [TAX])
        self.assertIn("8.1", out)

    def test_shows_code(self):
        out = capture_with_responses(["taxes", "show", "1"], [TAX])
        self.assertIn("UN 8.1", out)

    def test_json_output(self):
        out = capture_with_responses(["--json", "taxes", "show", "1"], [TAX])
        parsed = json.loads(out)
        self.assertEqual(parsed["id"], 1)

    def test_uses_v3_endpoint(self):
        captured = []

        def fake_request(self, method, path, params=None, body=None, base=None):
            captured.append((method, path, base))
            return TAX

        buf = io.StringIO()
        with patch("bexio.client.BexioClient._request", fake_request), \
             patch("bexio.auth.get_token", return_value="FAKE"), \
             patch("sys.argv", ["bexio", "taxes", "show", "1"]), \
             patch("sys.stdout", buf):
            from bexio.cli import main
            main()

        _, path, base = captured[0]
        self.assertIn("/taxes/1", path)
        self.assertEqual(base, "https://api.bexio.com/3.0")


# ─── accounts list ───────────────────────────────────────────────────────────

class TestAccountsList(unittest.TestCase):
    def test_shows_account_name(self):
        out = capture_with_responses(["accounts", "list"], [[ACCOUNT]])
        self.assertIn("Kasse", out)

    def test_shows_account_no(self):
        out = capture_with_responses(["accounts", "list"], [[ACCOUNT]])
        self.assertIn("1000", out)

    def test_json_output(self):
        out = capture_with_responses(["--json", "accounts", "list"], [[ACCOUNT]])
        parsed = json.loads(out)
        self.assertEqual(parsed[0]["id"], 100)

    def test_limit_passed_as_param(self):
        captured = []

        def fake_request(self, method, path, params=None, body=None, base=None):
            captured.append((method, path, params))
            return [ACCOUNT]

        buf = io.StringIO()
        with patch("bexio.client.BexioClient._request", fake_request), \
             patch("bexio.auth.get_token", return_value="FAKE"), \
             patch("sys.argv", ["bexio", "accounts", "list", "--limit", "50"]), \
             patch("sys.stdout", buf):
            from bexio.cli import main
            main()

        _, _, params = captured[0]
        self.assertEqual(params.get("limit"), 50)

    def test_empty_list_no_crash(self):
        out = capture_with_responses(["accounts", "list"], [[]])
        self.assertEqual(out, "")


# ─── accounts show ───────────────────────────────────────────────────────────

class TestAccountsShow(unittest.TestCase):
    def test_shows_id_and_name(self):
        out = capture_with_responses(["accounts", "show", "100"], [ACCOUNT])
        self.assertIn("100", out)
        self.assertIn("Kasse", out)

    def test_shows_account_no(self):
        out = capture_with_responses(["accounts", "show", "100"], [ACCOUNT])
        self.assertIn("1000", out)

    def test_json_output(self):
        out = capture_with_responses(["--json", "accounts", "show", "100"], [ACCOUNT])
        parsed = json.loads(out)
        self.assertEqual(parsed["id"], 100)


# ─── accounts search ─────────────────────────────────────────────────────────

class TestAccountsSearch(unittest.TestCase):
    def test_shows_matching_account(self):
        out = capture_with_responses(["accounts", "search", "Kasse"], [[ACCOUNT]])
        self.assertIn("Kasse", out)

    def test_posts_search_body(self):
        captured = []

        def fake_request(self, method, path, params=None, body=None, base=None):
            captured.append((method, path, body))
            return [ACCOUNT]

        buf = io.StringIO()
        with patch("bexio.client.BexioClient._request", fake_request), \
             patch("bexio.auth.get_token", return_value="FAKE"), \
             patch("sys.argv", ["bexio", "accounts", "search", "Kasse"]), \
             patch("sys.stdout", buf):
            from bexio.cli import main
            main()

        method, path, body = captured[0]
        self.assertEqual(method, "POST")
        self.assertIn("accounts/search", path)
        self.assertEqual(body[0]["value"], "Kasse")
        self.assertEqual(body[0]["field"], "name")
        self.assertEqual(body[0]["criteria"], "like")

    def test_empty_results_message(self):
        out = capture_with_responses(["accounts", "search", "nothing"], [[]])
        self.assertIn("No accounts", out)

    def test_json_output(self):
        out = capture_with_responses(["--json", "accounts", "search", "Kasse"], [[ACCOUNT]])
        parsed = json.loads(out)
        self.assertEqual(parsed[0]["id"], 100)


# ─── account-groups list ─────────────────────────────────────────────────────

class TestAccountGroupsList(unittest.TestCase):
    def test_shows_group_name(self):
        out = capture_with_responses(["account-groups", "list"], [[ACCOUNT_GROUP]])
        self.assertIn("Umlaufvermögen", out)

    def test_shows_account_no(self):
        out = capture_with_responses(["account-groups", "list"], [[ACCOUNT_GROUP]])
        self.assertIn("10", out)

    def test_json_output(self):
        out = capture_with_responses(["--json", "account-groups", "list"], [[ACCOUNT_GROUP]])
        parsed = json.loads(out)
        self.assertEqual(parsed[0]["id"], 10)

    def test_empty_list_no_crash(self):
        out = capture_with_responses(["account-groups", "list"], [[]])
        self.assertEqual(out, "")


# ─── vat-periods list ────────────────────────────────────────────────────────

class TestVatPeriodsList(unittest.TestCase):
    def test_shows_period_dates(self):
        out = capture_with_responses(["vat-periods", "list"], [[VAT_PERIOD]])
        self.assertIn("2024-01-01", out)
        self.assertIn("2024-12-31", out)

    def test_shows_status(self):
        out = capture_with_responses(["vat-periods", "list"], [[VAT_PERIOD]])
        self.assertIn("closed", out)

    def test_json_output(self):
        out = capture_with_responses(["--json", "vat-periods", "list"], [[VAT_PERIOD]])
        parsed = json.loads(out)
        self.assertEqual(parsed[0]["id"], 5)

    def test_empty_list_shows_no_periods(self):
        out = capture_with_responses(["vat-periods", "list"], [[]])
        self.assertIn("No VAT periods", out)


if __name__ == "__main__":
    unittest.main()

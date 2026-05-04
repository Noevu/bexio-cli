"""Tests for items/products commands."""

import io
import json
import unittest
from unittest.mock import patch

from tests.helpers import capture_with_responses

ITEM = {
    "id": 50,
    "intern_name": "Widget Pro",
    "intern_code": "WP-001",
    "purchase_price": "10.00",
    "sale_price": "25.00",
    "purchase_total": "10.00",
    "sale_total": "25.00",
    "remarks": "",
    "delivery_price": "0.00",
    "article_type_id": 1,
    "unit_id": 1,
    "is_stock": False,
    "contact_id": None,
    "tax_income_id": None,
    "tax_expense_id": None,
    "intern_description": None,
    "manufacturer_description": None,
    "manufacturer_name": None,
    "manufacturer_nr": None,
}


class TestItemsList(unittest.TestCase):
    def test_shows_item_name(self):
        out = capture_with_responses(["items", "list"], [[ITEM]])
        self.assertIn("Widget Pro", out)

    def test_shows_sale_price(self):
        out = capture_with_responses(["items", "list"], [[ITEM]])
        self.assertIn("25.00", out)

    def test_json_output(self):
        out = capture_with_responses(["--json", "items", "list"], [[ITEM]])
        parsed = json.loads(out)
        self.assertEqual(parsed[0]["id"], 50)

    def test_empty_list_no_crash(self):
        out = capture_with_responses(["items", "list"], [[]])
        self.assertEqual(out, "")


class TestItemsShow(unittest.TestCase):
    def test_shows_id_and_name(self):
        out = capture_with_responses(["items", "show", "50"], [ITEM])
        self.assertIn("50", out)
        self.assertIn("Widget Pro", out)

    def test_shows_sale_price(self):
        out = capture_with_responses(["items", "show", "50"], [ITEM])
        self.assertIn("25.00", out)

    def test_json_output(self):
        out = capture_with_responses(["--json", "items", "show", "50"], [ITEM])
        parsed = json.loads(out)
        self.assertEqual(parsed["id"], 50)


class TestItemsSearch(unittest.TestCase):
    def test_shows_matching_item(self):
        out = capture_with_responses(["items", "search", "Widget"], [[ITEM]])
        self.assertIn("Widget Pro", out)

    def test_posts_search_body(self):
        captured = []

        def fake_request(self, method, path, params=None, body=None, base=None, accept="application/json"):
            captured.append({"method": method, "path": path, "body": body})
            return [ITEM]

        with patch("bexio.client.BexioClient._request", fake_request), \
             patch("bexio.auth.get_token", return_value="FAKE"), \
             patch("sys.argv", ["bexio", "items", "search", "Widget"]), \
             patch("sys.stdout", io.StringIO()):
            from bexio.cli import main
            main()

        self.assertEqual(captured[0]["method"], "POST")
        self.assertIn("/article/search", captured[0]["path"])
        body = captured[0]["body"]
        self.assertIsInstance(body, list)
        self.assertEqual(body[0]["field"], "intern_name")
        self.assertIn("Widget", body[0]["value"])

    def test_empty_results(self):
        out = capture_with_responses(["items", "search", "nothing"], [[]])
        self.assertIn("No items", out)


class TestItemsCreate(unittest.TestCase):
    def test_prints_confirmation(self):
        response = {"id": 50, **ITEM}
        out = capture_with_responses(["items", "create", "--name", "Widget Pro"], [response])
        self.assertIn("created", out)

    def test_posts_correct_body(self):
        captured = []

        def fake_request(self, method, path, params=None, body=None, base=None, accept="application/json"):
            captured.append({"method": method, "path": path, "body": body})
            return {"id": 50, **ITEM}

        with patch("bexio.client.BexioClient._request", fake_request), \
             patch("bexio.auth.get_token", return_value="FAKE"), \
             patch("sys.argv", ["bexio", "items", "create", "--name", "Widget Pro",
                                "--sale-price", "25.00"]), \
             patch("sys.stdout", io.StringIO()):
            from bexio.cli import main
            main()

        self.assertEqual(len(captured), 1)
        self.assertEqual(captured[0]["method"], "POST")
        body = captured[0]["body"]
        self.assertEqual(body["intern_name"], "Widget Pro")
        self.assertEqual(body["sale_price"], "25.00")

    def test_missing_name_exits(self):
        buf = io.StringIO()
        with patch("sys.argv", ["bexio", "items", "create"]), \
             patch("bexio.auth.get_token", return_value="FAKE"), \
             patch("sys.stderr", buf):
            with self.assertRaises(SystemExit):
                import importlib
                import bexio.cli as cli_mod
                importlib.reload(cli_mod)
                cli_mod.main()


class TestItemsEdit(unittest.TestCase):
    def test_prints_confirmation(self):
        out = capture_with_responses(["items", "edit", "50", "--name", "Widget Pro Plus"], [ITEM])
        self.assertIn("updated", out)

    def test_puts_correct_endpoint(self):
        captured = []

        def fake_request(self, method, path, params=None, body=None, base=None, accept="application/json"):
            captured.append({"method": method, "path": path, "body": body})
            return ITEM

        with patch("bexio.client.BexioClient._request", fake_request), \
             patch("bexio.auth.get_token", return_value="FAKE"), \
             patch("sys.argv", ["bexio", "items", "edit", "50", "--name", "Updated Name"]), \
             patch("sys.stdout", io.StringIO()):
            from bexio.cli import main
            main()

        self.assertEqual(captured[0]["method"], "PUT")
        self.assertIn("/article/50", captured[0]["path"])

    def test_sends_only_provided_fields(self):
        captured = []

        def fake_request(self, method, path, params=None, body=None, base=None, accept="application/json"):
            captured.append({"body": body})
            return ITEM

        with patch("bexio.client.BexioClient._request", fake_request), \
             patch("bexio.auth.get_token", return_value="FAKE"), \
             patch("sys.argv", ["bexio", "items", "edit", "50", "--sale-price", "30.00"]), \
             patch("sys.stdout", io.StringIO()):
            from bexio.cli import main
            main()

        body = captured[0]["body"]
        self.assertIn("sale_price", body)
        self.assertNotIn("intern_name", body)


class TestItemsDelete(unittest.TestCase):
    def test_prints_confirmation(self):
        out = capture_with_responses(["items", "delete", "50"], [{}])
        self.assertIn("50", out)
        self.assertIn("deleted", out)

    def test_deletes_correct_endpoint(self):
        captured = []

        def fake_request(self, method, path, params=None, body=None, base=None, accept="application/json"):
            captured.append({"method": method, "path": path})
            return {}

        with patch("bexio.client.BexioClient._request", fake_request), \
             patch("bexio.auth.get_token", return_value="FAKE"), \
             patch("sys.argv", ["bexio", "items", "delete", "50"]), \
             patch("sys.stdout", io.StringIO()):
            from bexio.cli import main
            main()

        self.assertEqual(captured[0]["method"], "DELETE")
        self.assertIn("/article/50", captured[0]["path"])

"""Tests for quote commands."""

import io
import json
import unittest
from unittest.mock import patch

from tests.helpers import capture_with_responses

QUOTE = {
    "id": 10,
    "document_nr": "AN-00010",
    "title": "Website Redesign",
    "is_valid_from": "2026-04-01",
    "total": "9500.000000",
    "kb_item_status_id": 3,
}


class TestQuotesList(unittest.TestCase):
    def test_shows_key_fields(self):
        out = capture_with_responses(["quotes", "list"], [[QUOTE]])
        self.assertIn("AN-00010", out)
        self.assertIn("Sent", out)
        self.assertIn("9500.00", out)

    def test_status_filter(self):
        captured = []

        def fake_request(self, method, path, params=None, body=None):
            captured.append(params or {})
            return []

        with patch("bexio.client.BexioClient._request", fake_request), \
             patch("bexio.auth.get_token", return_value="FAKE"), \
             patch("sys.argv", ["bexio", "quotes", "list", "--status", "accepted"]), \
             patch("sys.stdout", io.StringIO()):
            from bexio.cli import main
            main()

        self.assertEqual(captured[0].get("kb_item_status_id"), 8)

    def test_json_output(self):
        out = capture_with_responses(["--json", "quotes", "list"], [[QUOTE]])
        parsed = json.loads(out)
        self.assertEqual(parsed[0]["id"], 10)


class TestQuotesShow(unittest.TestCase):
    def test_shows_all_fields(self):
        out = capture_with_responses(["quotes", "show", "10"], [QUOTE])
        self.assertIn("AN-00010", out)
        self.assertIn("Sent", out)
        self.assertIn("9500.00", out)
        self.assertIn("office.bexio.com", out)


class TestQuoteActions(unittest.TestCase):
    def _test_action(self, subcommand, expected_path_fragment):
        captured = []

        def fake_request(self, method, path, params=None, body=None):
            captured.append((method, path))
            return {}

        with patch("bexio.client.BexioClient._request", fake_request), \
             patch("bexio.auth.get_token", return_value="FAKE"), \
             patch("sys.argv", ["bexio", "quotes", subcommand, "10"]), \
             patch("sys.stdout", io.StringIO()):
            from bexio.cli import main
            main()

        paths = [p for _, p in captured]
        self.assertTrue(any(expected_path_fragment in p for p in paths),
                        f"Expected '{expected_path_fragment}' in {paths}")

    def test_send(self):
        self._test_action("send", "/send")

    def test_accept(self):
        self._test_action("accept", "/accept")

    def test_decline(self):
        self._test_action("decline", "/decline")

    def test_create_order(self):
        self._test_action("create-order", "/order")

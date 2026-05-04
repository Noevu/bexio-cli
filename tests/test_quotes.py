"""Tests for quote commands."""

import io
import json
import os
import tempfile
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


class TestQuotesSearch(unittest.TestCase):
    def test_shows_matching_quote(self):
        out = capture_with_responses(["quotes", "search", "Website"], [[QUOTE]])
        self.assertIn("AN-00010", out)

    def test_posts_search_body(self):
        captured = []

        def fake_request(self, method, path, params=None, body=None, base=None, accept="application/json"):
            captured.append((method, path, body))
            return [QUOTE]

        with patch("bexio.client.BexioClient._request", fake_request), \
             patch("bexio.auth.get_token", return_value="FAKE"), \
             patch("sys.argv", ["bexio", "quotes", "search", "Website"]), \
             patch("sys.stdout", io.StringIO()):
            from bexio.cli import main
            main()

        method, path, body = captured[0]
        self.assertEqual(method, "POST")
        self.assertIn("kb_offer/search", path)
        self.assertEqual(body[0]["field"], "title")
        self.assertEqual(body[0]["value"], "Website")
        self.assertEqual(body[0]["criteria"], "like")

    def test_empty_results(self):
        out = capture_with_responses(["quotes", "search", "zzz"], [[]])
        self.assertIn("No quotes", out)


class TestQuotesDelete(unittest.TestCase):
    def test_prints_confirmation(self):
        out = capture_with_responses(["quotes", "delete", "10"], [{"success": True}])
        self.assertIn("deleted", out)
        self.assertIn("10", out)

    def test_deletes_correct_endpoint(self):
        captured = []

        def fake_request(self, method, path, params=None, body=None, base=None, accept="application/json"):
            captured.append((method, path))
            return {"success": True}

        with patch("bexio.client.BexioClient._request", fake_request), \
             patch("bexio.auth.get_token", return_value="FAKE"), \
             patch("sys.argv", ["bexio", "quotes", "delete", "10"]), \
             patch("sys.stdout", io.StringIO()):
            from bexio.cli import main
            main()

        self.assertIn(("DELETE", "/kb_offer/10"), captured)


class TestQuotesCopy(unittest.TestCase):
    def test_prints_new_id(self):
        out = capture_with_responses(["quotes", "copy", "10"], [{"id": 11, "document_nr": "AN-00011"}])
        self.assertIn("11", out)

    def test_posts_copy_endpoint(self):
        captured = []

        def fake_request(self, method, path, params=None, body=None, base=None, accept="application/json"):
            captured.append((method, path))
            return {"id": 11}

        with patch("bexio.client.BexioClient._request", fake_request), \
             patch("bexio.auth.get_token", return_value="FAKE"), \
             patch("sys.argv", ["bexio", "quotes", "copy", "10"]), \
             patch("sys.stdout", io.StringIO()):
            from bexio.cli import main
            main()

        self.assertIn(("POST", "/kb_offer/10/copy"), captured)


class TestQuotesPdf(unittest.TestCase):
    def test_saves_file(self):
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            tmp = f.name
        os.unlink(tmp)

        def fake_request(self, method, path, params=None, body=None, base=None, accept="application/json"):
            return b"FAKEPDF"

        with patch("bexio.client.BexioClient._request", fake_request), \
             patch("bexio.auth.get_token", return_value="FAKE"), \
             patch("sys.argv", ["bexio", "quotes", "pdf", "10", "--output", tmp]), \
             patch("sys.stdout", io.StringIO()):
            from bexio.cli import main
            main()

        self.assertTrue(os.path.exists(tmp))
        with open(tmp, "rb") as f:
            self.assertEqual(f.read(), b"FAKEPDF")
        os.unlink(tmp)

    def test_default_filename(self):
        default_file = "quote_10.pdf"
        if os.path.exists(default_file):
            os.unlink(default_file)

        def fake_request(self, method, path, params=None, body=None, base=None, accept="application/json"):
            return b"FAKEPDF"

        with patch("bexio.client.BexioClient._request", fake_request), \
             patch("bexio.auth.get_token", return_value="FAKE"), \
             patch("sys.argv", ["bexio", "quotes", "pdf", "10"]), \
             patch("sys.stdout", io.StringIO()):
            from bexio.cli import main
            main()

        self.assertTrue(os.path.exists(default_file))
        os.unlink(default_file)


class TestQuotesIssue(unittest.TestCase):
    def test_prints_confirmation(self):
        out = capture_with_responses(["quotes", "issue", "10"], [{"success": True}])
        self.assertIn("10", out)
        self.assertIn("issued", out)

    def test_posts_correct_endpoint(self):
        captured = []

        def fake_request(self, method, path, params=None, body=None, base=None, accept="application/json"):
            captured.append((method, path))
            return {"success": True}

        with patch("bexio.client.BexioClient._request", fake_request), \
             patch("bexio.auth.get_token", return_value="FAKE"), \
             patch("sys.argv", ["bexio", "quotes", "issue", "10"]), \
             patch("sys.stdout", io.StringIO()):
            from bexio.cli import main
            main()

        self.assertIn(("POST", "/kb_offer/10/issue"), captured)


class TestQuotesRevert(unittest.TestCase):
    def test_prints_confirmation(self):
        out = capture_with_responses(["quotes", "revert", "10"], [{"success": True}])
        self.assertIn("10", out)
        self.assertIn("draft", out)

    def test_posts_correct_endpoint(self):
        captured = []

        def fake_request(self, method, path, params=None, body=None, base=None, accept="application/json"):
            captured.append((method, path))
            return {"success": True}

        with patch("bexio.client.BexioClient._request", fake_request), \
             patch("bexio.auth.get_token", return_value="FAKE"), \
             patch("sys.argv", ["bexio", "quotes", "revert", "10"]), \
             patch("sys.stdout", io.StringIO()):
            from bexio.cli import main
            main()

        self.assertIn(("POST", "/kb_offer/10/revert"), captured)


class TestQuotesReissue(unittest.TestCase):
    def test_prints_confirmation(self):
        out = capture_with_responses(["quotes", "reissue", "10"], [{"success": True}])
        self.assertIn("10", out)
        self.assertIn("reissued", out)

    def test_posts_correct_endpoint(self):
        captured = []

        def fake_request(self, method, path, params=None, body=None, base=None, accept="application/json"):
            captured.append((method, path))
            return {"success": True}

        with patch("bexio.client.BexioClient._request", fake_request), \
             patch("bexio.auth.get_token", return_value="FAKE"), \
             patch("sys.argv", ["bexio", "quotes", "reissue", "10"]), \
             patch("sys.stdout", io.StringIO()):
            from bexio.cli import main
            main()

        self.assertIn(("POST", "/kb_offer/10/reissue"), captured)


class TestQuotesMarkSent(unittest.TestCase):
    def test_prints_confirmation(self):
        out = capture_with_responses(["quotes", "mark-sent", "10"], [{"success": True}])
        self.assertIn("10", out)
        self.assertIn("sent", out)

    def test_posts_correct_endpoint(self):
        captured = []

        def fake_request(self, method, path, params=None, body=None, base=None, accept="application/json"):
            captured.append((method, path))
            return {"success": True}

        with patch("bexio.client.BexioClient._request", fake_request), \
             patch("bexio.auth.get_token", return_value="FAKE"), \
             patch("sys.argv", ["bexio", "quotes", "mark-sent", "10"]), \
             patch("sys.stdout", io.StringIO()):
            from bexio.cli import main
            main()

        self.assertIn(("POST", "/kb_offer/10/mark_as_sent"), captured)


class TestQuotesCreateInvoice(unittest.TestCase):
    def test_prints_confirmation(self):
        out = capture_with_responses(["quotes", "create-invoice", "10"], [{"id": 200}])
        self.assertIn("200", out)

    def test_posts_correct_endpoint(self):
        captured = []

        def fake_request(self, method, path, params=None, body=None, base=None, accept="application/json"):
            captured.append((method, path))
            return {"id": 200}

        with patch("bexio.client.BexioClient._request", fake_request), \
             patch("bexio.auth.get_token", return_value="FAKE"), \
             patch("sys.argv", ["bexio", "quotes", "create-invoice", "10"]), \
             patch("sys.stdout", io.StringIO()):
            from bexio.cli import main
            main()

        self.assertIn(("POST", "/kb_offer/10/invoice"), captured)

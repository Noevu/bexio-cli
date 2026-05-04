"""Tests for countries commands."""

import io
import json
import unittest
from unittest.mock import patch

from tests.helpers import capture_with_responses

COUNTRY = {
    "id": 1,
    "name": "Schweiz",
    "name_short": "CH",
    "iso3166_alpha2": "CH",
}

COUNTRY_DE = {
    "id": 2,
    "name": "Deutschland",
    "name_short": "DE",
    "iso3166_alpha2": "DE",
}


class TestCountriesList(unittest.TestCase):
    def test_shows_iso_and_name(self):
        out = capture_with_responses(["countries", "list"], [[COUNTRY]])
        self.assertIn("CH", out)
        self.assertIn("Schweiz", out)

    def test_shows_multiple_rows(self):
        out = capture_with_responses(["countries", "list"], [[COUNTRY, COUNTRY_DE]])
        self.assertIn("Schweiz", out)
        self.assertIn("Deutschland", out)
        self.assertIn("DE", out)

    def test_json_flag(self):
        out = capture_with_responses(["--json", "countries", "list"], [[COUNTRY]])
        parsed = json.loads(out)
        self.assertEqual(parsed[0]["id"], 1)

    def test_empty_list_no_crash(self):
        out = capture_with_responses(["countries", "list"], [[]])
        # Should not raise — empty string or whitespace is fine
        self.assertIsInstance(out, str)

    def test_limit_param(self):
        captured = []

        def fake_request(self, method, path, params=None, body=None):
            captured.append((method, path, params))
            return [COUNTRY]

        with patch("bexio.client.BexioClient._request", fake_request), \
             patch("bexio.auth.get_token", return_value="FAKE"), \
             patch("sys.argv", ["bexio", "countries", "list", "--limit", "5"]), \
             patch("sys.stdout", io.StringIO()):
            from bexio.cli import main
            main()

        self.assertEqual(captured[0][2]["limit"], 5)


class TestCountriesShow(unittest.TestCase):
    def test_shows_id(self):
        out = capture_with_responses(["countries", "show", "1"], [COUNTRY])
        self.assertIn("1", out)

    def test_shows_name(self):
        out = capture_with_responses(["countries", "show", "1"], [COUNTRY])
        self.assertIn("Schweiz", out)

    def test_shows_iso(self):
        out = capture_with_responses(["countries", "show", "1"], [COUNTRY])
        self.assertIn("CH", out)

    def test_json_flag(self):
        out = capture_with_responses(["--json", "countries", "show", "1"], [COUNTRY])
        parsed = json.loads(out)
        self.assertEqual(parsed["id"], 1)
        self.assertEqual(parsed["name"], "Schweiz")


class TestCountriesSearch(unittest.TestCase):
    def test_posts_correct_body(self):
        captured = []

        def fake_request(self, method, path, params=None, body=None):
            captured.append((method, path, body))
            return [COUNTRY]

        with patch("bexio.client.BexioClient._request", fake_request), \
             patch("bexio.auth.get_token", return_value="FAKE"), \
             patch("sys.argv", ["bexio", "countries", "search", "Schweiz"]), \
             patch("sys.stdout", io.StringIO()):
            from bexio.cli import main
            main()

        method, path, body = captured[0]
        self.assertEqual(method, "POST")
        self.assertIn("country/search", path)
        self.assertEqual(body[0]["field"], "name")
        self.assertEqual(body[0]["value"], "Schweiz")
        self.assertEqual(body[0]["criteria"], "like")

    def test_shows_results(self):
        out = capture_with_responses(["countries", "search", "Schweiz"], [[COUNTRY]])
        self.assertIn("Schweiz", out)
        self.assertIn("CH", out)

    def test_no_results_message(self):
        out = capture_with_responses(["countries", "search", "Nowhere"], [[]])
        self.assertIn("No countries", out)

    def test_json_flag(self):
        out = capture_with_responses(["--json", "countries", "search", "CH"], [[COUNTRY]])
        parsed = json.loads(out)
        self.assertEqual(parsed[0]["id"], 1)


if __name__ == "__main__":
    unittest.main()

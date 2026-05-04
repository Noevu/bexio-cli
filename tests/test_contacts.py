"""Tests for contact commands."""

import io
import json
import unittest
from unittest.mock import patch

from tests.helpers import capture_with_responses

CONTACT = {
    "id": 246,
    "name": "Ausgleichskasse der AIHK",
    "firstname": None,
    "lastname": None,
    "mail": "info@aihk.ch",
    "phone_fixed": "+41 62 837 97 00",
}

PERSON = {
    "id": 245,
    "name": None,
    "firstname": "Anna",
    "lastname": "Imperia",
    "mail": "anna@aihk.ch",
    "phone_fixed": "",
}


class TestContactsList(unittest.TestCase):
    def test_shows_org_name(self):
        out = capture_with_responses(["contacts", "list"], [[CONTACT]])
        self.assertIn("Ausgleichskasse der AIHK", out)
        self.assertIn("info@aihk.ch", out)

    def test_shows_person_name_from_parts(self):
        out = capture_with_responses(["contacts", "list"], [[PERSON]])
        self.assertIn("Anna Imperia", out)

    def test_json_output(self):
        out = capture_with_responses(["--json", "contacts", "list"], [[CONTACT]])
        parsed = json.loads(out)
        self.assertEqual(parsed[0]["id"], 246)


class TestContactsShow(unittest.TestCase):
    def test_shows_all_fields(self):
        out = capture_with_responses(["contacts", "show", "246"], [CONTACT])
        self.assertIn("246", out)
        self.assertIn("Ausgleichskasse der AIHK", out)
        self.assertIn("info@aihk.ch", out)
        self.assertIn("office.bexio.com", out)

    def test_person_name_from_parts(self):
        out = capture_with_responses(["contacts", "show", "245"], [PERSON])
        self.assertIn("Anna Imperia", out)


class TestContactsSearch(unittest.TestCase):
    def test_posts_search_body(self):
        captured = []

        def fake_request(self, method, path, params=None, body=None):
            captured.append((method, path, body))
            return [CONTACT]

        with patch("bexio.client.BexioClient._request", fake_request), \
             patch("bexio.auth.get_token", return_value="FAKE"), \
             patch("sys.argv", ["bexio", "contacts", "search", "AIHK"]), \
             patch("sys.stdout", io.StringIO()):
            from bexio.cli import main
            main()

        method, path, body = captured[0]
        self.assertEqual(method, "POST")
        self.assertIn("contact/search", path)
        self.assertEqual(body[0]["value"], "AIHK")

    def test_empty_results_message(self):
        out = capture_with_responses(["contacts", "search", "nobody"], [[]])
        self.assertIn("No contacts", out)

    def test_json_output(self):
        out = capture_with_responses(["--json", "contacts", "search", "AIHK"], [[CONTACT]])
        parsed = json.loads(out)
        self.assertEqual(parsed[0]["id"], 246)

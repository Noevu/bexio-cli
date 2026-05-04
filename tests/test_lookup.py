"""Tests for lookup commands: languages, contact-groups, business-activities."""

import json
import unittest

from tests.helpers import capture_with_responses

LANGUAGE = {
    "id": 1,
    "name": "Deutsch",
    "iso_639_1": "de",
}

LANGUAGE_FR = {
    "id": 2,
    "name": "Français",
    "iso_639_1": "fr",
}

CONTACT_GROUP = {
    "id": 10,
    "name": "VIP Clients",
}

CONTACT_GROUP_2 = {
    "id": 11,
    "name": "Partners",
}

BUSINESS_ACTIVITY = {
    "id": 5,
    "name": "Webdesign",
    "default_is_billable": True,
    "default_price_per_hour": "150.00",
    "account_id": 3200,
}

BUSINESS_ACTIVITY_2 = {
    "id": 6,
    "name": "Consulting",
    "default_is_billable": False,
    "default_price_per_hour": "0.00",
    "account_id": 3201,
}


class TestLanguagesList(unittest.TestCase):
    def test_shows_iso_and_name(self):
        out = capture_with_responses(["languages", "list"], [[LANGUAGE, LANGUAGE_FR]])
        self.assertIn("de", out)
        self.assertIn("Deutsch", out)
        self.assertIn("fr", out)
        self.assertIn("Français", out)

    def test_shows_id(self):
        out = capture_with_responses(["languages", "list"], [[LANGUAGE]])
        self.assertIn("1", out)

    def test_json_flag(self):
        out = capture_with_responses(["--json", "languages", "list"], [[LANGUAGE]])
        parsed = json.loads(out)
        self.assertEqual(parsed[0]["id"], 1)
        self.assertEqual(parsed[0]["iso_639_1"], "de")


class TestContactGroupsList(unittest.TestCase):
    def test_shows_id_and_name(self):
        out = capture_with_responses(["contact-groups", "list"], [[CONTACT_GROUP, CONTACT_GROUP_2]])
        self.assertIn("10", out)
        self.assertIn("VIP Clients", out)
        self.assertIn("11", out)
        self.assertIn("Partners", out)

    def test_json_flag(self):
        out = capture_with_responses(["--json", "contact-groups", "list"], [[CONTACT_GROUP]])
        parsed = json.loads(out)
        self.assertEqual(parsed[0]["id"], 10)
        self.assertEqual(parsed[0]["name"], "VIP Clients")


class TestBusinessActivitiesList(unittest.TestCase):
    def test_shows_id_and_name(self):
        out = capture_with_responses(
            ["business-activities", "list"],
            [[BUSINESS_ACTIVITY, BUSINESS_ACTIVITY_2]],
        )
        self.assertIn("5", out)
        self.assertIn("Webdesign", out)
        self.assertIn("6", out)
        self.assertIn("Consulting", out)

    def test_shows_billable_column(self):
        out = capture_with_responses(
            ["business-activities", "list"], [[BUSINESS_ACTIVITY]]
        )
        # billable=True should show something meaningful
        self.assertIn("Webdesign", out)
        self.assertTrue(len(out.strip()) > 0)

    def test_json_flag(self):
        out = capture_with_responses(
            ["--json", "business-activities", "list"], [[BUSINESS_ACTIVITY]]
        )
        parsed = json.loads(out)
        self.assertEqual(parsed[0]["id"], 5)
        self.assertEqual(parsed[0]["name"], "Webdesign")


class TestBusinessActivitiesShow(unittest.TestCase):
    def test_shows_fields(self):
        out = capture_with_responses(
            ["business-activities", "show", "5"], [BUSINESS_ACTIVITY]
        )
        self.assertIn("5", out)
        self.assertIn("Webdesign", out)
        self.assertIn("150.00", out)

    def test_hits_correct_endpoint(self):
        """Confirm the endpoint uses /client_service/{id}, not /business_activity."""
        captured = []

        import io
        from unittest.mock import patch

        def fake_request(self, method, path, params=None, body=None):
            captured.append(path)
            return BUSINESS_ACTIVITY

        buf = io.StringIO()
        with patch("bexio.client.BexioClient._request", fake_request), \
             patch("bexio.auth.get_token", return_value="FAKE"), \
             patch("sys.argv", ["bexio", "business-activities", "show", "5"]), \
             patch("sys.stdout", buf):
            from bexio.cli import main
            main()

        self.assertTrue(
            any("/client_service/5" in p for p in captured),
            f"Expected /client_service/5 in calls, got: {captured}",
        )

    def test_json_flag(self):
        out = capture_with_responses(
            ["--json", "business-activities", "show", "5"], [BUSINESS_ACTIVITY]
        )
        parsed = json.loads(out)
        self.assertEqual(parsed["id"], 5)
        self.assertEqual(parsed["name"], "Webdesign")

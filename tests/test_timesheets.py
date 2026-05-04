"""Tests for timesheet commands."""

import io
import json
import unittest
from unittest.mock import patch

from tests.helpers import capture_with_responses

TIMESHEET = {
    "id": 77,
    "user_id": 1,
    "status_id": 1,
    "client_service_id": None,
    "text": "Working on homepage",
    "allowable_bill": True,
    "charge": True,
    "pr_project_id": 20,
    "pr_milestone_id": None,
    "pr_package_id": None,
    "contact_id": None,
    "sub_contact_id": None,
    "tracking": {
        "type": "duration",
        "date": "2024-03-15",
        "duration": "03:30",
    },
}

TIMESHEET_STATUS = {"id": 1, "name": "In Progress"}


class TestTimesheetsList(unittest.TestCase):
    def test_shows_timesheet_text(self):
        out = capture_with_responses(["timesheets", "list"], [[TIMESHEET]])
        self.assertIn("Working on homepage", out)

    def test_shows_date(self):
        out = capture_with_responses(["timesheets", "list"], [[TIMESHEET]])
        self.assertIn("2024-03-15", out)

    def test_shows_duration(self):
        out = capture_with_responses(["timesheets", "list"], [[TIMESHEET]])
        self.assertIn("03:30", out)

    def test_json_output(self):
        out = capture_with_responses(["--json", "timesheets", "list"], [[TIMESHEET]])
        parsed = json.loads(out)
        self.assertEqual(parsed[0]["id"], 77)

    def test_empty_list_shows_no_timesheets(self):
        out = capture_with_responses(["timesheets", "list"], [[]])
        self.assertIn("No timesheets found", out)

    def test_limit_passed_as_param(self):
        captured = []

        def fake_request(self, method, path, params=None, body=None, base=None, accept="application/json"):
            captured.append((method, path, params))
            return [TIMESHEET]

        with patch("bexio.client.BexioClient._request", fake_request), \
             patch("bexio.auth.get_token", return_value="FAKE"), \
             patch("sys.argv", ["bexio", "timesheets", "list", "--limit", "5"]), \
             patch("sys.stdout", io.StringIO()):
            from bexio.cli import main
            main()

        _, _, params = captured[0]
        self.assertEqual(params.get("limit"), 5)


class TestTimesheetsShow(unittest.TestCase):
    def test_shows_id(self):
        out = capture_with_responses(["timesheets", "show", "77"], [TIMESHEET])
        self.assertIn("77", out)

    def test_shows_text(self):
        out = capture_with_responses(["timesheets", "show", "77"], [TIMESHEET])
        self.assertIn("Working on homepage", out)

    def test_json_output(self):
        out = capture_with_responses(["--json", "timesheets", "show", "77"], [TIMESHEET])
        parsed = json.loads(out)
        self.assertEqual(parsed["id"], 77)


class TestTimesheetsSearch(unittest.TestCase):
    def test_shows_matching_timesheet(self):
        out = capture_with_responses(["timesheets", "search", "homepage"], [[TIMESHEET]])
        self.assertIn("Working on homepage", out)

    def test_posts_search_body(self):
        captured = []

        def fake_request(self, method, path, params=None, body=None, base=None, accept="application/json"):
            captured.append((method, path, body))
            return [TIMESHEET]

        with patch("bexio.client.BexioClient._request", fake_request), \
             patch("bexio.auth.get_token", return_value="FAKE"), \
             patch("sys.argv", ["bexio", "timesheets", "search", "homepage"]), \
             patch("sys.stdout", io.StringIO()):
            from bexio.cli import main
            main()

        method, path, body = captured[0]
        self.assertEqual(method, "POST")
        self.assertIn("timesheet/search", path)
        self.assertEqual(body[0]["field"], "text")
        self.assertEqual(body[0]["value"], "homepage")
        self.assertEqual(body[0]["criteria"], "like")

    def test_empty_results(self):
        out = capture_with_responses(["timesheets", "search", "nothing"], [[]])
        self.assertIn("No timesheets found", out)


class TestTimesheetsCreate(unittest.TestCase):
    def _capture_create(self, extra_args, response=None):
        captured = []
        resp = response or {"id": 99, **TIMESHEET}

        def fake_request(self, method, path, params=None, body=None, base=None, accept="application/json"):
            captured.append((method, path, body))
            return resp

        buf = io.StringIO()
        with patch("bexio.client.BexioClient._request", fake_request), \
             patch("bexio.auth.get_token", return_value="FAKE"), \
             patch("sys.argv", ["bexio", "timesheets", "create"] + extra_args), \
             patch("sys.stdout", buf):
            from bexio.cli import main
            main()
        return buf.getvalue(), captured

    def test_prints_confirmation(self):
        out, _ = self._capture_create(["--date", "2024-03-15", "--duration", "03:30"])
        self.assertIn("created", out)

    def test_posts_correct_body(self):
        _, captured = self._capture_create(
            ["--date", "2024-03-15", "--duration", "03:30", "--text", "My work"]
        )
        method, path, body = captured[0]
        self.assertEqual(method, "POST")
        self.assertIn("timesheet", path)
        tracking = body.get("tracking", {})
        self.assertEqual(tracking.get("type"), "duration")
        self.assertEqual(tracking.get("date"), "2024-03-15")
        self.assertEqual(tracking.get("duration"), "03:30")
        self.assertEqual(body.get("text"), "My work")

    def test_missing_date_exits(self):
        with self.assertRaises(SystemExit):
            with patch("bexio.auth.get_token", return_value="FAKE"), \
                 patch("sys.argv", ["bexio", "timesheets", "create", "--duration", "03:30"]):
                from bexio.cli import main
                main()

    def test_missing_duration_exits(self):
        with self.assertRaises(SystemExit):
            with patch("bexio.auth.get_token", return_value="FAKE"), \
                 patch("sys.argv", ["bexio", "timesheets", "create", "--date", "2024-03-15"]):
                from bexio.cli import main
                main()

    def test_optional_fields_included_when_provided(self):
        _, captured = self._capture_create(
            ["--date", "2024-03-15", "--duration", "02:00",
             "--user-id", "3", "--project-id", "42", "--text", "Extra work"]
        )
        body = captured[0][2]
        self.assertEqual(body.get("user_id"), 3)
        self.assertEqual(body.get("pr_project_id"), 42)


class TestTimesheetsEdit(unittest.TestCase):
    def _capture_edit(self, extra_args, response=None):
        captured = []
        resp = response or TIMESHEET

        def fake_request(self, method, path, params=None, body=None, base=None, accept="application/json"):
            captured.append((method, path, body))
            return resp

        buf = io.StringIO()
        with patch("bexio.client.BexioClient._request", fake_request), \
             patch("bexio.auth.get_token", return_value="FAKE"), \
             patch("sys.argv", ["bexio", "timesheets", "edit"] + extra_args), \
             patch("sys.stdout", buf):
            from bexio.cli import main
            main()
        return buf.getvalue(), captured

    def test_prints_confirmation(self):
        out, _ = self._capture_edit(["77", "--text", "Updated text"])
        self.assertIn("updated", out)

    def test_puts_correct_endpoint(self):
        _, captured = self._capture_edit(["77", "--text", "Updated text"])
        method, path, body = captured[0]
        self.assertEqual(method, "PUT")
        self.assertIn("timesheet/77", path)

    def test_only_sends_provided_fields(self):
        _, captured = self._capture_edit(["77", "--duration", "04:00"])
        body = captured[0][2]
        tracking = body.get("tracking", {})
        self.assertEqual(tracking.get("duration"), "04:00")
        # date and text not provided — should not appear in body
        self.assertNotIn("text", body)


class TestTimesheetsDelete(unittest.TestCase):
    def test_prints_confirmation(self):
        out = capture_with_responses(["timesheets", "delete", "77"], [True])
        self.assertIn("deleted", out)
        self.assertIn("77", out)

    def test_deletes_correct_endpoint(self):
        captured = []

        def fake_request(self, method, path, params=None, body=None, base=None, accept="application/json"):
            captured.append((method, path))
            return True

        with patch("bexio.client.BexioClient._request", fake_request), \
             patch("bexio.auth.get_token", return_value="FAKE"), \
             patch("sys.argv", ["bexio", "timesheets", "delete", "77"]), \
             patch("sys.stdout", io.StringIO()):
            from bexio.cli import main
            main()

        method, path = captured[0]
        self.assertEqual(method, "DELETE")
        self.assertIn("timesheet/77", path)


class TestTimesheetsStatuses(unittest.TestCase):
    def test_shows_status_name(self):
        out = capture_with_responses(["timesheets", "statuses"], [[TIMESHEET_STATUS]])
        self.assertIn("In Progress", out)

    def test_shows_status_id(self):
        out = capture_with_responses(["timesheets", "statuses"], [[TIMESHEET_STATUS]])
        self.assertIn("1", out)

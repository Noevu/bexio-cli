"""Tests for project, milestone, and work-package commands."""

import io
import json
import unittest
from unittest.mock import patch

from tests.helpers import capture_with_responses

PROJECT = {
    "id": 20,
    "name": "Website Redesign",
    "start_date": "2024-01-01",
    "end_date": "2024-12-31",
    "comment": "Annual redesign project",
    "pr_state_id": 1,
    "pr_project_type_id": 1,
    "contact_id": 5,
    "contact_sub_contact_id": None,
    "user_id": 1,
    "pr_invoice_type_id": 1,
    "pr_invoice_type_amount": None,
}

PROJECT_TYPE = {"id": 1, "name": "Standard"}
PROJECT_STATUS = {"id": 1, "name": "In Progress"}

MILESTONE = {
    "id": 100,
    "name": "Phase 1 Launch",
    "project_id": 20,
    "user_id": 1,
    "finish_date": "2024-06-30",
}

WORK_PACKAGE = {
    "id": 200,
    "name": "Frontend Development",
    "project_id": 20,
    "user_id": 1,
    "estimated_hours": "40.00",
    "comment": None,
}


# ---------------------------------------------------------------------------
# Projects
# ---------------------------------------------------------------------------

class TestProjectsList(unittest.TestCase):
    def test_shows_project_name(self):
        out = capture_with_responses(["projects", "list"], [[PROJECT]])
        self.assertIn("Website Redesign", out)

    def test_json_output(self):
        out = capture_with_responses(["--json", "projects", "list"], [[PROJECT]])
        parsed = json.loads(out)
        self.assertEqual(parsed[0]["id"], 20)

    def test_empty_list_shows_no_projects(self):
        out = capture_with_responses(["projects", "list"], [[]])
        self.assertIn("No projects", out)


class TestProjectsShow(unittest.TestCase):
    def test_shows_id_and_name(self):
        out = capture_with_responses(["projects", "show", "20"], [PROJECT])
        self.assertIn("20", out)
        self.assertIn("Website Redesign", out)

    def test_json_output(self):
        out = capture_with_responses(["--json", "projects", "show", "20"], [PROJECT])
        parsed = json.loads(out)
        self.assertEqual(parsed["id"], 20)
        self.assertEqual(parsed["name"], "Website Redesign")


class TestProjectsSearch(unittest.TestCase):
    def test_shows_matching_project(self):
        out = capture_with_responses(["projects", "search", "Website"], [[PROJECT]])
        self.assertIn("Website Redesign", out)

    def test_posts_search_body(self):
        captured = []

        def fake_request(self, method, path, params=None, body=None, base=None, accept="application/json"):
            captured.append((method, path, body))
            return [PROJECT]

        with patch("bexio.client.BexioClient._request", fake_request), \
             patch("bexio.auth.get_token", return_value="FAKE"), \
             patch("sys.argv", ["bexio", "projects", "search", "Website"]), \
             patch("sys.stdout", io.StringIO()):
            from bexio.cli import main
            main()

        method, path, body = captured[0]
        self.assertEqual(method, "POST")
        self.assertIn("pr_project/search", path)
        self.assertEqual(body[0]["field"], "name")
        self.assertEqual(body[0]["value"], "Website")
        self.assertEqual(body[0]["criteria"], "like")

    def test_empty_results(self):
        out = capture_with_responses(["projects", "search", "zzz"], [[]])
        self.assertIn("No projects", out)


class TestProjectsCreate(unittest.TestCase):
    def test_prints_confirmation(self):
        out = capture_with_responses(["projects", "create", "--name", "New Project"], [PROJECT])
        self.assertIn("created", out)
        self.assertIn("20", out)

    def test_posts_correct_body(self):
        captured = []

        def fake_request(self, method, path, params=None, body=None, base=None, accept="application/json"):
            captured.append((method, path, body))
            return PROJECT

        with patch("bexio.client.BexioClient._request", fake_request), \
             patch("bexio.auth.get_token", return_value="FAKE"), \
             patch("sys.argv", ["bexio", "projects", "create", "--name", "New Project", "--contact-id", "5"]), \
             patch("sys.stdout", io.StringIO()):
            from bexio.cli import main
            main()

        method, path, body = captured[0]
        self.assertEqual(method, "POST")
        self.assertIn("pr_project", path)
        self.assertEqual(body["name"], "New Project")
        self.assertEqual(body["contact_id"], 5)


class TestProjectsEdit(unittest.TestCase):
    def test_prints_confirmation(self):
        out = capture_with_responses(["projects", "edit", "20", "--name", "Updated"], [PROJECT])
        self.assertIn("updated", out)
        self.assertIn("20", out)

    def test_puts_correct_endpoint(self):
        captured = []

        def fake_request(self, method, path, params=None, body=None, base=None, accept="application/json"):
            captured.append((method, path))
            return PROJECT

        with patch("bexio.client.BexioClient._request", fake_request), \
             patch("bexio.auth.get_token", return_value="FAKE"), \
             patch("sys.argv", ["bexio", "projects", "edit", "20", "--name", "Updated"]), \
             patch("sys.stdout", io.StringIO()):
            from bexio.cli import main
            main()

        self.assertIn(("PUT", "/pr_project/20"), captured)


class TestProjectsDelete(unittest.TestCase):
    def test_prints_confirmation(self):
        out = capture_with_responses(["projects", "delete", "20"], [{"success": True}])
        self.assertIn("deleted", out)
        self.assertIn("20", out)

    def test_deletes_correct_endpoint(self):
        captured = []

        def fake_request(self, method, path, params=None, body=None, base=None, accept="application/json"):
            captured.append((method, path))
            return {"success": True}

        with patch("bexio.client.BexioClient._request", fake_request), \
             patch("bexio.auth.get_token", return_value="FAKE"), \
             patch("sys.argv", ["bexio", "projects", "delete", "20"]), \
             patch("sys.stdout", io.StringIO()):
            from bexio.cli import main
            main()

        self.assertIn(("DELETE", "/pr_project/20"), captured)


class TestProjectsArchive(unittest.TestCase):
    def test_prints_confirmation(self):
        out = capture_with_responses(["projects", "archive", "20"], [{"success": True}])
        self.assertIn("archived", out)
        self.assertIn("20", out)

    def test_posts_archive_endpoint(self):
        captured = []

        def fake_request(self, method, path, params=None, body=None, base=None, accept="application/json"):
            captured.append((method, path))
            return {"success": True}

        with patch("bexio.client.BexioClient._request", fake_request), \
             patch("bexio.auth.get_token", return_value="FAKE"), \
             patch("sys.argv", ["bexio", "projects", "archive", "20"]), \
             patch("sys.stdout", io.StringIO()):
            from bexio.cli import main
            main()

        self.assertIn(("POST", "/pr_project/20/archive"), captured)


class TestProjectsReactivate(unittest.TestCase):
    def test_prints_confirmation(self):
        out = capture_with_responses(["projects", "reactivate", "20"], [{"success": True}])
        self.assertIn("reactivated", out)
        self.assertIn("20", out)


class TestProjectsTypes(unittest.TestCase):
    def test_shows_type_name(self):
        out = capture_with_responses(["projects", "types"], [[PROJECT_TYPE]])
        self.assertIn("Standard", out)


class TestProjectsStatuses(unittest.TestCase):
    def test_shows_status_name(self):
        out = capture_with_responses(["projects", "statuses"], [[PROJECT_STATUS]])
        self.assertIn("In Progress", out)


# ---------------------------------------------------------------------------
# Milestones
# ---------------------------------------------------------------------------

class TestMilestonesList(unittest.TestCase):
    def test_shows_milestone_name(self):
        out = capture_with_responses(["milestones", "list", "--project-id", "20"], [[MILESTONE]])
        self.assertIn("Phase 1 Launch", out)

    def test_uses_v3_endpoint(self):
        captured = []

        def fake_request(self, method, path, params=None, body=None, base=None, accept="application/json"):
            captured.append((method, path, base))
            return [MILESTONE]

        with patch("bexio.client.BexioClient._request", fake_request), \
             patch("bexio.auth.get_token", return_value="FAKE"), \
             patch("sys.argv", ["bexio", "milestones", "list", "--project-id", "20"]), \
             patch("sys.stdout", io.StringIO()):
            from bexio.cli import main
            main()

        method, path, base = captured[0]
        self.assertEqual(base, "https://api.bexio.com/3.0")

    def test_empty_list_shows_no_milestones(self):
        out = capture_with_responses(["milestones", "list", "--project-id", "20"], [[]])
        self.assertIn("No milestones", out)


class TestMilestonesCreate(unittest.TestCase):
    def test_prints_confirmation(self):
        out = capture_with_responses(
            ["milestones", "create", "--project-id", "20", "--name", "Phase 1 Launch"],
            [MILESTONE],
        )
        self.assertIn("created", out)
        self.assertIn("100", out)

    def test_posts_correct_endpoint(self):
        captured = []

        def fake_request(self, method, path, params=None, body=None, base=None, accept="application/json"):
            captured.append((method, path, base))
            return MILESTONE

        with patch("bexio.client.BexioClient._request", fake_request), \
             patch("bexio.auth.get_token", return_value="FAKE"), \
             patch("sys.argv", ["bexio", "milestones", "create", "--project-id", "20", "--name", "Phase 1 Launch"]), \
             patch("sys.stdout", io.StringIO()):
            from bexio.cli import main
            main()

        method, path, base = captured[0]
        self.assertEqual(method, "POST")
        self.assertIn("projects/20/milestones", path)
        self.assertEqual(base, "https://api.bexio.com/3.0")


class TestMilestonesDelete(unittest.TestCase):
    def test_prints_confirmation(self):
        out = capture_with_responses(
            ["milestones", "delete", "--project-id", "20", "100"],
            [{"success": True}],
        )
        self.assertIn("deleted", out)
        self.assertIn("100", out)


# ---------------------------------------------------------------------------
# Work packages
# ---------------------------------------------------------------------------

class TestWorkPackagesList(unittest.TestCase):
    def test_shows_package_name(self):
        out = capture_with_responses(["work-packages", "list", "--project-id", "20"], [[WORK_PACKAGE]])
        self.assertIn("Frontend Development", out)

    def test_uses_v3_endpoint(self):
        captured = []

        def fake_request(self, method, path, params=None, body=None, base=None, accept="application/json"):
            captured.append((method, path, base))
            return [WORK_PACKAGE]

        with patch("bexio.client.BexioClient._request", fake_request), \
             patch("bexio.auth.get_token", return_value="FAKE"), \
             patch("sys.argv", ["bexio", "work-packages", "list", "--project-id", "20"]), \
             patch("sys.stdout", io.StringIO()):
            from bexio.cli import main
            main()

        method, path, base = captured[0]
        self.assertEqual(base, "https://api.bexio.com/3.0")

    def test_empty_list_shows_no_packages(self):
        out = capture_with_responses(["work-packages", "list", "--project-id", "20"], [[]])
        self.assertIn("No work packages", out)


class TestWorkPackagesCreate(unittest.TestCase):
    def test_prints_confirmation(self):
        out = capture_with_responses(
            ["work-packages", "create", "--project-id", "20", "--name", "Frontend Development"],
            [WORK_PACKAGE],
        )
        self.assertIn("created", out)
        self.assertIn("200", out)


if __name__ == "__main__":
    unittest.main()

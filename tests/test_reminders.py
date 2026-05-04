"""Tests for reminder commands."""

import io
import json
import os
import unittest
from unittest.mock import patch

from tests.helpers import capture_with_responses

REMINDER = {
    "id": 30,
    "document_nr": "MAN-2024-001",
    "title": "Zahlungserinnerung",
    "contact_id": 5,
    "kb_invoice_id": 99,
    "is_valid_from": "2024-03-01",
    "due_date": "2024-03-15",
    "total": "1500.00",
    "currency_id": 1,
    "kb_item_status_id": 18,
}


class TestRemindersList(unittest.TestCase):
    def test_shows_reminder_title(self):
        out = capture_with_responses(["reminders", "list", "99"], [[REMINDER]])
        self.assertIn("Zahlungserinnerung", out)

    def test_shows_due_date(self):
        out = capture_with_responses(["reminders", "list", "99"], [[REMINDER]])
        self.assertIn("2024-03-15", out)

    def test_shows_total(self):
        out = capture_with_responses(["reminders", "list", "99"], [[REMINDER]])
        self.assertIn("1500.00", out)

    def test_json_output(self):
        out = capture_with_responses(["--json", "reminders", "list", "99"], [[REMINDER]])
        parsed = json.loads(out)
        self.assertEqual(parsed[0]["id"], 30)

    def test_empty_list_shows_no_reminders(self):
        out = capture_with_responses(["reminders", "list", "99"], [[]])
        self.assertIn("No reminders found", out)


class TestRemindersShow(unittest.TestCase):
    def test_shows_id_and_title(self):
        out = capture_with_responses(["reminders", "show", "99", "30"], [REMINDER])
        self.assertIn("30", out)
        self.assertIn("Zahlungserinnerung", out)

    def test_shows_due_date(self):
        out = capture_with_responses(["reminders", "show", "99", "30"], [REMINDER])
        self.assertIn("2024-03-15", out)

    def test_json_output(self):
        out = capture_with_responses(["--json", "reminders", "show", "99", "30"], [REMINDER])
        parsed = json.loads(out)
        self.assertEqual(parsed["id"], 30)


class TestRemindersCreate(unittest.TestCase):
    def test_prints_confirmation(self):
        out = capture_with_responses(["reminders", "create", "99"], [REMINDER])
        self.assertIn("30", out)
        self.assertIn("created", out)

    def test_posts_correct_endpoint(self):
        captured = []

        def fake_request(self, method, path, params=None, body=None, base=None, accept="application/json"):
            captured.append((method, path, body))
            return REMINDER

        with patch("bexio.client.BexioClient._request", fake_request), \
             patch("bexio.auth.get_token", return_value="FAKE"), \
             patch("sys.argv", ["bexio", "reminders", "create", "99"]), \
             patch("sys.stdout", io.StringIO()):
            from bexio.cli import main
            main()

        self.assertEqual(len(captured), 1)
        method, path, body = captured[0]
        self.assertEqual(method, "POST")
        self.assertEqual(path, "/kb_invoice/99/kb_reminder")

    def test_create_with_title(self):
        captured = []

        def fake_request(self, method, path, params=None, body=None, base=None, accept="application/json"):
            captured.append((method, path, body))
            return REMINDER

        with patch("bexio.client.BexioClient._request", fake_request), \
             patch("bexio.auth.get_token", return_value="FAKE"), \
             patch("sys.argv", ["bexio", "reminders", "create", "99", "--title", "Mahnung 1"]), \
             patch("sys.stdout", io.StringIO()):
            from bexio.cli import main
            main()

        _, _, body = captured[0]
        self.assertEqual(body.get("title"), "Mahnung 1")


class TestRemindersDelete(unittest.TestCase):
    def test_prints_confirmation(self):
        out = capture_with_responses(["reminders", "delete", "99", "30"], [{"success": True}])
        self.assertIn("30", out)
        self.assertIn("deleted", out)

    def test_deletes_correct_endpoint(self):
        captured = []

        def fake_request(self, method, path, params=None, body=None, base=None, accept="application/json"):
            captured.append((method, path))
            return {"success": True}

        with patch("bexio.client.BexioClient._request", fake_request), \
             patch("bexio.auth.get_token", return_value="FAKE"), \
             patch("sys.argv", ["bexio", "reminders", "delete", "99", "30"]), \
             patch("sys.stdout", io.StringIO()):
            from bexio.cli import main
            main()

        self.assertIn(("DELETE", "/kb_invoice/99/kb_reminder/30"), captured)


class TestRemindersSend(unittest.TestCase):
    def test_prints_confirmation(self):
        out = capture_with_responses(["reminders", "send", "99", "30"], [{}])
        self.assertIn("30", out)
        self.assertIn("sent", out)

    def test_posts_send_endpoint(self):
        captured = []

        def fake_request(self, method, path, params=None, body=None, base=None, accept="application/json"):
            captured.append((method, path))
            return {}

        with patch("bexio.client.BexioClient._request", fake_request), \
             patch("bexio.auth.get_token", return_value="FAKE"), \
             patch("sys.argv", ["bexio", "reminders", "send", "99", "30"]), \
             patch("sys.stdout", io.StringIO()):
            from bexio.cli import main
            main()

        self.assertIn(("POST", "/kb_invoice/99/kb_reminder/30/send"), captured)


class TestRemindersMarkSent(unittest.TestCase):
    def test_prints_confirmation(self):
        out = capture_with_responses(["reminders", "mark-sent", "99", "30"], [{}])
        self.assertIn("30", out)
        self.assertIn("marked as sent", out)

    def test_posts_mark_as_sent_endpoint(self):
        captured = []

        def fake_request(self, method, path, params=None, body=None, base=None, accept="application/json"):
            captured.append((method, path))
            return {}

        with patch("bexio.client.BexioClient._request", fake_request), \
             patch("bexio.auth.get_token", return_value="FAKE"), \
             patch("sys.argv", ["bexio", "reminders", "mark-sent", "99", "30"]), \
             patch("sys.stdout", io.StringIO()):
            from bexio.cli import main
            main()

        self.assertIn(("POST", "/kb_invoice/99/kb_reminder/30/mark_as_sent"), captured)


class TestRemindersMarkUnsent(unittest.TestCase):
    def test_prints_confirmation(self):
        out = capture_with_responses(["reminders", "mark-unsent", "99", "30"], [{}])
        self.assertIn("30", out)
        self.assertIn("marked as unsent", out)

    def test_posts_mark_as_unsent_endpoint(self):
        captured = []

        def fake_request(self, method, path, params=None, body=None, base=None, accept="application/json"):
            captured.append((method, path))
            return {}

        with patch("bexio.client.BexioClient._request", fake_request), \
             patch("bexio.auth.get_token", return_value="FAKE"), \
             patch("sys.argv", ["bexio", "reminders", "mark-unsent", "99", "30"]), \
             patch("sys.stdout", io.StringIO()):
            from bexio.cli import main
            main()

        self.assertIn(("POST", "/kb_invoice/99/kb_reminder/30/mark_as_unsent"), captured)


class TestRemindersPdf(unittest.TestCase):
    def test_saves_file(self):
        tmp = "/tmp/test_reminder_saves.pdf"
        if os.path.exists(tmp):
            os.unlink(tmp)

        def fake_request(self, method, path, params=None, body=None, base=None, accept="application/json"):
            if accept == "application/pdf":
                return b"FAKEPDF"
            return REMINDER

        buf = io.StringIO()
        with patch("bexio.client.BexioClient._request", fake_request), \
             patch("bexio.auth.get_token", return_value="FAKE"), \
             patch("sys.argv", ["bexio", "reminders", "pdf", "99", "30", "--output", tmp]), \
             patch("sys.stdout", buf):
            from bexio.cli import main
            main()

        self.assertTrue(os.path.exists(tmp))
        with open(tmp, "rb") as f:
            self.assertEqual(f.read(), b"FAKEPDF")
        os.unlink(tmp)

    def test_default_filename(self):
        default_file = "reminder_30.pdf"
        if os.path.exists(default_file):
            os.unlink(default_file)

        def fake_request(self, method, path, params=None, body=None, base=None, accept="application/json"):
            if accept == "application/pdf":
                return b"FAKEPDF"
            return REMINDER

        buf = io.StringIO()
        with patch("bexio.client.BexioClient._request", fake_request), \
             patch("bexio.auth.get_token", return_value="FAKE"), \
             patch("sys.argv", ["bexio", "reminders", "pdf", "99", "30"]), \
             patch("sys.stdout", buf):
            from bexio.cli import main
            main()

        self.assertTrue(os.path.exists(default_file))
        os.unlink(default_file)

    def test_custom_output_flag(self):
        tmp = "/tmp/test_reminder_custom.pdf"
        if os.path.exists(tmp):
            os.unlink(tmp)

        def fake_request(self, method, path, params=None, body=None, base=None, accept="application/json"):
            if accept == "application/pdf":
                return b"FAKEPDF"
            return REMINDER

        buf = io.StringIO()
        with patch("bexio.client.BexioClient._request", fake_request), \
             patch("bexio.auth.get_token", return_value="FAKE"), \
             patch("sys.argv", ["bexio", "reminders", "pdf", "99", "30", "--output", tmp]), \
             patch("sys.stdout", buf):
            from bexio.cli import main
            main()

        out = buf.getvalue()
        self.assertIn(tmp, out)
        self.assertIn("Saved to", out)
        os.unlink(tmp)

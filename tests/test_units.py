"""Tests for units commands."""

import argparse
import io
import json
import unittest
from unittest.mock import patch

from bexio.commands import units
from bexio.client import BexioClient


def _make_parser():
    """Build a units-only argument parser (mirrors cli.py structure)."""
    root = argparse.ArgumentParser(prog="bexio")
    root.add_argument("--json", action="store_true")
    sub = root.add_subparsers(dest="resource")
    units.register(sub)
    return root


def _run(argv, responses):
    """Parse argv through the units sub-parser and call handle(), capturing stdout."""
    # argv is e.g. ["units", "list"] or ["--json", "units", "show", "1"]
    root = _make_parser()
    call_count = [0]

    def fake_request(self, method, path, params=None, body=None):
        result = responses[call_count[0] % len(responses)]
        call_count[0] += 1
        return result

    buf = io.StringIO()
    with patch("bexio.client.BexioClient._request", fake_request), \
         patch("sys.stdout", buf):
        try:
            args = root.parse_args(argv)
            units.handle(args, BexioClient("FAKE"), args.json)
        except SystemExit:
            pass
    return buf.getvalue()


UNIT = {"id": 1, "name": "Stunde"}
UNIT2 = {"id": 2, "name": "Stück"}


class TestUnitsList(unittest.TestCase):
    def test_table_shows_id_and_name(self):
        out = _run(["units", "list"], [[UNIT, UNIT2]])
        self.assertIn("1", out)
        self.assertIn("Stunde", out)
        self.assertIn("2", out)
        self.assertIn("Stück", out)

    def test_json_flag(self):
        out = _run(["--json", "units", "list"], [[UNIT]])
        parsed = json.loads(out)
        self.assertEqual(parsed[0]["id"], 1)
        self.assertEqual(parsed[0]["name"], "Stunde")

    def test_empty_list_no_crash(self):
        out = _run(["units", "list"], [[]])
        self.assertIsInstance(out, str)  # no exception, just empty output


class TestUnitsShow(unittest.TestCase):
    def test_shows_id_and_name(self):
        out = _run(["units", "show", "1"], [UNIT])
        self.assertIn("1", out)
        self.assertIn("Stunde", out)

    def test_correct_endpoint(self):
        captured = []

        def fake_request(self, method, path, params=None, body=None):
            captured.append((method, path))
            return UNIT

        buf = io.StringIO()
        root = _make_parser()
        with patch("bexio.client.BexioClient._request", fake_request), \
             patch("sys.stdout", buf):
            args = root.parse_args(["units", "show", "7"])
            units.handle(args, BexioClient("FAKE"), False)

        self.assertEqual(captured[0][0], "GET")
        self.assertIn("/unit/7", captured[0][1])

    def test_json_flag(self):
        out = _run(["--json", "units", "show", "1"], [UNIT])
        parsed = json.loads(out)
        self.assertEqual(parsed["id"], 1)
        self.assertEqual(parsed["name"], "Stunde")


class TestUnitsCreate(unittest.TestCase):
    def _capture_create(self, extra_args, response=None):
        captured = []
        resp = response or {"id": 5, "name": "Tag"}

        def fake_request(self, method, path, params=None, body=None):
            captured.append((method, path, body))
            return resp

        buf = io.StringIO()
        root = _make_parser()
        with patch("bexio.client.BexioClient._request", fake_request), \
             patch("sys.stdout", buf):
            try:
                args = root.parse_args(["units", "create"] + extra_args)
                units.handle(args, BexioClient("FAKE"), False)
            except SystemExit:
                pass
        return buf.getvalue(), captured

    def test_posts_correct_body(self):
        _, captured = self._capture_create(["--name", "Kilometer"])
        self.assertEqual(captured[0][0], "POST")
        self.assertIn("/unit", captured[0][1])
        self.assertEqual(captured[0][2], {"name": "Kilometer"})

    def test_prints_id_and_name(self):
        out, _ = self._capture_create(["--name", "Kilometer"], {"id": 5, "name": "Kilometer"})
        self.assertIn("5", out)
        self.assertIn("Kilometer", out)

    def test_json_flag(self):
        out = _run(["--json", "units", "create", "--name", "Tag"], [{"id": 5, "name": "Tag"}])
        parsed = json.loads(out)
        self.assertEqual(parsed["id"], 5)
        self.assertEqual(parsed["name"], "Tag")

    def test_missing_name_exits(self):
        root = _make_parser()
        with self.assertRaises(SystemExit):
            root.parse_args(["units", "create"])  # --name required; argparse exits


class TestUnitsDelete(unittest.TestCase):
    def test_deletes_correct_endpoint(self):
        captured = []

        def fake_request(self, method, path, params=None, body=None):
            captured.append((method, path))
            return {"success": True}

        buf = io.StringIO()
        root = _make_parser()
        with patch("bexio.client.BexioClient._request", fake_request), \
             patch("sys.stdout", buf):
            args = root.parse_args(["units", "delete", "3"])
            units.handle(args, BexioClient("FAKE"), False)

        self.assertEqual(captured[0][0], "DELETE")
        self.assertIn("/unit/3", captured[0][1])

    def test_prints_confirmation(self):
        out = _run(["units", "delete", "3"], [{"success": True}])
        self.assertIn("3", out)

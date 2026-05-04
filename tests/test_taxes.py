"""Tests for taxes and vat-periods commands."""

import argparse
import io
import json
import unittest
from unittest.mock import patch

from bexio.commands.taxes import handle_taxes, handle_vat_periods

TAX = {
    "id": 10,
    "uuid": "abc-123",
    "name": "MwSt. 8.1%",
    "code": "MwSt. 8.1",
    "value": "8.10",
    "is_active": True,
    "display_name": "MwSt. 8.1% (8.10%)",
}

TAX_2 = {
    "id": 11,
    "uuid": "def-456",
    "name": "MwSt. 2.6%",
    "code": "MwSt. 2.6",
    "value": "2.60",
    "is_active": False,
    "display_name": "MwSt. 2.6% (2.60%)",
}

VAT_PERIOD = {
    "id": 1,
    "start": "2024-01-01",
    "end": "2024-12-31",
    "type": "annual",
    "status": "open",
    "closed_at": None,
}

VAT_PERIOD_2 = {
    "id": 2,
    "start": "2023-01-01",
    "end": "2023-12-31",
    "type": "annual",
    "status": "closed",
    "closed_at": "2024-01-15",
}


def _taxes_args(action, limit=100, **kwargs):
    ns = argparse.Namespace(action=action, limit=limit, **kwargs)
    return ns


def _vat_args(action, **kwargs):
    ns = argparse.Namespace(action=action, **kwargs)
    return ns


def _make_client(responses):
    """Build a BexioClient where get_v3() cycles through responses."""
    from bexio.client import BexioClient
    if isinstance(responses, dict):
        responses = [responses]
    call_count = [0]

    def fake_get_v3(path, params=None):
        result = responses[call_count[0] % len(responses)]
        call_count[0] += 1
        return result

    client = BexioClient("FAKE_TOKEN")
    client.get_v3 = fake_get_v3
    return client


def _capture(fn, args, responses, json_flag=False):
    client = _make_client(responses)
    buf = io.StringIO()
    with patch("sys.stdout", buf):
        try:
            fn(args, client, json_flag)
        except SystemExit:
            pass
    return buf.getvalue()


# ── TestTaxesList ──────────────────────────────────────────────────────────────

class TestTaxesList(unittest.TestCase):
    def test_table_output_shows_code_and_name(self):
        out = _capture(handle_taxes, _taxes_args("list"), [{"data": [TAX]}])
        self.assertIn("MwSt. 8.1", out)
        self.assertIn("MwSt. 8.1%", out)

    def test_table_output_shows_value(self):
        out = _capture(handle_taxes, _taxes_args("list"), [{"data": [TAX]}])
        self.assertIn("8.10", out)

    def test_table_output_shows_active_status(self):
        out = _capture(handle_taxes, _taxes_args("list"), [{"data": [TAX, TAX_2]}])
        self.assertIn("Yes", out)
        self.assertIn("No", out)

    def test_limit_param_passed(self):
        captured = []

        def fake_get_v3(path, params=None):
            captured.append((path, params))
            return {"data": [TAX]}

        client = _make_client([{"data": [TAX]}])
        client.get_v3 = fake_get_v3

        buf = io.StringIO()
        with patch("sys.stdout", buf):
            handle_taxes(_taxes_args("list", limit=5), client, False)

        self.assertEqual(len(captured), 1)
        self.assertEqual(captured[0][1]["limit"], 5)

    def test_json_flag(self):
        out = _capture(handle_taxes, _taxes_args("list"), [{"data": [TAX]}], json_flag=True)
        parsed = json.loads(out)
        self.assertEqual(parsed[0]["id"], 10)

    def test_empty_list_no_crash(self):
        out = _capture(handle_taxes, _taxes_args("list"), [{"data": []}])
        self.assertIsNotNone(out)


# ── TestTaxesShow ──────────────────────────────────────────────────────────────

class TestTaxesShow(unittest.TestCase):
    def test_shows_id(self):
        out = _capture(handle_taxes, _taxes_args("show", id=10), [TAX])
        self.assertIn("10", out)

    def test_shows_name(self):
        out = _capture(handle_taxes, _taxes_args("show", id=10), [TAX])
        self.assertIn("MwSt. 8.1%", out)

    def test_shows_code(self):
        out = _capture(handle_taxes, _taxes_args("show", id=10), [TAX])
        self.assertIn("MwSt. 8.1", out)

    def test_shows_value(self):
        out = _capture(handle_taxes, _taxes_args("show", id=10), [TAX])
        self.assertIn("8.10", out)

    def test_json_flag(self):
        out = _capture(handle_taxes, _taxes_args("show", id=10), [TAX], json_flag=True)
        parsed = json.loads(out)
        self.assertEqual(parsed["id"], 10)

    def test_correct_endpoint_called(self):
        captured = []

        def fake_get_v3(path, params=None):
            captured.append(path)
            return TAX

        client = _make_client([TAX])
        client.get_v3 = fake_get_v3

        buf = io.StringIO()
        with patch("sys.stdout", buf):
            handle_taxes(_taxes_args("show", id=10), client, False)

        self.assertEqual(len(captured), 1)
        self.assertIn("/taxes/10", captured[0])


# ── TestVatPeriodsList ─────────────────────────────────────────────────────────

class TestVatPeriodsList(unittest.TestCase):
    def test_table_output_shows_start_end(self):
        out = _capture(handle_vat_periods, _vat_args("list"), [{"data": [VAT_PERIOD]}])
        self.assertIn("2024-01-01", out)
        self.assertIn("2024-12-31", out)

    def test_table_output_shows_type_and_status(self):
        out = _capture(handle_vat_periods, _vat_args("list"), [{"data": [VAT_PERIOD]}])
        self.assertIn("annual", out)
        self.assertIn("open", out)

    def test_table_output_shows_id(self):
        out = _capture(handle_vat_periods, _vat_args("list"), [{"data": [VAT_PERIOD]}])
        self.assertIn("1", out)

    def test_json_flag(self):
        out = _capture(handle_vat_periods, _vat_args("list"), [{"data": [VAT_PERIOD]}], json_flag=True)
        parsed = json.loads(out)
        self.assertEqual(parsed[0]["id"], 1)

    def test_empty_list_no_crash(self):
        out = _capture(handle_vat_periods, _vat_args("list"), [{"data": []}])
        self.assertIsNotNone(out)


# ── TestVatPeriodsShow ─────────────────────────────────────────────────────────

class TestVatPeriodsShow(unittest.TestCase):
    def test_shows_id(self):
        out = _capture(handle_vat_periods, _vat_args("show", id=1), [VAT_PERIOD])
        self.assertIn("1", out)

    def test_shows_start_end(self):
        out = _capture(handle_vat_periods, _vat_args("show", id=1), [VAT_PERIOD])
        self.assertIn("2024-01-01", out)
        self.assertIn("2024-12-31", out)

    def test_shows_type(self):
        out = _capture(handle_vat_periods, _vat_args("show", id=1), [VAT_PERIOD])
        self.assertIn("annual", out)

    def test_shows_status(self):
        out = _capture(handle_vat_periods, _vat_args("show", id=1), [VAT_PERIOD])
        self.assertIn("open", out)

    def test_json_flag(self):
        out = _capture(handle_vat_periods, _vat_args("show", id=1), [VAT_PERIOD], json_flag=True)
        parsed = json.loads(out)
        self.assertEqual(parsed["id"], 1)

    def test_correct_endpoint_called(self):
        captured = []

        def fake_get_v3(path, params=None):
            captured.append(path)
            return VAT_PERIOD

        client = _make_client([VAT_PERIOD])
        client.get_v3 = fake_get_v3

        buf = io.StringIO()
        with patch("sys.stdout", buf):
            handle_vat_periods(_vat_args("show", id=1), client, False)

        self.assertEqual(len(captured), 1)
        self.assertIn("/accounting/vat_periods/1", captured[0])

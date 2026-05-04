"""Tests for currencies commands."""

import io
import json
import unittest
from unittest.mock import patch

CURRENCY_CHF = {
    "id": 1,
    "name": "CHF",
    "round_factor": 0.05,
}

CURRENCY_EUR = {
    "id": 2,
    "name": "EUR",
    "round_factor": 0.01,
}

EXCHANGE_RATES = {
    "data": [
        {"currency_id": 1, "name": "CHF", "rate": 1.0},
        {"currency_id": 2, "name": "EUR", "rate": 0.95},
    ]
}


def _run(argv, responses):
    """Run CLI with mocked _request (accepts base= kwarg), return captured stdout."""
    call_count = [0]

    def fake_request(self, method, path, params=None, body=None, base=None):
        result = responses[call_count[0] % len(responses)]
        call_count[0] += 1
        return result

    buf = io.StringIO()
    with patch("sys.argv", ["bexio"] + argv), \
         patch("bexio.auth.get_token", return_value="FAKE_TOKEN"), \
         patch("bexio.client.BexioClient._request", fake_request), \
         patch("sys.stdout", buf):
        try:
            from bexio.cli import main
            main()
        except SystemExit:
            pass
    return buf.getvalue()


class TestCurrenciesList(unittest.TestCase):
    def test_shows_id_name_round_factor(self):
        out = _run(["currencies", "list"], [[CURRENCY_CHF, CURRENCY_EUR]])
        self.assertIn("1", out)
        self.assertIn("CHF", out)
        self.assertIn("0.05", out)

    def test_shows_multiple_currencies(self):
        out = _run(["currencies", "list"], [[CURRENCY_CHF, CURRENCY_EUR]])
        self.assertIn("EUR", out)
        self.assertIn("2", out)

    def test_json_flag(self):
        out = _run(["--json", "currencies", "list"], [[CURRENCY_CHF]])
        parsed = json.loads(out)
        self.assertEqual(parsed[0]["id"], 1)
        self.assertEqual(parsed[0]["name"], "CHF")

    def test_empty_list_no_crash(self):
        out = _run(["currencies", "list"], [[]])
        self.assertIsNotNone(out)

    def test_calls_v3_endpoint(self):
        captured = []

        def fake_request(self, method, path, params=None, body=None, base=None):
            captured.append((method, path, base))
            return [CURRENCY_CHF]

        buf = io.StringIO()
        with patch("sys.argv", ["bexio", "currencies", "list"]), \
             patch("bexio.auth.get_token", return_value="FAKE_TOKEN"), \
             patch("bexio.client.BexioClient._request", fake_request), \
             patch("sys.stdout", buf):
            try:
                from bexio.cli import main
                main()
            except SystemExit:
                pass

        method, path, base = captured[0]
        self.assertEqual(method, "GET")
        self.assertIn("/currencies", path)
        self.assertIn("3.0", base)


class TestCurrenciesShow(unittest.TestCase):
    def test_shows_fields(self):
        out = _run(["currencies", "show", "1"], [CURRENCY_CHF])
        self.assertIn("1", out)
        self.assertIn("CHF", out)
        self.assertIn("0.05", out)

    def test_calls_v3_endpoint_with_id(self):
        captured = []

        def fake_request(self, method, path, params=None, body=None, base=None):
            captured.append((method, path, base))
            return CURRENCY_CHF

        buf = io.StringIO()
        with patch("sys.argv", ["bexio", "currencies", "show", "1"]), \
             patch("bexio.auth.get_token", return_value="FAKE_TOKEN"), \
             patch("bexio.client.BexioClient._request", fake_request), \
             patch("sys.stdout", buf):
            try:
                from bexio.cli import main
                main()
            except SystemExit:
                pass

        method, path, base = captured[0]
        self.assertEqual(method, "GET")
        self.assertIn("/currencies/1", path)
        self.assertIn("3.0", base)

    def test_json_flag(self):
        out = _run(["--json", "currencies", "show", "1"], [CURRENCY_CHF])
        parsed = json.loads(out)
        self.assertEqual(parsed["id"], 1)
        self.assertEqual(parsed["name"], "CHF")


class TestCurrenciesExchangeRates(unittest.TestCase):
    def test_calls_v3_exchange_rates_endpoint(self):
        captured = []

        def fake_request(self, method, path, params=None, body=None, base=None):
            captured.append((method, path, base))
            return EXCHANGE_RATES

        buf = io.StringIO()
        with patch("sys.argv", ["bexio", "currencies", "exchange-rates"]), \
             patch("bexio.auth.get_token", return_value="FAKE_TOKEN"), \
             patch("bexio.client.BexioClient._request", fake_request), \
             patch("sys.stdout", buf):
            try:
                from bexio.cli import main
                main()
            except SystemExit:
                pass

        method, path, base = captured[0]
        self.assertEqual(method, "GET")
        self.assertIn("exchange-rates", path)
        self.assertIn("3.0", base)

    def test_output_contains_data(self):
        out = _run(["currencies", "exchange-rates"], [EXCHANGE_RATES])
        self.assertIn("CHF", out)
        self.assertIn("EUR", out)

    def test_json_output_is_valid(self):
        out = _run(["--json", "currencies", "exchange-rates"], [EXCHANGE_RATES])
        parsed = json.loads(out)
        self.assertIn("data", parsed)

"""Tests for manual-entries (Sammelbuchungen) commands."""

import io
import unittest
from argparse import Namespace
from unittest.mock import patch

from tests.helpers import capture_with_responses

ACCOUNTS = [
    {"id": 24, "account_no": "1030", "name": "Wise CHF", "account_type": "1", "is_active": True},
    {"id": 243, "account_no": "4450", "name": "Fremdleistungen", "account_type": "3", "is_active": True},
    {"id": 171, "account_no": "4400", "name": "Materialaufwand", "account_type": "3", "is_active": True},
    {"id": 99, "account_no": "6949", "name": "Kursdifferenzen", "account_type": "3", "is_active": True},
    {"id": 60, "account_no": "3400", "name": "Dienstleistungsertrag", "account_type": "4", "is_active": True},
]

TAXES = [
    {"id": 53, "code": "Vorsteuer8.1", "name": "Vorsteuer 8.1%", "type": "tax_type_expenditure",
     "value": "8.1", "is_active": True},
    {"id": 49, "code": "V00", "name": "Ohne MWST", "type": "tax_type_expenditure",
     "value": "0", "is_active": True},
    {"id": 12, "code": "UN81", "name": "Umsatz normal 8.1%", "type": "tax_type_sales",
     "value": "8.1", "is_active": True},
    {"id": 7, "code": "ALT77", "name": "Vorsteuer 7.7% (alt)", "type": "tax_type_expenditure",
     "value": "7.7", "is_active": False},
]

CURRENCIES = [
    {"id": 1, "name": "CHF", "round_factor": 0.05},
    {"id": 2, "name": "EUR", "round_factor": 0.01},
    {"id": 5, "name": "BRL", "round_factor": 0.01},
]

ENTRY_702 = {
    "id": 827,
    "reference_nr": "702",
    "date": "2026-07-01",
    "type": "manual_compound_entry",
    "entries": [
        {"debit_account_id": 24, "credit_account_id": None, "amount": 119.84, "currency_id": 1,
         "currency_factor": 1, "base_currency_amount": 119.84, "tax_id": None,
         "description": "Rückerstattung"},
        {"debit_account_id": None, "credit_account_id": 243, "amount": 765.35, "currency_id": 5,
         "currency_factor": 0.157222, "base_currency_amount": 120.33, "tax_id": 53,
         "description": "Rückerstattung"},
        {"debit_account_id": 99, "credit_account_id": None, "amount": 0.49, "currency_id": 1,
         "currency_factor": 1, "base_currency_amount": 0.49, "tax_id": None,
         "description": "Kursdifferenz"},
    ],
}

ENTRY_OLD = {
    "id": 790,
    "reference_nr": "690",
    "date": "2026-06-26",
    "type": "manual_compound_entry",
    "entries": [
        {"debit_account_id": 171, "credit_account_id": None, "amount": 10.0, "currency_id": 1,
         "currency_factor": 1, "base_currency_amount": 10.0, "tax_id": None, "description": "x"},
        {"debit_account_id": None, "credit_account_id": 24, "amount": 10.0, "currency_id": 1,
         "currency_factor": 1, "base_currency_amount": 10.0, "tax_id": None, "description": "x"},
    ],
}


class FakeClient:
    """Client stub that answers per path and records every call."""

    def __init__(self, entries=None, accounts=None, taxes=None, currencies=None, posted=None):
        self.entries = entries if entries is not None else [ENTRY_702, ENTRY_OLD]
        self.accounts = accounts if accounts is not None else ACCOUNTS
        self.taxes = taxes if taxes is not None else TAXES
        self.currencies = currencies if currencies is not None else CURRENCIES
        self.posted = posted if posted is not None else {"id": 999, "reference_nr": "702"}
        self.calls = []

    def get(self, path, params=None):
        self.calls.append(("GET", path))
        if path.startswith("/accounts"):
            return self.accounts
        raise AssertionError(f"unexpected GET {path}")

    def get_v3(self, path, params=None):
        self.calls.append(("GET3", path))
        if path.startswith("/taxes"):
            return self.taxes
        if path.startswith("/currencies"):
            return self.currencies
        if path.startswith("/accounting/manual_entries"):
            return self.entries
        raise AssertionError(f"unexpected GET3 {path}")

    def post_v3(self, path, body=None):
        self.calls.append(("POST3", path, body))
        return self.posted

    def put_v3(self, path, body=None):
        self.calls.append(("PUT3", path, body))
        return self.posted

    def delete_v3(self, path):
        self.calls.append(("DELETE3", path))
        return {}


def run_handle(args_ns, client, json_flag=False):
    """Run manual_entries.handle with stdout captured."""
    from bexio.commands import manual_entries

    buf = io.StringIO()
    with patch("sys.stdout", buf):
        manual_entries.handle(args_ns, client, json_flag)
    return buf.getvalue()


def show_args(entry_id, limit=2000):
    return Namespace(action="show", id=entry_id, limit=limit)


def create_args(**over):
    base = dict(action="create", date="2026-07-01", reference_nr=None, line=[],
                lines_file=None, limit=500)
    base.update(over)
    return Namespace(**base)


class TestManualEntriesRead(unittest.TestCase):
    def test_list_shows_id_date_and_reference(self):
        out = capture_with_responses(["manual-entries", "list", "--limit", "5"],
                                     [[ENTRY_702, ENTRY_OLD]])
        self.assertIn("827", out)
        self.assertIn("2026-07-01", out)
        self.assertIn("702", out)
        self.assertIn("790", out)

    def test_list_filters_by_date_range(self):
        out = capture_with_responses(
            ["manual-entries", "list", "--from", "2026-07-01", "--to", "2026-07-31"],
            [[ENTRY_702, ENTRY_OLD]])
        self.assertIn("827", out)
        self.assertNotIn("790", out)

    def test_show_prints_account_numbers_not_ids(self):
        out = run_handle(show_args(827), FakeClient())
        self.assertIn("4450", out)
        self.assertIn("1030", out)
        self.assertIn("6949", out)

    def test_show_prints_tax_code_not_id(self):
        out = run_handle(show_args(827), FakeClient())
        self.assertIn("Vorsteuer8.1", out)

    def test_show_prints_debit_and_credit_side(self):
        out = run_handle(show_args(827), FakeClient())
        self.assertIn("Soll", out)
        self.assertIn("Haben", out)

    def test_show_unknown_account_id_does_not_break(self):
        entry = {
            "id": 900, "reference_nr": "800", "date": "2026-07-05",
            "type": "manual_compound_entry",
            "entries": [
                {"debit_account_id": 4711, "credit_account_id": None, "amount": 5.0,
                 "currency_id": 1, "currency_factor": 1, "base_currency_amount": 5.0,
                 "tax_id": None, "description": "y"},
                {"debit_account_id": None, "credit_account_id": 24, "amount": 5.0,
                 "currency_id": 1, "currency_factor": 1, "base_currency_amount": 5.0,
                 "tax_id": None, "description": "y"},
            ],
        }
        out = run_handle(show_args(900), FakeClient(entries=[entry]))
        self.assertIn("4711", out)
        self.assertIn("id", out.lower())

    def test_show_unknown_entry_id_errors_with_limit_hint(self):
        from bexio.commands.manual_entries import ManualEntryError

        with self.assertRaises(ManualEntryError) as ctx:
            run_handle(show_args(12345), FakeClient())
        self.assertIn("12345", str(ctx.exception))
        self.assertIn("--limit", str(ctx.exception))


class TestResolveAccountsAndTaxes(unittest.TestCase):
    def _resolver(self, client=None):
        from bexio.commands.manual_entries import Resolver

        return Resolver(client or FakeClient())

    def test_account_number_resolves_to_id(self):
        self.assertEqual(self._resolver().account_id("4450"), 243)

    def test_account_lookup_is_cached(self):
        client = FakeClient()
        r = self._resolver(client)
        r.account_id("4450")
        r.account_id("1030")
        r.account_id("6949")
        self.assertEqual([c for c in client.calls if c[1].startswith("/accounts")].__len__(), 1)

    def test_unknown_account_number_lists_near_matches(self):
        from bexio.commands.manual_entries import ManualEntryError

        with self.assertRaises(ManualEntryError) as ctx:
            self._resolver().account_id("4451")
        self.assertIn("4450", str(ctx.exception))

    def test_account_id_reverse_lookup(self):
        self.assertEqual(self._resolver().account_no(243), "4450")
        self.assertIsNone(self._resolver().account_no(4711))

    def test_tax_code_resolves_to_id(self):
        self.assertEqual(self._resolver().tax_id("Vorsteuer8.1", account_no="4450"), 53)

    def test_tax_code_lookup_is_case_insensitive(self):
        self.assertEqual(self._resolver().tax_id("v00", account_no="4450"), 49)

    def test_inactive_tax_code_is_refused(self):
        from bexio.commands.manual_entries import ManualEntryError

        with self.assertRaises(ManualEntryError) as ctx:
            self._resolver().tax_id("ALT77", account_no="4450")
        self.assertIn("inaktiv", str(ctx.exception).lower())

    def test_sales_tax_code_on_expense_line_is_refused(self):
        from bexio.commands.manual_entries import ManualEntryError

        with self.assertRaises(ManualEntryError) as ctx:
            self._resolver().tax_id("UN81", account_no="4450")
        self.assertIn("UN81", str(ctx.exception))

    def test_sales_tax_code_on_revenue_line_is_allowed(self):
        self.assertEqual(self._resolver().tax_id("UN81", account_no="3400"), 12)

    def test_unknown_tax_code_lists_active_codes(self):
        from bexio.commands.manual_entries import ManualEntryError

        with self.assertRaises(ManualEntryError) as ctx:
            self._resolver().tax_id("Vorsteuer9.9", account_no="4450")
        self.assertIn("V00", str(ctx.exception))

    def test_currency_code_resolves_to_id(self):
        self.assertEqual(self._resolver().currency_id("BRL"), 5)
        self.assertEqual(self._resolver().currency_id("chf"), 1)

    def test_unknown_currency_is_refused(self):
        from bexio.commands.manual_entries import ManualEntryError

        with self.assertRaises(ManualEntryError):
            self._resolver().currency_id("XXX")

    def test_tax_id_reverse_lookup(self):
        self.assertEqual(self._resolver().tax_code(53), "Vorsteuer8.1")
        self.assertIsNone(self._resolver().tax_code(4711))


class TestCreateAndBalance(unittest.TestCase):
    LINES_702 = [
        "debit=1030,amount=119.84,currency=CHF,text=Rückerstattung",
        "credit=4450,amount=765.35,currency=BRL,rate=0.157222,tax=Vorsteuer8.1,text=Rückerstattung",
        "debit=6949,amount=0.49,currency=CHF,text=Kursdifferenz",
    ]

    def test_parse_line_reads_named_fields(self):
        from bexio.commands.manual_entries import parse_line

        line = parse_line("credit=4450,amount=765.35,currency=BRL,rate=0.157222,"
                          "tax=Vorsteuer8.1,text=Hetzner Juli")
        self.assertEqual(line["credit"], "4450")
        self.assertIsNone(line["debit"])
        self.assertEqual(line["amount"], 765.35)
        self.assertEqual(line["currency"], "BRL")
        self.assertEqual(line["rate"], 0.157222)
        self.assertEqual(line["tax"], "Vorsteuer8.1")
        self.assertEqual(line["text"], "Hetzner Juli")

    def test_parse_line_defaults_currency_chf_and_rate_one(self):
        from bexio.commands.manual_entries import parse_line

        line = parse_line("debit=1030,amount=10,text=x")
        self.assertEqual(line["currency"], "CHF")
        self.assertEqual(line["rate"], 1.0)
        self.assertIsNone(line["tax"])

    def test_parse_line_keeps_comma_inside_text(self):
        from bexio.commands.manual_entries import parse_line

        line = parse_line("debit=1030,amount=10,text=Hetzner, Juli 2026")
        self.assertEqual(line["text"], "Hetzner, Juli 2026")

    def test_parse_line_requires_exactly_one_side(self):
        from bexio.commands.manual_entries import ManualEntryError, parse_line

        with self.assertRaises(ManualEntryError):
            parse_line("debit=1030,credit=4450,amount=10,text=x")
        with self.assertRaises(ManualEntryError):
            parse_line("amount=10,text=x")

    def test_parse_line_rejects_unknown_field(self):
        from bexio.commands.manual_entries import ManualEntryError, parse_line

        with self.assertRaises(ManualEntryError) as ctx:
            parse_line("debit=1030,amount=10,betrag=5,text=x")
        self.assertIn("betrag", str(ctx.exception))

    def test_parse_line_requires_positive_amount(self):
        from bexio.commands.manual_entries import ManualEntryError, parse_line

        with self.assertRaises(ManualEntryError):
            parse_line("debit=1030,amount=0,text=x")

    def test_beleg_702_produces_expected_payload(self):
        client = FakeClient(entries=[ENTRY_OLD])  # Beleg 702 not booked yet
        run_handle(create_args(line=self.LINES_702, reference_nr="702"), client)
        posts = [c for c in client.calls if c[0] == "POST3"]
        self.assertEqual(len(posts), 1)
        path, body = posts[0][1], posts[0][2]
        self.assertEqual(path, "/accounting/manual_entries")
        self.assertEqual(body["type"], "manual_compound_entry")
        self.assertEqual(body["date"], "2026-07-01")
        self.assertEqual(body["reference_nr"], "702")
        self.assertEqual(body["entries"], [
            {"debit_account_id": 24, "credit_account_id": None, "amount": 119.84,
             "currency_id": 1, "currency_factor": 1.0, "base_currency_amount": 119.84,
             "description": "Rückerstattung"},
            {"debit_account_id": None, "credit_account_id": 243, "amount": 765.35,
             "currency_id": 5, "currency_factor": 0.157222, "base_currency_amount": 120.33,
             "tax_id": 53, "description": "Rückerstattung"},
            {"debit_account_id": 99, "credit_account_id": None, "amount": 0.49,
             "currency_id": 1, "currency_factor": 1.0, "base_currency_amount": 0.49,
             "description": "Kursdifferenz"},
        ])

    def test_unbalanced_entry_names_both_sums_and_difference(self):
        from bexio.commands.manual_entries import ManualEntryError

        client = FakeClient()
        lines = [
            "debit=1030,amount=100,text=x",
            "credit=4450,amount=90,text=x",
        ]
        with self.assertRaises(ManualEntryError) as ctx:
            run_handle(create_args(line=lines), client)
        msg = str(ctx.exception)
        self.assertIn("100", msg)
        self.assertIn("90", msg)
        self.assertIn("10", msg)
        self.assertFalse([c for c in client.calls if c[0] == "POST3"])

    def test_missing_date_is_refused(self):
        from bexio.commands.manual_entries import ManualEntryError

        client = FakeClient()
        with self.assertRaises(ManualEntryError):
            run_handle(create_args(date=None, line=self.LINES_702), client)
        self.assertFalse([c for c in client.calls if c[0] == "POST3"])

    def test_malformed_date_is_refused(self):
        from bexio.commands.manual_entries import ManualEntryError

        with self.assertRaises(ManualEntryError):
            run_handle(create_args(date="01.07.2026", line=self.LINES_702), FakeClient())

    def test_no_lines_is_refused(self):
        from bexio.commands.manual_entries import ManualEntryError

        with self.assertRaises(ManualEntryError):
            run_handle(create_args(line=[]), FakeClient())

    def test_date_is_sent_verbatim(self):
        client = FakeClient()
        run_handle(create_args(date="2026-07-01", line=self.LINES_702), client)
        body = [c for c in client.calls if c[0] == "POST3"][0][2]
        self.assertEqual(body["date"], "2026-07-01")

    def test_existing_reference_nr_is_refused(self):
        from bexio.commands.manual_entries import ManualEntryError

        client = FakeClient()
        with self.assertRaises(ManualEntryError) as ctx:
            run_handle(create_args(line=self.LINES_702, reference_nr="690"), client)
        self.assertIn("690", str(ctx.exception))
        self.assertIn("790", str(ctx.exception))
        self.assertFalse([c for c in client.calls if c[0] == "POST3"])

    def test_reference_nr_is_optional(self):
        client = FakeClient()
        run_handle(create_args(line=self.LINES_702), client)
        body = [c for c in client.calls if c[0] == "POST3"][0][2]
        self.assertNotIn("reference_nr", body)

    def test_lines_file_is_accepted(self):
        import json
        import tempfile

        payload = [
            {"debit": "1030", "amount": 10, "text": "x"},
            {"credit": "4450", "amount": 10, "text": "x"},
        ]
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False,
                                         encoding="utf-8") as fh:
            json.dump(payload, fh)
            path = fh.name
        client = FakeClient()
        run_handle(create_args(line=[], lines_file=path), client)
        body = [c for c in client.calls if c[0] == "POST3"][0][2]
        self.assertEqual(len(body["entries"]), 2)


class TestEditAndDelete(unittest.TestCase):
    """The v3 PUT replaces the whole line set — an omitted line is GONE.

    Verified against the live tenant on 2026-08-06 with a 0.01 test entry
    (see docs/solutions). Every edit therefore reads, merges and writes back
    all lines, and `edit --line` means "this is the complete new line set".
    """

    def edit_args(self, entry_id=831, **over):
        base = dict(action="edit", id=entry_id, date=None, reference_nr=None,
                    line=[], lines_file=None, limit=2000)
        base.update(over)
        return Namespace(**base)

    def test_edit_without_lines_writes_all_existing_lines_back(self):
        client = FakeClient(entries=[ENTRY_702])
        run_handle(self.edit_args(entry_id=827, date="2026-07-02"), client)
        puts = [c for c in client.calls if c[0] == "PUT3"]
        self.assertEqual(len(puts), 1)
        path, body = puts[0][1], puts[0][2]
        self.assertEqual(path, "/accounting/manual_entries/827")
        self.assertEqual(body["date"], "2026-07-02")
        self.assertEqual(len(body["entries"]), 3)
        self.assertEqual(body["entries"][1]["credit_account_id"], 243)
        self.assertEqual(body["entries"][1]["tax_id"], 53)
        self.assertEqual(body["entries"][1]["base_currency_amount"], 120.33)

    def test_edit_strips_read_only_line_fields(self):
        client = FakeClient(entries=[ENTRY_702])
        run_handle(self.edit_args(entry_id=827, reference_nr="702b"), client)
        body = [c for c in client.calls if c[0] == "PUT3"][0][2]
        for line in body["entries"]:
            self.assertNotIn("id", line)
            self.assertNotIn("created_by_user_id", line)

    def test_edit_with_lines_replaces_the_whole_set(self):
        client = FakeClient(entries=[ENTRY_702])
        run_handle(self.edit_args(entry_id=827, line=[
            "debit=1030,amount=50,currency=CHF,text=neu",
            "credit=4450,amount=50,currency=CHF,text=neu",
        ]), client)
        body = [c for c in client.calls if c[0] == "PUT3"][0][2]
        self.assertEqual(len(body["entries"]), 2)
        self.assertEqual(body["entries"][0]["amount"], 50.0)

    def test_edit_checks_balance_before_sending(self):
        from bexio.commands.manual_entries import ManualEntryError

        client = FakeClient(entries=[ENTRY_702])
        with self.assertRaises(ManualEntryError):
            run_handle(self.edit_args(entry_id=827, line=[
                "debit=1030,amount=50,text=x",
                "credit=4450,amount=40,text=x",
            ]), client)
        self.assertFalse([c for c in client.calls if c[0] == "PUT3"])

    def test_edit_without_any_change_is_refused(self):
        from bexio.commands.manual_entries import ManualEntryError

        client = FakeClient(entries=[ENTRY_702])
        with self.assertRaises(ManualEntryError):
            run_handle(self.edit_args(entry_id=827), client)
        self.assertFalse([c for c in client.calls if c[0] == "PUT3"])

    def test_edit_unknown_id_errors(self):
        from bexio.commands.manual_entries import ManualEntryError

        with self.assertRaises(ManualEntryError) as ctx:
            run_handle(self.edit_args(entry_id=99999, date="2026-07-02"), FakeClient())
        self.assertIn("99999", str(ctx.exception))

    def test_delete_uses_the_api_id(self):
        client = FakeClient()
        run_handle(Namespace(action="delete", id=827, limit=2000), client)
        deletes = [c for c in client.calls if c[0] == "DELETE3"]
        self.assertEqual(deletes[0][1], "/accounting/manual_entries/827")

    def test_delete_refuses_a_beleg_number(self):
        from bexio.commands.manual_entries import ManualEntryError

        client = FakeClient()
        with self.assertRaises(ManualEntryError) as ctx:
            run_handle(Namespace(action="delete", id=702, limit=2000), client)
        msg = str(ctx.exception)
        self.assertIn("702", msg)
        self.assertIn("827", msg)  # names the API id it is the Beleg of
        self.assertFalse([c for c in client.calls if c[0] == "DELETE3"])

    def test_delete_unknown_id_errors(self):
        from bexio.commands.manual_entries import ManualEntryError

        client = FakeClient()
        with self.assertRaises(ManualEntryError):
            run_handle(Namespace(action="delete", id=99999, limit=2000), client)
        self.assertFalse([c for c in client.calls if c[0] == "DELETE3"])


class TestCliRegistration(unittest.TestCase):
    def test_manual_entries_is_registered_in_cli(self):
        out = capture_with_responses(["--help"], [{}])
        self.assertIn("manual-entries", out)


class TestMcpTools(unittest.TestCase):
    def setUp(self):
        try:
            import bexio.mcp_server  # noqa: F401
        except ImportError:
            self.skipTest("mcp package not installed")

    def test_manual_entry_tools_exist(self):
        import bexio.mcp_server as m

        for name in ("list_manual_entries", "show_manual_entry", "create_manual_entry"):
            self.assertTrue(hasattr(m, name), f"missing MCP tool {name}")

    def test_create_tool_docstring_warns_about_ledger(self):
        import bexio.mcp_server as m

        doc = (m.create_manual_entry.__doc__ or "").lower()
        self.assertTrue("hauptbuch" in doc or "ledger" in doc)


if __name__ == "__main__":
    unittest.main()

"""Manual entry (Sammelbuchung) commands — general ledger, v3 API.

Accounts are addressed by account NUMBER (4450) and taxes by CODE (Vorsteuer8.1),
never by installation-specific IDs: an ID typo is invisible, a wrong account number
is readable. IDs are resolved internally against /2.0/accounts and /3.0/taxes.
"""

import difflib
import json
import re
import sys

from bexio.output import print_json

MANUAL_ENTRIES_PATH = "/accounting/manual_entries"
LINE_FIELDS = ("debit", "credit", "amount", "currency", "rate", "tax", "text")
EXPENSE_ACCOUNT_CLASSES = ("4", "5", "6")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
# split "a=1,b=2" on commas that start a new field, so a comma inside text survives
FIELD_SPLIT_RE = re.compile(r",(?=(?:%s)=)" % "|".join(LINE_FIELDS))


class ManualEntryError(Exception):
    """Refusal before any request is sent."""


def register(sub):
    p = sub.add_parser("manual-entries", help="Manual entry (Sammelbuchung) commands")
    s = p.add_subparsers(dest="action")

    ls = s.add_parser("list", help="List manual entries")
    ls.add_argument("--limit", type=int, default=100)
    ls.add_argument("--from", dest="date_from", help="Only entries on/after this date (YYYY-MM-DD)")
    ls.add_argument("--to", dest="date_to", help="Only entries on/before this date (YYYY-MM-DD)")

    show = s.add_parser("show", help="Show one manual entry with all its lines")
    show.add_argument("id", type=int, help="API id (NOT the Beleg/reference number)")
    show.add_argument("--limit", type=int, default=2000,
                      help="How many entries to scan for the id (the API has no single-entry GET)")

    create = s.add_parser(
        "create",
        help="Create a compound manual entry",
        description="Create a Sammelbuchung. The date is sent verbatim as YYYY-MM-DD and read "
                    "back unchanged — the web UI may DISPLAY a neighbouring day, the API holds "
                    "the truth. Debit and credit totals must match or nothing is sent.",
    )
    create.add_argument("--date", help="Booking date (YYYY-MM-DD)")
    create.add_argument("--reference-nr", dest="reference_nr",
                        help="Beleg number (visible document no, NOT the API id). "
                             "Refused when it already exists.")
    create.add_argument("--line", action="append", default=[],
                        help="Repeatable. Named fields: "
                             "debit=<account-no>|credit=<account-no>,amount=,currency=CHF,"
                             "rate=1,tax=<code>,text=... "
                             "Put text last if it contains commas.")
    create.add_argument("--lines-file", dest="lines_file",
                        help="JSON file with a list of line objects (same field names as --line)")
    create.add_argument("--limit", type=int, default=500,
                        help="How many recent entries to scan for a duplicate reference-nr")

    edit = s.add_parser(
        "edit",
        help="Change an existing manual entry",
        description="The v3 PUT REPLACES the whole line set: every line is always sent "
                    "back, so an omitted one would be deleted. Without --line the "
                    "existing lines are read and written back unchanged; with --line "
                    "the given lines are the COMPLETE new set.",
    )
    edit.add_argument("id", type=int, help="API id (NOT the Beleg number)")
    edit.add_argument("--date", help="New booking date (YYYY-MM-DD)")
    edit.add_argument("--reference-nr", dest="reference_nr", help="New Beleg number")
    edit.add_argument("--line", action="append", default=[],
                      help="Complete new line set (same fields as create). "
                           "Repeat per line; omitted lines are gone.")
    edit.add_argument("--lines-file", dest="lines_file",
                      help="JSON file with the complete new line set")
    edit.add_argument("--limit", type=int, default=2000,
                      help="How many entries to scan for the id")

    delete = s.add_parser("delete", help="Delete a manual entry")
    delete.add_argument("id", type=int, help="API id (NOT the Beleg number)")
    delete.add_argument("--limit", type=int, default=2000,
                        help="How many entries to scan for the id")

    return p


def handle(args, client, json_flag):
    if args.action == "list":
        _list(args, client, json_flag)
    elif args.action == "show":
        _show(args, client, json_flag)
    elif args.action == "create":
        _create(args, client, json_flag)
    elif args.action == "edit":
        _edit(args, client, json_flag)
    elif args.action == "delete":
        _delete(args, client, json_flag)
    else:
        sys.exit("Usage: bexio manual-entries {list|show|create|edit|delete}")


# ── read ──────────────────────────────────────────────────────────────────────

def _fetch(client, limit):
    resp = client.get_v3(MANUAL_ENTRIES_PATH, params={"limit": limit, "order_by": "id_desc"})
    entries = resp.get("data", resp) if isinstance(resp, dict) else resp
    if not isinstance(entries, list):
        sys.exit(f"Unexpected response: {entries}")
    return entries


def _list(args, client, json_flag):
    entries = _fetch(client, args.limit)
    date_from = getattr(args, "date_from", None)
    date_to = getattr(args, "date_to", None)
    if date_from:
        entries = [e for e in entries if str(e.get("date", ""))[:10] >= date_from]
    if date_to:
        entries = [e for e in entries if str(e.get("date", ""))[:10] <= date_to]
    if json_flag:
        print_json(entries)
        return
    if not entries:
        print("No manual entries found.")
        return
    print(f"{'ID':>6}  {'Date':<12}  {'Beleg':<10}  {'Lines':>5}  {'Total':>12}")
    print("-" * 54)
    for e in entries:
        lines = e.get("entries") or []
        total = sum(float(l.get("base_currency_amount") or 0)
                    for l in lines if l.get("debit_account_id"))
        print(f"{e.get('id', ''):>6}  {str(e.get('date', ''))[:10]:<12}  "
              f"{str(e.get('reference_nr', '')):<10}  {len(lines):>5}  {total:>12.2f}")


def _show(args, client, json_flag):
    entries = _fetch(client, args.limit)
    entry = next((e for e in entries if e.get("id") == args.id), None)
    if entry is None:
        raise ManualEntryError(
            f"Manual entry {args.id} not found in the last {args.limit} entries. "
            f"Raise --limit, or check that {args.id} is the API id and not a Beleg number."
        )
    if json_flag:
        print_json(entry)
        return
    resolver = Resolver(client)
    print(f"ID:      {entry.get('id')}")
    print(f"Date:    {str(entry.get('date', ''))[:10]}")
    print(f"Beleg:   {entry.get('reference_nr') or '—'}")
    print(f"Type:    {entry.get('type', '—')}")
    print()
    print(f"{'Side':<6}  {'Account':<10}  {'Amount':>12}  {'Cur':<4}  {'Rate':>10}  "
          f"{'CHF':>10}  {'Tax':<14}  Text")
    print("-" * 100)
    for line in entry.get("entries") or []:
        debit = line.get("debit_account_id")
        credit = line.get("credit_account_id")
        side = "Soll" if debit else "Haben"
        account = _label_account(resolver, debit or credit)
        tax = _label_tax(resolver, line.get("tax_id"))
        print(f"{side:<6}  {account:<10}  {float(line.get('amount') or 0):>12.2f}  "
              f"{_currency_label(resolver, line.get('currency_id')):<4}  "
              f"{float(line.get('currency_factor') or 1):>10.6f}  "
              f"{float(line.get('base_currency_amount') or 0):>10.2f}  {tax:<14}  "
              f"{line.get('description', '')}")


def _label_account(resolver, account_id):
    if account_id is None:
        return "—"
    number = resolver.account_no(account_id)
    return number if number else f"id {account_id}?"


def _label_tax(resolver, tax_id):
    if tax_id is None:
        return "—"
    code = resolver.tax_code(tax_id)
    return code if code else f"id {tax_id}?"


def _currency_label(resolver, currency_id):
    if currency_id is None:
        return "—"
    name = resolver.currency_name(currency_id)
    return name if name else f"id{currency_id}"


# ── resolution ────────────────────────────────────────────────────────────────

class Resolver:
    """Account number ↔ id, tax code ↔ id, currency code ↔ id. One fetch per kind."""

    def __init__(self, client):
        self._client = client
        self._accounts = None
        self._taxes = None
        self._currencies = None

    # -- accounts

    def _load_accounts(self):
        if self._accounts is None:
            resp = self._client.get("/accounts", params={"limit": 2000})
            self._accounts = resp.get("data", resp) if isinstance(resp, dict) else resp
        return self._accounts

    def account_id(self, account_no: str) -> int:
        wanted = str(account_no).strip()
        for a in self._load_accounts():
            if str(a.get("account_no", "")).strip() == wanted:
                return a["id"]
        numbers = [str(a.get("account_no", "")) for a in self._load_accounts()]
        near = difflib.get_close_matches(wanted, numbers, n=5, cutoff=0.5)
        hint = ", ".join(near) if near else ", ".join(sorted(numbers)[:5])
        raise ManualEntryError(f"Unknown account number {wanted}. Closest matches: {hint}")

    def account_no(self, account_id: int) -> str | None:
        for a in self._load_accounts():
            if a.get("id") == account_id:
                return str(a.get("account_no", "")) or None
        return None

    # -- taxes

    def _load_taxes(self):
        if self._taxes is None:
            resp = self._client.get_v3("/taxes", params={"limit": 500})
            self._taxes = resp.get("data", resp) if isinstance(resp, dict) else resp
        return self._taxes

    def tax_id(self, code: str, *, account_no: str | None = None) -> int:
        wanted = str(code).strip().lower()
        match = next((t for t in self._load_taxes()
                      if str(t.get("code", "")).strip().lower() == wanted), None)
        if match is None:
            active = [str(t.get("code")) for t in self._load_taxes() if t.get("is_active")]
            raise ManualEntryError(
                f"Unknown tax code {code}. Active codes: {', '.join(sorted(active))}")
        if not match.get("is_active"):
            raise ManualEntryError(
                f"Tax code {match.get('code')} is inaktiv (id {match.get('id')}) — "
                f"pick an active code; tax-free must be V00, never omission.")
        if (account_no and is_expense_account(account_no)
                and match.get("type") == "tax_type_sales"):
            raise ManualEntryError(
                f"Tax code {match.get('code')} is a sales tax (Umsatzsteuer) and cannot sit on "
                f"expense account {account_no}. Use a Vorsteuer code, or V00 for tax-free.")
        return match["id"]

    def tax_code(self, tax_id: int) -> str | None:
        for t in self._load_taxes():
            if t.get("id") == tax_id:
                return str(t.get("code", "")) or None
        return None

    # -- currencies

    def _load_currencies(self):
        if self._currencies is None:
            resp = self._client.get_v3("/currencies", params={"limit": 500})
            self._currencies = resp.get("data", resp) if isinstance(resp, dict) else resp
        return self._currencies

    def currency_id(self, code: str) -> int:
        wanted = str(code).strip().lower()
        for c in self._load_currencies():
            if str(c.get("name", "")).strip().lower() == wanted:
                return c["id"]
        known = ", ".join(sorted(str(c.get("name")) for c in self._load_currencies()))
        raise ManualEntryError(f"Unknown currency {code}. Known: {known}")

    def currency_name(self, currency_id: int) -> str | None:
        for c in self._load_currencies():
            if c.get("id") == currency_id:
                return str(c.get("name", "")) or None
        return None


def is_expense_account(account_no: str) -> bool:
    return str(account_no).strip()[:1] in EXPENSE_ACCOUNT_CLASSES


# ── create ────────────────────────────────────────────────────────────────────

def parse_line(spec: str) -> dict:
    """Parse 'debit=1030,amount=119.84,currency=CHF,tax=V00,text=…' into a line dict."""
    raw = {}
    for part in FIELD_SPLIT_RE.split(spec.strip()):
        if not part.strip():
            continue
        if "=" not in part:
            raise ManualEntryError(f"Line field without '=': {part!r} (in {spec!r})")
        key, value = part.split("=", 1)
        key = key.strip()
        if key not in LINE_FIELDS:
            raise ManualEntryError(
                f"Unknown line field {key!r}. Allowed: {', '.join(LINE_FIELDS)}")
        raw[key] = value.strip()
    return normalize_line(raw, source=spec)


def normalize_line(raw: dict, source: str | None = None) -> dict:
    where = f" (in {source!r})" if source else ""
    unknown = set(raw) - set(LINE_FIELDS)
    if unknown:
        raise ManualEntryError(
            f"Unknown line field {', '.join(sorted(unknown))!r}. "
            f"Allowed: {', '.join(LINE_FIELDS)}")
    debit = str(raw.get("debit")).strip() if raw.get("debit") not in (None, "") else None
    credit = str(raw.get("credit")).strip() if raw.get("credit") not in (None, "") else None
    if bool(debit) == bool(credit):
        raise ManualEntryError(
            f"Every line needs exactly one of debit= or credit={where}")
    if raw.get("amount") in (None, ""):
        raise ManualEntryError(f"Line without amount={where}")
    try:
        amount = round(float(raw["amount"]), 2)
    except ValueError:
        raise ManualEntryError(f"Amount {raw['amount']!r} is not a number{where}") from None
    if amount <= 0:
        raise ManualEntryError(
            f"Amount must be > 0 — flip debit/credit instead of a negative amount{where}")
    try:
        rate = float(raw.get("rate") or 1)
    except ValueError:
        raise ManualEntryError(f"Rate {raw.get('rate')!r} is not a number{where}") from None
    if rate <= 0:
        raise ManualEntryError(f"Rate must be > 0{where}")
    return {
        "debit": debit,
        "credit": credit,
        "amount": amount,
        "currency": (str(raw.get("currency") or "CHF")).strip().upper(),
        "rate": rate,
        "tax": (str(raw["tax"]).strip() if raw.get("tax") not in (None, "") else None),
        "text": str(raw.get("text") or "").strip(),
    }


def base_amount(line: dict) -> float:
    return round(line["amount"] * line["rate"], 2)


def check_balance(lines: list[dict]) -> None:
    debit = round(sum(base_amount(l) for l in lines if l["debit"]), 2)
    credit = round(sum(base_amount(l) for l in lines if l["credit"]), 2)
    if round(debit - credit, 2) != 0:
        raise ManualEntryError(
            f"Unbalanced entry: Soll {debit:.2f} vs Haben {credit:.2f}, "
            f"difference {round(debit - credit, 2):.2f} — nothing was sent.")


def build_entry(lines: list[dict], resolver: Resolver, *, date: str,
                reference_nr: str | None = None) -> dict:
    api_lines = []
    for line in lines:
        account_no = line["debit"] or line["credit"]
        account_id = resolver.account_id(account_no)
        api_line = {
            "debit_account_id": account_id if line["debit"] else None,
            "credit_account_id": account_id if line["credit"] else None,
            "amount": line["amount"],
            "currency_id": resolver.currency_id(line["currency"]),
            "currency_factor": line["rate"],
            "base_currency_amount": base_amount(line),
        }
        if line["tax"]:
            api_line["tax_id"] = resolver.tax_id(line["tax"], account_no=account_no)
        api_line["description"] = line["text"]
        api_lines.append(api_line)
    entry = {"type": "manual_compound_entry", "date": date, "entries": api_lines}
    if reference_nr:
        entry["reference_nr"] = str(reference_nr)
    return entry


def _collect_lines(args) -> list[dict]:
    lines = [parse_line(spec) for spec in (getattr(args, "line", None) or [])]
    lines_file = getattr(args, "lines_file", None)
    if lines_file:
        try:
            with open(lines_file, encoding="utf-8") as fh:
                payload = json.load(fh)
        except (OSError, json.JSONDecodeError) as e:
            raise ManualEntryError(f"Cannot read --lines-file {lines_file}: {e}") from None
        if not isinstance(payload, list):
            raise ManualEntryError("--lines-file must contain a JSON list of line objects")
        lines += [normalize_line(item, source=lines_file) for item in payload]
    if not lines:
        raise ManualEntryError("No lines — pass --line at least twice, or --lines-file.")
    return lines


def _create(args, client, json_flag):
    date = getattr(args, "date", None)
    if not date:
        raise ManualEntryError("--date is required (YYYY-MM-DD).")
    if not DATE_RE.match(str(date)):
        raise ManualEntryError(f"Date {date!r} must be YYYY-MM-DD.")
    lines = _collect_lines(args)
    check_balance(lines)

    reference_nr = getattr(args, "reference_nr", None)
    if reference_nr:
        existing = next((e for e in _fetch(client, getattr(args, "limit", 500))
                         if str(e.get("reference_nr", "")) == str(reference_nr)), None)
        if existing:
            raise ManualEntryError(
                f"Beleg {reference_nr} already exists (API id {existing.get('id')}, "
                f"date {str(existing.get('date', ''))[:10]}) — refusing a duplicate booking.")

    resolver = Resolver(client)
    entry = build_entry(lines, resolver, date=date, reference_nr=reference_nr)
    created = client.post_v3(MANUAL_ENTRIES_PATH, body=entry)
    if json_flag:
        print_json(created)
        return
    print(f"Manual entry {created.get('id')} created "
          f"(Beleg {created.get('reference_nr') or '—'}, date {date}, {len(lines)} lines)")
    if not created.get("reference_nr"):
        print("Note: no Beleg number — Bexio does not assign one; pass --reference-nr "
              "if this booking needs a document number.")


# ── edit / delete ─────────────────────────────────────────────────────────────

def _find_entry(client, entry_id, limit):
    entries = _fetch(client, limit)
    entry = next((e for e in entries if e.get("id") == entry_id), None)
    if entry is not None:
        return entry, entries
    by_reference = next((e for e in entries
                         if str(e.get("reference_nr", "")) == str(entry_id)), None)
    if by_reference is not None:
        raise ManualEntryError(
            f"{entry_id} is a Beleg number, not an API id — Beleg {entry_id} belongs to "
            f"API id {by_reference.get('id')}. Re-run with {by_reference.get('id')}.")
    raise ManualEntryError(
        f"Manual entry {entry_id} not found in the last {limit} entries. "
        f"Raise --limit, or check that {entry_id} is the API id.")


API_LINE_FIELDS = ("debit_account_id", "credit_account_id", "amount", "currency_id",
                   "currency_factor", "base_currency_amount", "tax_id", "description")


def strip_line(line: dict) -> dict:
    """Keep only what the API accepts back — id/date/audit fields are read-only."""
    kept = {k: line.get(k) for k in API_LINE_FIELDS if k in line}
    if kept.get("tax_id") is None:
        kept.pop("tax_id", None)
    return kept


def _edit(args, client, json_flag):
    date = getattr(args, "date", None)
    if date and not DATE_RE.match(str(date)):
        raise ManualEntryError(f"Date {date!r} must be YYYY-MM-DD.")
    reference_nr = getattr(args, "reference_nr", None)
    has_new_lines = bool(getattr(args, "line", None) or getattr(args, "lines_file", None))
    if not (date or reference_nr or has_new_lines):
        raise ManualEntryError(
            "Nothing to change — pass --date, --reference-nr, --line or --lines-file.")

    entry, _ = _find_entry(client, args.id, getattr(args, "limit", 2000))

    if has_new_lines:
        lines = _collect_lines(args)
        check_balance(lines)
        api_lines = build_entry(lines, Resolver(client), date=date or "")["entries"]
    else:
        api_lines = [strip_line(l) for l in (entry.get("entries") or [])]
        debit = round(sum(float(l.get("base_currency_amount") or 0)
                          for l in api_lines if l.get("debit_account_id")), 2)
        credit = round(sum(float(l.get("base_currency_amount") or 0)
                           for l in api_lines if l.get("credit_account_id")), 2)
        if round(debit - credit, 2) != 0:
            raise ManualEntryError(
                f"Stored entry {args.id} is unbalanced (Soll {debit:.2f} vs Haben "
                f"{credit:.2f}) — refusing to write it back.")

    body = {
        "type": entry.get("type", "manual_compound_entry"),
        "date": date or str(entry.get("date", ""))[:10],
        "entries": api_lines,
    }
    new_reference = reference_nr if reference_nr is not None else entry.get("reference_nr")
    if new_reference:
        body["reference_nr"] = str(new_reference)

    updated = client.put_v3(f"{MANUAL_ENTRIES_PATH}/{args.id}", body=body)
    if json_flag:
        print_json(updated)
        return
    print(f"Manual entry {args.id} updated ({len(api_lines)} lines written back)")


def _delete(args, client, json_flag):
    entry, _ = _find_entry(client, args.id, getattr(args, "limit", 2000))
    client.delete_v3(f"{MANUAL_ENTRIES_PATH}/{args.id}")
    if json_flag:
        print_json({"deleted": args.id})
        return
    print(f"Manual entry {args.id} deleted "
          f"(Beleg {entry.get('reference_nr') or '—'}, date {str(entry.get('date', ''))[:10]}, "
          f"{len(entry.get('entries') or [])} lines)")

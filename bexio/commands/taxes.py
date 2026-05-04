"""Taxes and VAT period commands."""

import sys
from bexio.output import print_json


# ── taxes ─────────────────────────────────────────────────────────────────────

def register_taxes(sub):
    p = sub.add_parser("taxes", help="Tax rate commands")
    s = p.add_subparsers(dest="action")

    ls = s.add_parser("list", help="List tax rates")
    ls.add_argument("--limit", type=int, default=100)

    show = s.add_parser("show", help="Show a tax rate")
    show.add_argument("id", type=int)

    return p


def handle_taxes(args, client, json_flag):
    if args.action == "list":
        _taxes_list(args, client, json_flag)
    elif args.action == "show":
        _taxes_show(args, client, json_flag)
    else:
        sys.exit("Usage: bexio taxes {list|show}")


def _taxes_list(args, client, json_flag):
    resp = client.get_v3("/taxes", params={"limit": args.limit})
    taxes = resp.get("data", resp) if isinstance(resp, dict) else resp
    if json_flag:
        print_json(taxes)
        return
    if not taxes:
        print("No taxes found.")
        return
    print(f"{'ID':>5}  {'Code':<20}  {'Name':<30}  {'Value%':>8}  Active")
    print("-" * 75)
    for t in taxes:
        active = "Yes" if t.get("is_active") else "No"
        print(f"{t['id']:>5}  {str(t.get('code', '')):<20}  {str(t.get('name', '')):<30}  {str(t.get('value', '')) + '%':>8}  {active}")


def _taxes_show(args, client, json_flag):
    t = client.get_v3(f"/taxes/{args.id}")
    if json_flag:
        print_json(t)
        return
    active = "Yes" if t.get("is_active") else "No"
    print(f"ID:           {t['id']}")
    print(f"Name:         {t.get('name', '—')}")
    print(f"Code:         {t.get('code', '—')}")
    print(f"Value:        {t.get('value', '—')}%")
    print(f"Active:       {active}")
    print(f"Display name: {t.get('display_name', '—')}")


# ── vat-periods ───────────────────────────────────────────────────────────────

def register_vat_periods(sub):
    p = sub.add_parser("vat-periods", help="VAT period commands")
    s = p.add_subparsers(dest="action")

    s.add_parser("list", help="List VAT periods")

    show = s.add_parser("show", help="Show a VAT period")
    show.add_argument("id", type=int)

    return p


def handle_vat_periods(args, client, json_flag):
    if args.action == "list":
        _vat_periods_list(args, client, json_flag)
    elif args.action == "show":
        _vat_periods_show(args, client, json_flag)
    else:
        sys.exit("Usage: bexio vat-periods {list|show}")


def _vat_periods_list(args, client, json_flag):
    resp = client.get_v3("/accounting/vat_periods")
    periods = resp.get("data", resp) if isinstance(resp, dict) else resp
    if json_flag:
        print_json(periods)
        return
    if not periods:
        print("No VAT periods found.")
        return
    print(f"{'ID':>5}  {'Start':<12}  {'End':<12}  {'Type':<12}  Status")
    print("-" * 60)
    for p in periods:
        print(f"{p['id']:>5}  {str(p.get('start', '')):<12}  {str(p.get('end', '')):<12}  {str(p.get('type', '')):<12}  {p.get('status', '')}")


def _vat_periods_show(args, client, json_flag):
    p = client.get_v3(f"/accounting/vat_periods/{args.id}")
    if json_flag:
        print_json(p)
        return
    print(f"ID:        {p['id']}")
    print(f"Start:     {p.get('start', '—')}")
    print(f"End:       {p.get('end', '—')}")
    print(f"Type:      {p.get('type', '—')}")
    print(f"Status:    {p.get('status', '—')}")
    print(f"Closed at: {p.get('closed_at') or '—'}")

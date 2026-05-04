"""Account and account-group commands."""

import sys
from bexio.output import print_json


def register(sub):
    # accounts
    p = sub.add_parser("accounts", help="Account commands")
    s = p.add_subparsers(dest="action")

    ls = s.add_parser("list", help="List accounts")
    ls.add_argument("--limit", type=int, default=200)
    ls.add_argument("--active", action="store_true", help="Show only active accounts")

    show = s.add_parser("show", help="Show account")
    show.add_argument("id", type=int)

    search = s.add_parser("search", help="Search accounts by name")
    search.add_argument("query", type=str)

    return p


def register_groups(sub):
    # account-groups
    p = sub.add_parser("account-groups", help="Account group commands")
    s = p.add_subparsers(dest="action")
    s.add_parser("list", help="List account groups")
    return p


def handle(args, client, json_flag):
    if args.action == "list":
        _list(args, client, json_flag)
    elif args.action == "show":
        _show(args, client, json_flag)
    elif args.action == "search":
        _search(args, client, json_flag)
    else:
        sys.exit("Usage: bexio accounts {list|show|search}")


def handle_groups(args, client, json_flag):
    if args.action == "list":
        _list_groups(args, client, json_flag)
    else:
        sys.exit("Usage: bexio account-groups {list}")


def _list(args, client, json_flag):
    accounts = client.get("/accounts", params={"limit": args.limit})
    if not isinstance(accounts, list):
        sys.exit(f"Unexpected response: {accounts}")
    if getattr(args, "active", False):
        accounts = [a for a in accounts if a.get("is_active")]
    if json_flag:
        print_json(accounts)
        return
    for a in accounts:
        active = "yes" if a.get("is_active") else "no"
        print(f"{a['id']:>5}  {str(a.get('account_no', '')):>8}  {a.get('name', ''):<40}  {a.get('account_type', ''):>4}  {active}")


def _show(args, client, json_flag):
    a = client.get(f"/accounts/{args.id}")
    if json_flag:
        print_json(a)
        return
    active = "yes" if a.get("is_active") else "no"
    print(f"ID:          {a['id']}")
    print(f"Account No:  {a.get('account_no', '—')}")
    print(f"Name:        {a.get('name', '—')}")
    print(f"Type:        {a.get('account_type', '—')}")
    print(f"Active:      {active}")
    print(f"Tax ID:      {a.get('tax_id', '—')}")


def _search(args, client, json_flag):
    results = client.post("/accounts/search", body=[
        {"field": "name", "value": args.query, "criteria": "like"}
    ])
    if not isinstance(results, list):
        sys.exit(f"Unexpected response: {results}")
    if json_flag:
        print_json(results)
        return
    if not results:
        print("No accounts found.")
        return
    for a in results:
        active = "yes" if a.get("is_active") else "no"
        print(f"{a['id']:>5}  {str(a.get('account_no', '')):>8}  {a.get('name', ''):<40}  {active}")


def _list_groups(args, client, json_flag):
    groups = client.get("/account_groups")
    if not isinstance(groups, list):
        sys.exit(f"Unexpected response: {groups}")
    if json_flag:
        print_json(groups)
        return
    for g in groups:
        active = "yes" if g.get("is_active") else "no"
        print(f"{g['id']:>5}  {str(g.get('account_no', '')):>8}  {g.get('name', ''):<40}  {active}")

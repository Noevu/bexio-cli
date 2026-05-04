"""Payment type commands."""

import sys
from bexio.output import print_json


def register(sub):
    p = sub.add_parser("payment-types", help="Payment type commands")
    s = p.add_subparsers(dest="action")

    s.add_parser("list", help="List payment types")

    show = s.add_parser("show", help="Show payment type")
    show.add_argument("id", type=int)

    return p


def handle(args, client, json_flag):
    if args.action == "list":
        _list(args, client, json_flag)
    elif args.action == "show":
        _show(args, client, json_flag)
    else:
        sys.exit("Usage: bexio payment-types {list|show}")


def _list(args, client, json_flag):
    items = client.get("/payment_type")
    if not isinstance(items, list):
        sys.exit(f"Unexpected response: {items}")
    if json_flag:
        print_json(items)
        return
    for pt in items:
        print(f"{pt['id']:>5}  {pt.get('name', '')}")


def _show(args, client, json_flag):
    pt = client.get(f"/payment_type/{args.id}")
    if json_flag:
        print_json(pt)
        return
    print(f"ID:    {pt['id']}")
    print(f"Name:  {pt.get('name', '—')}")

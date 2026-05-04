"""Currency commands."""

import sys
from bexio.output import print_json


def register(sub):
    p = sub.add_parser("currencies", help="Currency commands")
    s = p.add_subparsers(dest="action")

    s.add_parser("list", help="List currencies")

    show = s.add_parser("show", help="Show a currency")
    show.add_argument("id", type=int)

    s.add_parser("exchange-rates", help="Show current exchange rates")

    return p


def handle(args, client, json_flag):
    if args.action == "list":
        _list(args, client, json_flag)
    elif args.action == "show":
        _show(args, client, json_flag)
    elif args.action == "exchange-rates":
        _exchange_rates(args, client, json_flag)
    else:
        sys.exit("Usage: bexio currencies {list|show|exchange-rates}")


def _list(args, client, json_flag):
    currencies = client.get_v3("/currencies")
    if not isinstance(currencies, list):
        sys.exit(f"Unexpected response: {currencies}")
    if json_flag:
        print_json(currencies)
        return
    if not currencies:
        return
    print(f"{'ID':>4}  {'Name':<8}  Round Factor")
    print("-" * 28)
    for c in currencies:
        print(f"{c['id']:>4}  {str(c.get('name', '')):<8}  {c.get('round_factor', '')}")


def _show(args, client, json_flag):
    c = client.get_v3(f"/currencies/{args.id}")
    if json_flag:
        print_json(c)
        return
    print(f"ID:           {c['id']}")
    print(f"Name:         {c.get('name', '—')}")
    print(f"Round Factor: {c.get('round_factor', '—')}")


def _exchange_rates(args, client, json_flag):
    data = client.get_v3("/currencies/exchange-rates")
    if json_flag:
        print_json(data)
        return
    print_json(data)

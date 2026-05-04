"""Countries commands."""

import sys
from bexio.output import print_json


def register(sub):
    p = sub.add_parser("countries", help="Country reference data")
    s = p.add_subparsers(dest="action")

    ls = s.add_parser("list", help="List countries")
    ls.add_argument("--limit", type=int, default=200)

    show = s.add_parser("show", help="Show country")
    show.add_argument("id", type=int)

    search = s.add_parser("search", help="Search countries by name")
    search.add_argument("query", type=str)

    return p


def handle(args, client, json_flag):
    if args.action == "list":
        _list(args, client, json_flag)
    elif args.action == "show":
        _show(args, client, json_flag)
    elif args.action == "search":
        _search(args, client, json_flag)
    else:
        sys.exit("Usage: bexio countries {list|show|search}")


def _list(args, client, json_flag):
    countries = client.get("/country", params={"limit": args.limit})
    if not isinstance(countries, list):
        sys.exit(f"Unexpected response: {countries}")
    if json_flag:
        print_json(countries)
        return
    for c in countries:
        print(f"{c['id']:>5}  {c.get('iso3166_alpha2', ''):<4}  {c.get('name', '')}")


def _show(args, client, json_flag):
    c = client.get(f"/country/{args.id}")
    if json_flag:
        print_json(c)
        return
    print(f"ID:        {c['id']}")
    print(f"Name:      {c.get('name', '—')}")
    print(f"Short:     {c.get('name_short', '—')}")
    print(f"ISO 3166:  {c.get('iso3166_alpha2', '—')}")


def _search(args, client, json_flag):
    results = client.post("/country/search", body=[
        {"field": "name", "value": args.query, "criteria": "like"}
    ])
    if not isinstance(results, list):
        sys.exit(f"Unexpected response: {results}")
    if json_flag:
        print_json(results)
        return
    if not results:
        print("No countries found.")
        return
    for c in results:
        print(f"{c['id']:>5}  {c.get('iso3166_alpha2', ''):<4}  {c.get('name', '')}")

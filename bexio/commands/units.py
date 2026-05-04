"""Unit commands."""

import sys
from bexio.output import print_json


def register(sub):
    p = sub.add_parser("units", help="Unit commands")
    s = p.add_subparsers(dest="action")

    s.add_parser("list", help="List units")

    show = s.add_parser("show", help="Show unit")
    show.add_argument("id", type=int)

    create = s.add_parser("create", help="Create a unit")
    create.add_argument("--name", required=True, help="Unit name")

    delete = s.add_parser("delete", help="Delete a unit")
    delete.add_argument("id", type=int)

    return p


def handle(args, client, json_flag):
    if args.action == "list":
        _list(args, client, json_flag)
    elif args.action == "show":
        _show(args, client, json_flag)
    elif args.action == "create":
        _create(args, client, json_flag)
    elif args.action == "delete":
        _delete(args, client, json_flag)
    else:
        sys.exit("Usage: bexio units {list|show|create|delete}")


def _list(args, client, json_flag):
    units = client.get("/unit")
    if not isinstance(units, list):
        sys.exit(f"Unexpected response: {units}")
    if json_flag:
        print_json(units)
        return
    for u in units:
        print(f"{u['id']:>5}  {u['name']}")


def _show(args, client, json_flag):
    u = client.get(f"/unit/{args.id}")
    if json_flag:
        print_json(u)
        return
    print(f"ID:    {u['id']}")
    print(f"Name:  {u['name']}")


def _create(args, client, json_flag):
    result = client.post("/unit", body={"name": args.name})
    if json_flag:
        print_json(result)
        return
    print(f"Unit #{result.get('id')} created: {result.get('name')}")


def _delete(args, client, json_flag):
    client.delete(f"/unit/{args.id}")
    print(f"Unit #{args.id} deleted")

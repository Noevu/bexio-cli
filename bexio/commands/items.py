"""Items/products commands — Bexio article endpoint (/article)."""

import sys
from bexio.output import print_json


def register(sub):
    p = sub.add_parser("items", help="Item/product (article) commands")
    s = p.add_subparsers(dest="action")

    ls = s.add_parser("list", help="List items")
    ls.add_argument("--limit", type=int, default=100)

    show = s.add_parser("show", help="Show item detail")
    show.add_argument("id", type=int)

    search = s.add_parser("search", help="Search items by name")
    search.add_argument("query")

    create = s.add_parser("create", help="Create an item")
    create.add_argument("--name", required=True, help="Item name (intern_name)")
    create.add_argument("--unit-price", dest="unit_price", default=None,
                        help="Purchase price (purchase_price)")
    create.add_argument("--sale-price", dest="sale_price", default=None)
    create.add_argument("--unit-id", dest="unit_id", type=int, default=None)
    create.add_argument("--purchase-price", dest="purchase_price", default=None)

    edit = s.add_parser("edit", help="Edit an item")
    edit.add_argument("id", type=int)
    edit.add_argument("--name", dest="name", default=None)
    edit.add_argument("--unit-price", dest="unit_price", default=None,
                      help="Maps to purchase_price")
    edit.add_argument("--sale-price", dest="sale_price", default=None)

    delete = s.add_parser("delete", help="Delete an item")
    delete.add_argument("id", type=int)

    return p


def handle(args, client, json_flag):
    if args.action == "list":
        _list(args, client, json_flag)
    elif args.action == "show":
        _show(args, client, json_flag)
    elif args.action == "search":
        _search(args, client, json_flag)
    elif args.action == "create":
        _create(args, client, json_flag)
    elif args.action == "edit":
        _edit(args, client, json_flag)
    elif args.action == "delete":
        _delete(args, client, json_flag)
    else:
        sys.exit("Usage: bexio items {list|show|search|create|edit|delete}")


def _print_table(items):
    for item in items:
        iid = item.get("id", "")
        name = (item.get("intern_name") or "")[:40]
        sale = item.get("sale_price", "")
        purchase = item.get("purchase_price", "")
        uid = item.get("unit_id", "")
        print(f"{iid:>5}  {name:<40}  purchase={purchase:<10}  sale={sale:<10}  unit={uid}")


def _list(args, client, json_flag):
    items = client.get("/article", params={"limit": args.limit})
    if not isinstance(items, list):
        sys.exit(f"Unexpected response: {items}")
    if json_flag:
        print_json(items)
        return
    _print_table(items)


def _show(args, client, json_flag):
    item = client.get(f"/article/{args.id}")
    if json_flag:
        print_json(item)
        return
    print(f"ID:             {item.get('id')}")
    print(f"Name:           {item.get('intern_name')}")
    print(f"Code:           {item.get('intern_code')}")
    print(f"Purchase price: {item.get('purchase_price')}")
    print(f"Sale price:     {item.get('sale_price')}")
    print(f"Unit ID:        {item.get('unit_id')}")


def _search(args, client, json_flag):
    body = [{"field": "intern_name", "value": args.query, "criteria": "like"}]
    items = client.post("/article/search", body=body)
    if not isinstance(items, list):
        sys.exit(f"Unexpected response: {items}")
    if json_flag:
        print_json(items)
        return
    if not items:
        print("No items found.")
        return
    _print_table(items)


def _create(args, client, json_flag):
    body = {"intern_name": args.name}
    if args.unit_price is not None:
        body["purchase_price"] = args.unit_price
    if args.sale_price is not None:
        body["sale_price"] = args.sale_price
    if args.unit_id is not None:
        body["unit_id"] = args.unit_id
    if getattr(args, "purchase_price", None) is not None:
        body["purchase_price"] = args.purchase_price
    result = client.post("/article", body=body)
    if json_flag:
        print_json(result)
        return
    print(f"Item {result.get('id')} created")


def _edit(args, client, json_flag):
    body = {}
    if args.name is not None:
        body["intern_name"] = args.name
    if args.unit_price is not None:
        body["purchase_price"] = args.unit_price
    if args.sale_price is not None:
        body["sale_price"] = args.sale_price
    if not body:
        sys.exit("No fields to update. Provide at least --name, --unit-price, or --sale-price.")
    result = client.put(f"/article/{args.id}", body=body)
    if json_flag:
        print_json(result)
        return
    print(f"Item {args.id} updated")


def _delete(args, client, json_flag):
    client.delete(f"/article/{args.id}")
    print(f"Item {args.id} deleted")

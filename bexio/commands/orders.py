"""Order commands."""

import sys
from bexio.output import print_json, table

KB_ITEM_STATUS = {1: "Draft", 4: "Pending", 5: "Active", 6: "Cancelled"}


def register(sub):
    p = sub.add_parser("orders", help="Order (Auftrag) commands")
    s = p.add_subparsers(dest="action")

    ls = s.add_parser("list", help="List orders")
    ls.add_argument("--recurring", action="store_true", help="Only recurring orders")
    ls.add_argument("--limit", type=int, default=100)

    show = s.add_parser("show", help="Show order + repetition")
    show.add_argument("id", type=int)

    create_inv = s.add_parser("create-invoice", help="Create invoice from order")
    create_inv.add_argument("id", type=int, help="Order ID")

    search = s.add_parser("search", help="Search orders by name")
    search.add_argument("query", type=str)

    delete = s.add_parser("delete", help="Delete order")
    delete.add_argument("id", type=int)

    pdf = s.add_parser("pdf", help="Download order PDF")
    pdf.add_argument("id", type=int)
    pdf.add_argument("--output", "-o", help="Output filename")

    return p


def handle(args, client, json_flag):
    if args.action == "list":
        _list(args, client, json_flag)
    elif args.action == "show":
        _show(args, client, json_flag)
    elif args.action == "create-invoice":
        _create_invoice(args, client, json_flag)
    elif args.action == "search":
        _search(args, client, json_flag)
    elif args.action == "delete":
        _delete(args, client, json_flag)
    elif args.action == "pdf":
        _pdf(args, client, json_flag)
    else:
        sys.exit("Usage: bexio orders {list|show|create-invoice|search|delete|pdf}")


def _list(args, client, json_flag):
    params = {"limit": args.limit}
    if args.recurring:
        params["is_recurring"] = "true"
    orders = client.get("/kb_order", params=params)
    if not isinstance(orders, list):
        sys.exit(f"Unexpected response: {orders}")
    if json_flag:
        print_json(orders)
        return
    for o in orders:
        status = KB_ITEM_STATUS.get(o.get("kb_item_status_id"), "")
        rec = " [recurring]" if o.get("is_recurring") else ""
        print(f"{o['id']:>4}  {o['document_nr']:<20}  {o['title'][:48]:<48}  {status}{rec}")


def _show(args, client, json_flag):
    order = client.get(f"/kb_order/{args.id}")
    rep = client.get(f"/kb_order/{args.id}/repetition")
    if json_flag:
        print_json({"order": order, "repetition": rep})
        return
    print(f"ID:         {order['id']}")
    print(f"Nr:         {order['document_nr']}")
    print(f"Title:      {order['title']}")
    print(f"Recurring:  {order.get('is_recurring', False)}")
    print(f"Total:      CHF {float(order['total']):.2f}")
    if isinstance(rep, dict) and "repetition" in rep:
        r = rep["repetition"]
        print(f"Repetition: {r.get('type')} every {r.get('interval')} — starts {rep.get('start')}")


def _create_invoice(args, client, json_flag):
    result = client.post(f"/kb_order/{args.id}/create_invoice")
    if json_flag:
        print_json(result)
        return
    inv_id = result.get("id")
    print(f"Invoice #{inv_id} ({result.get('document_nr', '—')}) created")
    print(f"  https://office.bexio.com/index.php/kb_invoice/show/id/{inv_id}")


def _search(args, client, json_flag):
    results = client.post("/kb_order/search", body=[
        {"field": "name", "value": args.query, "criteria": "like"}
    ])
    if not isinstance(results, list):
        sys.exit(f"Unexpected response: {results}")
    if json_flag:
        print_json(results)
        return
    if not results:
        print("No orders found.")
        return
    for o in results:
        status = KB_ITEM_STATUS.get(o.get("kb_item_status_id"), "")
        rec = " [recurring]" if o.get("is_recurring") else ""
        print(f"{o['id']:>4}  {o['document_nr']:<20}  {o['title'][:48]:<48}  {status}{rec}")


def _delete(args, client, json_flag):
    client.delete(f"/kb_order/{args.id}")
    print(f"Order {args.id} deleted.")


def _pdf(args, client, json_flag):
    data = client.get_pdf(f"/kb_order/{args.id}/pdf")
    filename = args.output or f"order_{args.id}.pdf"
    with open(filename, "wb") as f:
        f.write(data)
    print(f"Saved to {filename}")

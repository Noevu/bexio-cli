"""Order commands."""

import json
import sys
from bexio.models import KbOrder, OrderRepetition
from bexio.output import print_json, table

KB_ITEM_STATUS = {1: "Draft", 4: "Pending", 5: "Active", 6: "Cancelled"}

REPETITION_TYPES = ("daily", "weekly", "monthly", "yearly")
MONTHLY_SCHEDULES = ("fixed_day", "week_day", "first_day", "last_day")


def register(sub):
    p = sub.add_parser("orders", help="Order (Auftrag) commands")
    s = p.add_subparsers(dest="action")

    ls = s.add_parser("list", help="List orders")
    ls.add_argument("--recurring", action="store_true", help="Only recurring orders")
    ls.add_argument("--limit", type=int, default=100)

    show = s.add_parser("show", help="Show order + repetition")
    show.add_argument("id", type=int)

    create = s.add_parser("create", help="Create an order from a JSON body")
    create.add_argument("--file", "-f", required=True,
                        help="Path to JSON body file, or '-' to read stdin")

    create_inv = s.add_parser("create-invoice", help="Create invoice from order")
    create_inv.add_argument("id", type=int, help="Order ID")

    unset_rep = s.add_parser("unset-repetition",
                             help="Remove recurrence from an order (required before delete)")
    unset_rep.add_argument("id", type=int, help="Order ID")

    set_rep = s.add_parser("set-repetition", help="Set recurrence on an order")
    set_rep.add_argument("id", type=int, help="Order ID")
    set_rep.add_argument("--file", "-f",
                         help="JSON body file (or '-' for stdin). If set, overrides flags.")
    set_rep.add_argument("--start", help="Start date (YYYY-MM-DD)")
    set_rep.add_argument("--end", default=None, help="End date (YYYY-MM-DD); omit for indefinite")
    set_rep.add_argument("--type", dest="rep_type", choices=REPETITION_TYPES,
                         help="Recurrence type")
    set_rep.add_argument("--interval", type=int, default=1, help="Repetition interval (default 1)")
    set_rep.add_argument("--schedule", choices=MONTHLY_SCHEDULES,
                         help="Monthly only: when in the month to repeat")
    set_rep.add_argument("--weekdays",
                         help="Weekly only: comma-separated weekday names (monday,…,sunday)")

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
    elif args.action == "create":
        _create(args, client, json_flag)
    elif args.action == "create-invoice":
        _create_invoice(args, client, json_flag)
    elif args.action == "set-repetition":
        _set_repetition(args, client, json_flag)
    elif args.action == "unset-repetition":
        _unset_repetition(args, client, json_flag)
    elif args.action == "search":
        _search(args, client, json_flag)
    elif args.action == "delete":
        _delete(args, client, json_flag)
    elif args.action == "pdf":
        _pdf(args, client, json_flag)
    else:
        sys.exit("Usage: bexio orders {list|show|create|create-invoice|set-repetition|unset-repetition|search|delete|pdf}")


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


def _read_body(path: str) -> dict:
    if path == "-":
        raw = sys.stdin.read()
    else:
        with open(path, "r") as f:
            raw = f.read()
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        sys.exit(f"Invalid JSON in {path}: {e}")


def _format_validation_errors(exc) -> str:
    lines = []
    for err in exc.errors():
        loc = ".".join(str(p) for p in err["loc"])
        lines.append(f"  {loc}: {err['msg']}")
    return "\n".join(lines)


def _create(args, client, json_flag):
    body = _read_body(args.file)
    try:
        order = KbOrder.model_validate(body)
    except Exception as e:
        sys.exit(f"Invalid order body:\n{_format_validation_errors(e)}")
    payload = order.model_dump(mode="json", exclude_none=True)
    result = client.post("/kb_order", body=payload)
    if json_flag:
        print_json(result)
        return
    oid = result.get("id")
    print(f"Order #{oid} ({result.get('document_nr', '—')}) created — {result.get('title', '')}")
    print(f"  https://office.bexio.com/index.php/kb_order/show/id/{oid}")


def _set_repetition(args, client, json_flag):
    if args.file:
        body = _read_body(args.file)
    else:
        if not args.start or not args.rep_type:
            sys.exit("set-repetition requires --file OR --start + --type")
        rep: dict = {"type": args.rep_type, "interval": args.interval}
        if args.rep_type == "monthly":
            if not args.schedule:
                sys.exit("--schedule is required for type=monthly (one of: " + ", ".join(MONTHLY_SCHEDULES) + ")")
            rep["schedule"] = args.schedule
        if args.rep_type == "weekly":
            if not args.weekdays:
                sys.exit("--weekdays is required for type=weekly (e.g. monday,wednesday)")
            rep["weekdays"] = [d.strip().lower() for d in args.weekdays.split(",") if d.strip()]
        body = {"start": args.start, "end": args.end, "repetition": rep}

    try:
        spec = OrderRepetition.model_validate(body)
    except Exception as e:
        sys.exit(f"Invalid repetition body:\n{_format_validation_errors(e)}")
    payload = spec.model_dump(mode="json")
    result = client.post(f"/kb_order/{args.id}/repetition", body=payload)
    if json_flag:
        print_json(result)
        return
    r = result.get("repetition", {}) if isinstance(result, dict) else {}
    print(f"Order {args.id} recurrence set: {r.get('type')} every {r.get('interval')} — starts {result.get('start')}")
    if args.end:
        print(f"  ends {args.end}")


def _unset_repetition(args, client, json_flag):
    result = client.delete(f"/kb_order/{args.id}/repetition")
    if json_flag:
        print_json(result)
        return
    print(f"Order {args.id} recurrence removed.")


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

"""Invoice commands."""

import sys
from bexio.output import print_json

STATUS_MAP = {"draft": 1, "open": 7, "partial": 8, "paid": 9, "cancelled": 16}
STATUS_LABELS = {v: k.title() for k, v in STATUS_MAP.items()}


def register(sub):
    p = sub.add_parser("invoices", help="Invoice commands")
    s = p.add_subparsers(dest="action")

    ls = s.add_parser("list", help="List invoices")
    ls.add_argument("--status", choices=list(STATUS_MAP))
    ls.add_argument("--limit", type=int, default=100)

    show = s.add_parser("show", help="Show invoice")
    show.add_argument("id", type=int)

    send = s.add_parser("send", help="Send invoice by email")
    send.add_argument("id", type=int)

    mark = s.add_parser("mark-sent", help="Mark sent (no email)")
    mark.add_argument("id", type=int)

    cancel = s.add_parser("cancel", help="Cancel invoice")
    cancel.add_argument("id", type=int)

    issue = s.add_parser("issue", help="Issue (finalize) invoice")
    issue.add_argument("id", type=int)

    search = s.add_parser("search", help="Search invoices by title")
    search.add_argument("query", type=str)

    delete = s.add_parser("delete", help="Delete invoice")
    delete.add_argument("id", type=int)

    copy = s.add_parser("copy", help="Copy invoice")
    copy.add_argument("id", type=int)

    pdf = s.add_parser("pdf", help="Download invoice PDF")
    pdf.add_argument("id", type=int)
    pdf.add_argument("--output", "-o", help="Output filename")

    revert_issue = s.add_parser("revert-issue", help="Revert invoice to draft")
    revert_issue.add_argument("id", type=int)

    return p


def handle(args, client, json_flag):
    if args.action == "list":
        _list(args, client, json_flag)
    elif args.action == "show":
        _show(args, client, json_flag)
    elif args.action == "send":
        _action(args, client, json_flag, f"/kb_invoice/{args.id}/send", "sent")
    elif args.action == "mark-sent":
        _action(args, client, json_flag, f"/kb_invoice/{args.id}/mark_as_sent", "marked as sent")
    elif args.action == "cancel":
        _action(args, client, json_flag, f"/kb_invoice/{args.id}/cancel", "cancelled")
    elif args.action == "issue":
        _action(args, client, json_flag, f"/kb_invoice/{args.id}/issue", "issued")
    elif args.action == "search":
        _search(args, client, json_flag)
    elif args.action == "delete":
        _delete(args, client, json_flag)
    elif args.action == "copy":
        _copy(args, client, json_flag)
    elif args.action == "pdf":
        _pdf(args, client, json_flag)
    elif args.action == "revert-issue":
        _revert_issue(args, client, json_flag)
    else:
        sys.exit("Usage: bexio invoices {list|show|send|mark-sent|cancel|issue|search|delete|copy|pdf|revert-issue}")


def _list(args, client, json_flag):
    params = {"limit": args.limit}
    if args.status:
        params["kb_item_status_id"] = STATUS_MAP[args.status]
    invoices = client.get("/kb_invoice", params=params)
    if not isinstance(invoices, list):
        sys.exit(f"Unexpected response: {invoices}")
    if json_flag:
        print_json(invoices)
        return
    for inv in invoices:
        status = STATUS_LABELS.get(inv.get("kb_item_status_id"), str(inv.get("kb_item_status_id")))
        total = f"CHF {float(inv.get('total', 0)):.2f}"
        date = (inv.get("is_valid_from") or "")[:10]
        title = (inv.get("title") or "")[:36]
        print(f"{inv['id']:>5}  {inv['document_nr']:<18}  {date:<10}  {total:>11}  {status:<10}  {title}")


def _show(args, client, json_flag):
    inv = client.get(f"/kb_invoice/{args.id}")
    if json_flag:
        print_json(inv)
        return
    status = STATUS_LABELS.get(inv.get("kb_item_status_id"), str(inv.get("kb_item_status_id")))
    print(f"ID:      {inv['id']}")
    print(f"Nr:      {inv['document_nr']}")
    print(f"Title:   {inv.get('title', '—')}")
    print(f"Date:    {inv.get('is_valid_from', '—')}")
    print(f"Due:     {inv.get('is_valid_to', '—')}")
    print(f"Total:   CHF {float(inv.get('total', 0)):.2f}")
    print(f"Status:  {status}")
    print(f"URL:     https://office.bexio.com/index.php/kb_invoice/show/id/{inv['id']}")


def _action(args, client, json_flag, path, verb):
    result = client.post(path)
    if json_flag:
        print_json(result)
        return
    print(f"Invoice {args.id} {verb}.")


def _search(args, client, json_flag):
    results = client.post("/kb_invoice/search", body=[
        {"field": "title", "value": args.query, "criteria": "like"}
    ])
    if not isinstance(results, list):
        sys.exit(f"Unexpected response: {results}")
    if json_flag:
        print_json(results)
        return
    if not results:
        print("No invoices found.")
        return
    for inv in results:
        status = STATUS_LABELS.get(inv.get("kb_item_status_id"), str(inv.get("kb_item_status_id")))
        total = f"CHF {float(inv.get('total', 0)):.2f}"
        date = (inv.get("is_valid_from") or "")[:10]
        title = (inv.get("title") or "")[:36]
        print(f"{inv['id']:>5}  {inv['document_nr']:<18}  {date:<10}  {total:>11}  {status:<10}  {title}")


def _delete(args, client, json_flag):
    client.delete(f"/kb_invoice/{args.id}")
    print(f"Invoice {args.id} deleted.")


def _copy(args, client, json_flag):
    result = client.post(f"/kb_invoice/{args.id}/copy")
    if json_flag:
        print_json(result)
        return
    print(f"Invoice {result['id']} created.")


def _pdf(args, client, json_flag):
    data = client.get_pdf(f"/kb_invoice/{args.id}/pdf")
    filename = args.output or f"invoice_{args.id}.pdf"
    with open(filename, "wb") as f:
        f.write(data)
    print(f"Saved to {filename}")


def _revert_issue(args, client, json_flag):
    client.post(f"/kb_invoice/{args.id}/revert_issue")
    print(f"Invoice {args.id} reverted to draft.")

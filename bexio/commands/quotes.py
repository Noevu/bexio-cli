"""Quote commands."""

import sys
from bexio.output import print_json

STATUS_MAP = {"draft": 1, "sent": 3, "accepted": 8, "declined": 9}
STATUS_LABELS = {v: k.title() for k, v in STATUS_MAP.items()}


def register(sub):
    p = sub.add_parser("quotes", help="Quote (Offerte) commands")
    s = p.add_subparsers(dest="action")

    ls = s.add_parser("list", help="List quotes")
    ls.add_argument("--status", choices=list(STATUS_MAP))
    ls.add_argument("--limit", type=int, default=100)

    show = s.add_parser("show", help="Show quote")
    show.add_argument("id", type=int)

    send = s.add_parser("send", help="Send quote by email")
    send.add_argument("id", type=int)

    accept = s.add_parser("accept", help="Accept quote")
    accept.add_argument("id", type=int)

    decline = s.add_parser("decline", help="Decline quote")
    decline.add_argument("id", type=int)

    create_order = s.add_parser("create-order", help="Create order from quote")
    create_order.add_argument("id", type=int)

    search = s.add_parser("search", help="Search quotes by title")
    search.add_argument("query", type=str)

    delete = s.add_parser("delete", help="Delete quote")
    delete.add_argument("id", type=int)

    copy = s.add_parser("copy", help="Copy quote")
    copy.add_argument("id", type=int)

    pdf = s.add_parser("pdf", help="Download quote PDF")
    pdf.add_argument("id", type=int)
    pdf.add_argument("--output", "-o", help="Output filename")

    issue = s.add_parser("issue", help="Issue quote")
    issue.add_argument("id", type=int)

    revert = s.add_parser("revert", help="Revert quote to draft")
    revert.add_argument("id", type=int)

    reissue = s.add_parser("reissue", help="Reissue quote")
    reissue.add_argument("id", type=int)

    mark_sent = s.add_parser("mark-sent", help="Mark quote as sent")
    mark_sent.add_argument("id", type=int)

    create_invoice = s.add_parser("create-invoice", help="Create invoice from quote")
    create_invoice.add_argument("id", type=int)

    return p


def handle(args, client, json_flag):
    if args.action == "list":
        _list(args, client, json_flag)
    elif args.action == "show":
        _show(args, client, json_flag)
    elif args.action == "send":
        _action(args, client, json_flag, f"/kb_offer/{args.id}/send", "sent")
    elif args.action == "accept":
        _action(args, client, json_flag, f"/kb_offer/{args.id}/accept", "accepted")
    elif args.action == "decline":
        _action(args, client, json_flag, f"/kb_offer/{args.id}/decline", "declined")
    elif args.action == "create-order":
        _action(args, client, json_flag, f"/kb_offer/{args.id}/order", "converted to order")
    elif args.action == "search":
        _search(args, client, json_flag)
    elif args.action == "delete":
        _delete(args, client, json_flag)
    elif args.action == "copy":
        _copy(args, client, json_flag)
    elif args.action == "pdf":
        _pdf(args, client, json_flag)
    elif args.action == "issue":
        client.post(f"/kb_offer/{args.id}/issue")
        print(f"Quote {args.id} issued.")
    elif args.action == "revert":
        client.post(f"/kb_offer/{args.id}/revert")
        print(f"Quote {args.id} reverted to draft.")
    elif args.action == "reissue":
        client.post(f"/kb_offer/{args.id}/reissue")
        print(f"Quote {args.id} reissued.")
    elif args.action == "mark-sent":
        client.post(f"/kb_offer/{args.id}/mark_as_sent")
        print(f"Quote {args.id} marked as sent.")
    elif args.action == "create-invoice":
        result = client.post(f"/kb_offer/{args.id}/invoice")
        if json_flag:
            print_json(result)
            return
        print(f"Invoice {result['id']} created.")
    else:
        sys.exit("Usage: bexio quotes {list|show|send|accept|decline|create-order|search|delete|copy|pdf|issue|revert|reissue|mark-sent|create-invoice}")


def _list(args, client, json_flag):
    params = {"limit": args.limit}
    if args.status:
        params["kb_item_status_id"] = STATUS_MAP[args.status]
    quotes = client.get("/kb_offer", params=params)
    if not isinstance(quotes, list):
        sys.exit(f"Unexpected response: {quotes}")
    if json_flag:
        print_json(quotes)
        return
    for q in quotes:
        status = STATUS_LABELS.get(q.get("kb_item_status_id"), str(q.get("kb_item_status_id")))
        total = f"CHF {float(q.get('total', 0)):.2f}"
        date = (q.get("is_valid_from") or "")[:10]
        title = (q.get("title") or "")[:36]
        print(f"{q['id']:>5}  {q['document_nr']:<18}  {date:<10}  {total:>11}  {status:<10}  {title}")


def _show(args, client, json_flag):
    q = client.get(f"/kb_offer/{args.id}")
    if json_flag:
        print_json(q)
        return
    status = STATUS_LABELS.get(q.get("kb_item_status_id"), str(q.get("kb_item_status_id")))
    print(f"ID:      {q['id']}")
    print(f"Nr:      {q['document_nr']}")
    print(f"Title:   {q.get('title', '—')}")
    print(f"Date:    {q.get('is_valid_from', '—')}")
    print(f"Total:   CHF {float(q.get('total', 0)):.2f}")
    print(f"Status:  {status}")
    print(f"URL:     https://office.bexio.com/index.php/kb_offer/show/id/{q['id']}")


def _action(args, client, json_flag, path, verb):
    result = client.post(path)
    if json_flag:
        print_json(result)
        return
    print(f"Quote {args.id} {verb}.")


def _search(args, client, json_flag):
    results = client.post("/kb_offer/search", body=[
        {"field": "title", "value": args.query, "criteria": "like"}
    ])
    if not isinstance(results, list):
        sys.exit(f"Unexpected response: {results}")
    if json_flag:
        print_json(results)
        return
    if not results:
        print("No quotes found.")
        return
    for q in results:
        status = STATUS_LABELS.get(q.get("kb_item_status_id"), str(q.get("kb_item_status_id")))
        total = f"CHF {float(q.get('total', 0)):.2f}"
        date = (q.get("is_valid_from") or "")[:10]
        title = (q.get("title") or "")[:36]
        print(f"{q['id']:>5}  {q['document_nr']:<18}  {date:<10}  {total:>11}  {status:<10}  {title}")


def _delete(args, client, json_flag):
    client.delete(f"/kb_offer/{args.id}")
    print(f"Quote {args.id} deleted.")


def _copy(args, client, json_flag):
    result = client.post(f"/kb_offer/{args.id}/copy")
    if json_flag:
        print_json(result)
        return
    print(f"Quote {result['id']} created.")


def _pdf(args, client, json_flag):
    data = client.get_pdf(f"/kb_offer/{args.id}/pdf")
    filename = args.output or f"quote_{args.id}.pdf"
    with open(filename, "wb") as f:
        f.write(data)
    print(f"Saved to {filename}")

"""Bills commands (v4 API)."""

import sys
from bexio.output import print_json

BILLS_PATH = "/purchase/bills"


def register(sub):
    p = sub.add_parser("bills", help="Bill (purchase) commands")
    s = p.add_subparsers(dest="action")

    ls = s.add_parser("list", help="List bills")
    ls.add_argument("--limit", type=int, default=100)

    show = s.add_parser("show", help="Show bill detail")
    show.add_argument("id", help="Bill UUID")

    create = s.add_parser("create", help="Create a bill")
    create.add_argument("--title", required=True, help="Bill title")
    create.add_argument("--total", dest="total_gross", help="Gross total amount")
    create.add_argument("--contact-id", type=int, dest="contact_id", help="Contact ID")

    edit = s.add_parser("edit", help="Update a bill")
    edit.add_argument("id", help="Bill UUID")
    edit.add_argument("--title", help="New title")
    edit.add_argument("--total", dest="total_gross", help="New gross total")
    edit.add_argument("--bill-date", dest="bill_date", help="New bill date (YYYY-MM-DD)")
    edit.add_argument("--due-date", dest="due_date", help="New due date (YYYY-MM-DD)")
    edit.add_argument("--attach", dest="attachment_ids",
                      help="Comma-separated file UUIDs to set as attachments. "
                           "NOTE: this REPLACES the attachment list — pass every "
                           "UUID you want kept (the v4 PUT clears any omitted).")

    delete = s.add_parser("delete", help="Delete a bill")
    delete.add_argument("id", help="Bill UUID")

    mark_paid = s.add_parser("mark-paid", help="Mark bill as paid")
    mark_paid.add_argument("id", help="Bill UUID")

    return p


def handle(args, client, json_flag):
    if args.action == "list":
        _list(args, client, json_flag)
    elif args.action == "show":
        _show(args, client, json_flag)
    elif args.action == "create":
        _create(args, client, json_flag)
    elif args.action == "edit":
        _edit(args, client, json_flag)
    elif args.action == "delete":
        _delete(args, client, json_flag)
    elif args.action == "mark-paid":
        _mark_paid(args, client, json_flag)
    else:
        sys.exit("Usage: bexio bills {list|show|create|edit|delete|mark-paid}")


def _list(args, client, json_flag):
    params = {"limit": args.limit}
    bills = client.get_v4(BILLS_PATH, params=params)
    if not isinstance(bills, list):
        sys.exit(f"Unexpected response: {bills}")
    if json_flag:
        print_json(bills)
        return
    if not bills:
        print("No bills found.")
        return
    for b in bills:
        bid = b.get("id", "")
        doc_no = b.get("document_no", "")
        title = (b.get("title") or "")[:40]
        total = b.get("total_gross", "")
        status = b.get("status", "")
        print(f"{bid:<36}  {doc_no:<18}  {total:>10}  {status:<10}  {title}")


def _show(args, client, json_flag):
    bill = client.get_v4(f"{BILLS_PATH}/{args.id}")
    if json_flag:
        print_json(bill)
        return
    print(f"ID:         {bill.get('id', '')}")
    print(f"Doc No:     {bill.get('document_no', '—')}")
    print(f"Title:      {bill.get('title', '—')}")
    print(f"Total:      {bill.get('total_gross', '—')} {bill.get('currency_code', '')}")
    print(f"Net:        {bill.get('total_net', '—')}")
    print(f"Status:     {bill.get('status', '—')}")
    print(f"Contact ID: {bill.get('contact_id', '—')}")
    print(f"Created:    {bill.get('created_at', '—')}")


def _create(args, client, json_flag):
    body = {"title": args.title}
    if args.total_gross is not None:
        body["total_gross"] = args.total_gross
    if args.contact_id is not None:
        body["contact_id"] = args.contact_id
    bill = client.post_v4(BILLS_PATH, body=body)
    if json_flag:
        print_json(bill)
        return
    print(f"Bill {bill.get('id')} created")


def _edit(args, client, json_flag):
    # v4 purchase-bill PUT is patch-style for most scalar fields (rejects the full
    # echoed object, e.g. read-only `id`; leaves omitted scalars unchanged) — BUT
    # `attachment_ids` is replace-semantics: omit it and the API CLEARS the bill's
    # attachments. So we always read the current attachment_ids and carry them back
    # unless --attach explicitly overrides, otherwise a `--title` edit would silently
    # wipe the receipt off a booked bill.
    body = {}
    if args.title is not None:
        body["title"] = args.title
    if args.total_gross is not None:
        body["total_gross"] = args.total_gross
    if args.bill_date is not None:
        body["bill_date"] = args.bill_date
    if args.due_date is not None:
        body["due_date"] = args.due_date
    if args.attachment_ids is not None:
        body["attachment_ids"] = [x.strip() for x in args.attachment_ids.split(",") if x.strip()]
    else:
        current = client.get_v4(f"{BILLS_PATH}/{args.id}")
        existing = current.get("attachment_ids")
        if existing:
            body["attachment_ids"] = existing
    bill = client.put_v4(f"{BILLS_PATH}/{args.id}", body=body)
    if json_flag:
        print_json(bill)
        return
    print(f"Bill {args.id} updated")


def _delete(args, client, json_flag):
    client.delete_v4(f"{BILLS_PATH}/{args.id}")
    print(f"Bill {args.id} deleted")


def _mark_paid(args, client, json_flag):
    client.post_v4(f"{BILLS_PATH}/{args.id}/actions", body={"action": "mark_as_paid"})
    print(f"Bill {args.id} marked as paid")

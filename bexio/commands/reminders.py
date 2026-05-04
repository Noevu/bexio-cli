"""Reminder commands (nested under invoices)."""

import sys
from bexio.output import print_json


def register(sub):
    p = sub.add_parser("reminders", help="Invoice reminder commands")
    s = p.add_subparsers(dest="action")

    ls = s.add_parser("list", help="List reminders for an invoice")
    ls.add_argument("invoice_id", type=int)

    show = s.add_parser("show", help="Show a reminder")
    show.add_argument("invoice_id", type=int)
    show.add_argument("reminder_id", type=int)

    create = s.add_parser("create", help="Create a reminder")
    create.add_argument("invoice_id", type=int)
    create.add_argument("--title", default=None)

    delete = s.add_parser("delete", help="Delete a reminder")
    delete.add_argument("invoice_id", type=int)
    delete.add_argument("reminder_id", type=int)

    send = s.add_parser("send", help="Send reminder by email")
    send.add_argument("invoice_id", type=int)
    send.add_argument("reminder_id", type=int)

    mark_sent = s.add_parser("mark-sent", help="Mark reminder as sent")
    mark_sent.add_argument("invoice_id", type=int)
    mark_sent.add_argument("reminder_id", type=int)

    mark_unsent = s.add_parser("mark-unsent", help="Mark reminder as unsent")
    mark_unsent.add_argument("invoice_id", type=int)
    mark_unsent.add_argument("reminder_id", type=int)

    pdf = s.add_parser("pdf", help="Download reminder PDF")
    pdf.add_argument("invoice_id", type=int)
    pdf.add_argument("reminder_id", type=int)
    pdf.add_argument("--output", default=None)

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
    elif args.action == "send":
        _post_action(args, client, json_flag,
                     f"/kb_invoice/{args.invoice_id}/kb_reminder/{args.reminder_id}/send",
                     f"Reminder {args.reminder_id} sent")
    elif args.action == "mark-sent":
        _post_action(args, client, json_flag,
                     f"/kb_invoice/{args.invoice_id}/kb_reminder/{args.reminder_id}/mark_as_sent",
                     f"Reminder {args.reminder_id} marked as sent")
    elif args.action == "mark-unsent":
        _post_action(args, client, json_flag,
                     f"/kb_invoice/{args.invoice_id}/kb_reminder/{args.reminder_id}/mark_as_unsent",
                     f"Reminder {args.reminder_id} marked as unsent")
    elif args.action == "pdf":
        _pdf(args, client)
    else:
        sys.exit("Usage: bexio reminders {list|show|create|delete|send|mark-sent|mark-unsent|pdf}")


def _list(args, client, json_flag):
    reminders = client.get(f"/kb_invoice/{args.invoice_id}/kb_reminder")
    if not isinstance(reminders, list):
        sys.exit(f"Unexpected response: {reminders}")
    if json_flag:
        print_json(reminders)
        return
    if not reminders:
        print("No reminders found.")
        return
    for r in reminders:
        due = (r.get("due_date") or "")[:10]
        total = r.get("total", "")
        doc_nr = (r.get("document_nr") or "")
        title = (r.get("title") or "")[:40]
        print(f"{r['id']:>5}  {doc_nr:<18}  {title:<40}  {due:<10}  {total}")


def _show(args, client, json_flag):
    r = client.get(f"/kb_invoice/{args.invoice_id}/kb_reminder/{args.reminder_id}")
    if json_flag:
        print_json(r)
        return
    print(f"ID:         {r['id']}")
    print(f"Nr:         {r.get('document_nr', '—')}")
    print(f"Title:      {r.get('title', '—')}")
    print(f"Invoice ID: {r.get('kb_invoice_id', '—')}")
    print(f"Valid from: {r.get('is_valid_from', '—')}")
    print(f"Due date:   {r.get('due_date', '—')}")
    print(f"Total:      {r.get('total', '—')}")


def _create(args, client, json_flag):
    body = {}
    if args.title:
        body["title"] = args.title
    r = client.post(f"/kb_invoice/{args.invoice_id}/kb_reminder", body=body)
    if json_flag:
        print_json(r)
        return
    print(f"Reminder {r['id']} created")


def _delete(args, client, json_flag):
    result = client.delete(f"/kb_invoice/{args.invoice_id}/kb_reminder/{args.reminder_id}")
    if json_flag:
        print_json(result)
        return
    print(f"Reminder {args.reminder_id} deleted")


def _post_action(args, client, json_flag, path, message):
    result = client.post(path)
    if json_flag:
        print_json(result)
        return
    print(message)


def _pdf(args, client):
    data = client.get_pdf(f"/kb_invoice/{args.invoice_id}/kb_reminder/{args.reminder_id}/pdf")
    filename = args.output or f"reminder_{args.reminder_id}.pdf"
    with open(filename, "wb") as f:
        f.write(data)
    print(f"Saved to {filename}")

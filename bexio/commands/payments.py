"""Payment commands — invoice payments via /kb_invoice/{invoice_id}/payment."""

import sys
from bexio.output import print_json


def register(sub):
    p = sub.add_parser("payments", help="Invoice payment commands")
    s = p.add_subparsers(dest="action")

    ls = s.add_parser("list", help="List payments for an invoice")
    ls.add_argument("invoice_id", type=int)

    show = s.add_parser("show", help="Show a single payment")
    show.add_argument("invoice_id", type=int)
    show.add_argument("payment_id", type=int)

    create = s.add_parser("create", help="Create a payment for an invoice")
    create.add_argument("invoice_id", type=int)
    create.add_argument("--amount", required=True, help="Payment amount (e.g. 100.00)")
    create.add_argument("--date", required=True, help="Payment date (YYYY-MM-DD)")
    create.add_argument("--payment-type-id", type=int, default=None)

    delete = s.add_parser("delete", help="Delete a payment")
    delete.add_argument("invoice_id", type=int)
    delete.add_argument("payment_id", type=int)

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
        sys.exit("Usage: bexio payments {list|show|create|delete}")


def _list(args, client, json_flag):
    payments = client.get(f"/kb_invoice/{args.invoice_id}/payment")
    if not isinstance(payments, list):
        sys.exit(f"Unexpected response: {payments}")
    if json_flag:
        print_json(payments)
        return
    for p in payments:
        pid = p.get("id", "")
        date = p.get("date", "")
        amount = p.get("value", "")
        ptype = p.get("payment_type_id", "")
        print(f"{pid:>5}  {date:<12}  {amount:>10}  type={ptype}")


def _show(args, client, json_flag):
    payment = client.get(f"/kb_invoice/{args.invoice_id}/payment/{args.payment_id}")
    if json_flag:
        print_json(payment)
        return
    print(f"ID:               {payment.get('id')}")
    print(f"Date:             {payment.get('date')}")
    print(f"Amount:           {payment.get('value')}")
    print(f"Payment type ID:  {payment.get('payment_type_id')}")


def _create(args, client, json_flag):
    body = {
        "value": args.amount,
        "date": args.date,
    }
    if args.payment_type_id is not None:
        body["payment_type_id"] = args.payment_type_id
    result = client.post(f"/kb_invoice/{args.invoice_id}/payment", body=body)
    if json_flag:
        print_json(result)
        return
    print(f"Payment {result.get('id')} created")


def _delete(args, client, json_flag):
    client.delete(f"/kb_invoice/{args.invoice_id}/payment/{args.payment_id}")
    print(f"Payment {args.payment_id} deleted")

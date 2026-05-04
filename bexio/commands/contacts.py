"""Contact commands."""

import sys
from bexio.output import print_json


def register(sub):
    p = sub.add_parser("contacts", help="Contact commands")
    s = p.add_subparsers(dest="action")

    ls = s.add_parser("list", help="List contacts")
    ls.add_argument("--limit", type=int, default=100)

    show = s.add_parser("show", help="Show contact")
    show.add_argument("id", type=int)

    search = s.add_parser("search", help="Search contacts by name")
    search.add_argument("query", type=str)

    create = s.add_parser("create", help="Create a contact")
    create.add_argument("--name", help="Company name")
    create.add_argument("--firstname", help="First name (person)")
    create.add_argument("--lastname", help="Last name (person)")
    create.add_argument("--email", dest="mail")
    create.add_argument("--phone", dest="phone_fixed")
    create.add_argument("--type", dest="contact_type_id", type=int, default=1,
                        help="1=company (default), 2=person")

    edit = s.add_parser("edit", help="Edit a contact")
    edit.add_argument("id", type=int)
    edit.add_argument("--name", help="Company name")
    edit.add_argument("--firstname", help="First name")
    edit.add_argument("--lastname", help="Last name")
    edit.add_argument("--email", dest="mail")
    edit.add_argument("--phone", dest="phone_fixed")

    delete = s.add_parser("delete", help="Delete a contact")
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
        sys.exit("Usage: bexio contacts {list|show|search|create|edit|delete}")


def _list(args, client, json_flag):
    contacts = client.get("/contact", params={"limit": args.limit})
    if not isinstance(contacts, list):
        sys.exit(f"Unexpected response: {contacts}")
    if json_flag:
        print_json(contacts)
        return
    for c in contacts:
        name = c.get("name", "") or f"{c.get('firstname', '')} {c.get('lastname', '')}".strip()
        email = (c.get("mail") or "")[:36]
        print(f"{c['id']:>5}  {name[:40]:<40}  {email}")


def _show(args, client, json_flag):
    c = client.get(f"/contact/{args.id}")
    if json_flag:
        print_json(c)
        return
    name = c.get("name", "") or f"{c.get('firstname', '')} {c.get('lastname', '')}".strip()
    print(f"ID:      {c['id']}")
    print(f"Name:    {name}")
    print(f"Email:   {c.get('mail', '—')}")
    print(f"Phone:   {c.get('phone_fixed', '—')}")
    print(f"URL:     https://office.bexio.com/index.php/contact/show/id/{c['id']}")


def _create(args, client, json_flag):
    body = {"contact_type_id": args.contact_type_id}
    if args.name:
        body["name"] = args.name
    if args.firstname:
        body["firstname"] = args.firstname
    if args.lastname:
        body["lastname"] = args.lastname
    if args.mail:
        body["mail"] = args.mail
    if args.phone_fixed:
        body["phone_fixed"] = args.phone_fixed
    if not body.get("name") and not (body.get("firstname") or body.get("lastname")):
        sys.exit("Provide --name (company) or --firstname/--lastname (person)")
    result = client.post("/contact", body=body)
    if json_flag:
        print_json(result)
        return
    print(f"Contact #{result.get('id')} created")
    print(f"  https://office.bexio.com/index.php/contact/show/id/{result.get('id')}")


def _search(args, client, json_flag):
    results = client.post("/contact/search", body=[
        {"field": "name", "value": args.query, "criteria": "like"}
    ])
    if not isinstance(results, list):
        sys.exit(f"Unexpected response: {results}")
    if json_flag:
        print_json(results)
        return
    if not results:
        print("No contacts found.")
        return
    for c in results:
        name = c.get("name", "") or f"{c.get('firstname', '')} {c.get('lastname', '')}".strip()
        print(f"{c['id']:>5}  {name[:40]:<40}  {c.get('mail', '')}")


def _edit(args, client, json_flag):
    body = {}
    if args.name is not None:
        body["name"] = args.name
    if args.firstname is not None:
        body["firstname"] = args.firstname
    if args.lastname is not None:
        body["lastname"] = args.lastname
    if args.mail is not None:
        body["mail"] = args.mail
    if args.phone_fixed is not None:
        body["phone_fixed"] = args.phone_fixed
    result = client.put(f"/contact/{args.id}", body=body)
    if json_flag:
        print_json(result)
        return
    print(f"Contact {args.id} updated.")


def _delete(args, client, json_flag):
    client.delete(f"/contact/{args.id}")
    print(f"Contact {args.id} deleted.")

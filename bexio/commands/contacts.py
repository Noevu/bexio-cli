"""Contact commands."""

import sys
from bexio.output import print_json

# Bexio's writable address fields. The single `address` field a GET returns is
# read-only (Bexio composes it from these), so writes use the parts. NOE-3277.
_ADDRESS_ARGS = [
    ("--street", "street_name", "Street name"),
    ("--house-number", "house_number", "House number"),
    ("--address-addition", "address_addition", "Extra address line (c/o, building)"),
    ("--postcode", "postcode", "Postal code"),
    ("--city", "city", "City"),
]

# Writable contact fields carried over unchanged when editing (Bexio's edit
# replaces the whole record, so anything omitted is wiped).
_EDIT_CARRY_SCALAR = [
    "contact_type_id", "nr", "name_1", "name_2", "salutation_id", "salutation_form",
    "titel_id", "birthday", "street_name", "house_number", "address_addition",
    "postcode", "city", "country_id", "mail", "mail_second", "phone_fixed",
    "phone_fixed_second", "phone_mobile", "fax", "url", "skype_name", "remarks",
    "language_id", "user_id", "owner_id",
]
_EDIT_CARRY_LIST = ["contact_group_ids", "contact_branch_ids"]


def _add_address_args(parser):
    for flag, dest, help_text in _ADDRESS_ARGS:
        parser.add_argument(flag, dest=dest, help=help_text)
    parser.add_argument("--country-id", dest="country_id", type=int,
                        help="Country id (1 = Switzerland)")


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
    _add_address_args(create)

    edit = s.add_parser("edit", help="Edit a contact")
    edit.add_argument("id", type=int)
    edit.add_argument("--name", help="Company name")
    edit.add_argument("--firstname", help="First name")
    edit.add_argument("--lastname", help="Last name")
    edit.add_argument("--email", dest="mail")
    edit.add_argument("--phone", dest="phone_fixed")
    _add_address_args(edit)

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


# Bexio führt Namen ausschliesslich in `name_1` und `name_2`. Die Felder `name`,
# `firstname` und `lastname` kommen in KEINER Antwort vor — sie hier zu lesen
# ergab stumm eine leere Spalte, und `field: "name"` in der Suche quittierte Bexio
# mit HTTP 400 ("The following search parameters could not have been applied").
# Gemessen am 2026-09-02 gegen die Live-API: `name_1` und `name_2` sind gültige
# Suchfelder, `name` ist keines.
CONTACT_TYPE_PERSON = 2


def _display_name(contact: dict) -> str:
    """Anzeigename aus den Feldern, die Bexio wirklich liefert.

    Firma: `name_1` ist der Firmenname, `name_2` ein Zusatz.
    Person: `name_1` ist der NACHname, `name_2` der Vorname — deshalb gedreht.
    """
    n1 = (contact.get("name_1") or "").strip()
    n2 = (contact.get("name_2") or "").strip()
    if contact.get("contact_type_id") == CONTACT_TYPE_PERSON and n2:
        return f"{n2} {n1}".strip()
    return " ".join(part for part in (n1, n2) if part)


def _list(args, client, json_flag):
    contacts = client.get("/contact", params={"limit": args.limit})
    if not isinstance(contacts, list):
        sys.exit(f"Unexpected response: {contacts}")
    if json_flag:
        print_json(contacts)
        return
    for c in contacts:
        name = _display_name(c)
        email = (c.get("mail") or "")[:36]
        print(f"{c['id']:>5}  {name[:40]:<40}  {email}")


def _show(args, client, json_flag):
    c = client.get(f"/contact/{args.id}")
    if json_flag:
        print_json(c)
        return
    name = _display_name(c)
    print(f"ID:      {c['id']}")
    print(f"Name:    {name}")
    print(f"Email:   {c.get('mail', '—')}")
    print(f"Phone:   {c.get('phone_fixed', '—')}")
    print(f"URL:     https://office.bexio.com/index.php/contact/show/id/{c['id']}")


def _create(args, client, json_flag):
    # Bexio names its fields name_1/name_2, not name/firstname/lastname, and demands
    # user_id + owner_id — anything else comes back as 422 "Pflichtfeld".
    # Company: name_1 = company name. Person: name_1 = surname, name_2 = given name.
    body = {"contact_type_id": args.contact_type_id, "user_id": 1, "owner_id": 1}
    if args.name:
        body["name_1"] = args.name
    if args.lastname:
        body["name_1"] = args.lastname
    if args.firstname:
        body["name_2"] = args.firstname
    if args.mail:
        body["mail"] = args.mail
    if args.phone_fixed:
        body["phone_fixed"] = args.phone_fixed
    for _flag, dest, _help in _ADDRESS_ARGS:
        if getattr(args, dest):
            body[dest] = getattr(args, dest)
    if args.country_id is not None:
        body["country_id"] = args.country_id
    if not body.get("name_1") and not body.get("name_2"):
        sys.exit("Provide --name (company) or --firstname/--lastname (person)")
    result = client.post("/contact", body=body)
    if json_flag:
        print_json(result)
        return
    print(f"Contact #{result.get('id')} created")
    print(f"  https://office.bexio.com/index.php/contact/show/id/{result.get('id')}")


def _search(args, client, json_flag):
    # Zwei Abfragen statt einer: mehrere Kriterien in EINEM Rumpf verknüpft Bexio
    # mit UND, gesucht ist aber ODER — sonst findet «Benedikt» nie eine Person,
    # deren Vorname in `name_2` steht, und «Vogel» nie eine Firma in `name_1`.
    results: list = []
    seen: set = set()
    for field in ("name_1", "name_2"):
        hits = client.post("/contact/search", body=[
            {"field": field, "value": args.query, "criteria": "like"}
        ])
        if not isinstance(hits, list):
            sys.exit(f"Unexpected response: {hits}")
        for c in hits:
            if c.get("id") not in seen:
                seen.add(c.get("id"))
                results.append(c)
    if json_flag:
        print_json(results)
        return
    if not results:
        print("No contacts found.")
        return
    for c in results:
        print(f"{c['id']:>5}  {_display_name(c)[:40]:<40}  {c.get('mail', '')}")


def _edit(args, client, json_flag):
    # Bexio edit is POST /2.0/contact/{id} and REPLACES the whole record — read the
    # existing contact, carry its writable fields over, then overlay the changes so
    # nothing (address, phone, group membership) is silently wiped. NOE-3277.
    existing = client.get(f"/contact/{args.id}")
    body = {}
    for field in _EDIT_CARRY_SCALAR:
        value = existing.get(field)
        if value is not None:
            body[field] = value
    for field in _EDIT_CARRY_LIST:
        value = existing.get(field)
        if value:
            body[field] = ",".join(str(v) for v in value) if isinstance(value, list) else value
    body.setdefault("contact_type_id", 1)
    body.setdefault("user_id", 1)
    body.setdefault("owner_id", 1)

    if args.name is not None:
        body["name_1"] = args.name
    if args.lastname is not None:
        body["name_1"] = args.lastname
    if args.firstname is not None:
        body["name_2"] = args.firstname
    if args.mail is not None:
        body["mail"] = args.mail
    if args.phone_fixed is not None:
        body["phone_fixed"] = args.phone_fixed
    for _flag, dest, _help in _ADDRESS_ARGS:
        if getattr(args, dest) is not None:
            body[dest] = getattr(args, dest)
    if args.country_id is not None:
        body["country_id"] = args.country_id

    result = client.post(f"/contact/{args.id}", body=body)
    if json_flag:
        print_json(result)
        return
    print(f"Contact {args.id} updated.")


def _delete(args, client, json_flag):
    client.delete(f"/contact/{args.id}")
    print(f"Contact {args.id} deleted.")

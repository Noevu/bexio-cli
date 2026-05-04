"""Reference data lookup commands: languages, contact-groups, business-activities."""

import sys
from bexio.output import print_json


def register(sub):
    parsers = {}

    # languages
    p = sub.add_parser("languages", help="Language reference data")
    s = p.add_subparsers(dest="action")
    s.add_parser("list", help="List languages")
    parsers["languages"] = p

    # contact-groups
    p2 = sub.add_parser("contact-groups", help="Contact group reference data")
    s2 = p2.add_subparsers(dest="action")
    s2.add_parser("list", help="List contact groups")
    parsers["contact-groups"] = p2

    # business-activities
    p3 = sub.add_parser("business-activities", help="Business activity reference data")
    s3 = p3.add_subparsers(dest="action")
    s3.add_parser("list", help="List business activities")
    show = s3.add_parser("show", help="Show business activity")
    show.add_argument("id", type=int)
    parsers["business-activities"] = p3

    return parsers


def handle(args, client, json_flag):
    if args.resource == "languages":
        _languages_handle(args, client, json_flag)
    elif args.resource == "contact-groups":
        _contact_groups_handle(args, client, json_flag)
    elif args.resource == "business-activities":
        _business_activities_handle(args, client, json_flag)


# --- languages ---

def _languages_handle(args, client, json_flag):
    if args.action == "list":
        _languages_list(args, client, json_flag)
    else:
        sys.exit("Usage: bexio languages list")


def _languages_list(args, client, json_flag):
    languages = client.get("/language")
    if not isinstance(languages, list):
        sys.exit(f"Unexpected response: {languages}")
    if json_flag:
        print_json(languages)
        return
    for lang in languages:
        print(f"{lang['id']:>4}  {lang.get('iso_639_1', ''):>4}  {lang.get('name', '')}")


# --- contact-groups ---

def _contact_groups_handle(args, client, json_flag):
    if args.action == "list":
        _contact_groups_list(args, client, json_flag)
    else:
        sys.exit("Usage: bexio contact-groups list")


def _contact_groups_list(args, client, json_flag):
    groups = client.get("/contact_group")
    if not isinstance(groups, list):
        sys.exit(f"Unexpected response: {groups}")
    if json_flag:
        print_json(groups)
        return
    for g in groups:
        print(f"{g['id']:>4}  {g.get('name', '')}")


# --- business-activities ---

def _business_activities_handle(args, client, json_flag):
    if args.action == "list":
        _business_activities_list(args, client, json_flag)
    elif args.action == "show":
        _business_activities_show(args, client, json_flag)
    else:
        sys.exit("Usage: bexio business-activities {list|show}")


def _business_activities_list(args, client, json_flag):
    activities = client.get("/client_service")
    if not isinstance(activities, list):
        sys.exit(f"Unexpected response: {activities}")
    if json_flag:
        print_json(activities)
        return
    for a in activities:
        billable = "yes" if a.get("default_is_billable") else "no"
        price = a.get("default_price_per_hour", "—")
        print(f"{a['id']:>4}  {a.get('name', ''):<30}  {billable:<4}  {price}")


def _business_activities_show(args, client, json_flag):
    a = client.get(f"/client_service/{args.id}")
    if json_flag:
        print_json(a)
        return
    print(f"ID:          {a['id']}")
    print(f"Name:        {a.get('name', '—')}")
    print(f"Billable:    {'yes' if a.get('default_is_billable') else 'no'}")
    print(f"Price/h:     {a.get('default_price_per_hour', '—')}")
    print(f"Account ID:  {a.get('account_id', '—')}")

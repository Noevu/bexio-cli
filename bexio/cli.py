"""bexio CLI entrypoint."""

import argparse
import sys

from bexio import __version__
from bexio.auth import cmd_auth_login, cmd_auth_logout, cmd_auth_status, get_token
from bexio.client import BexioClient
from bexio.commands import accounts, bills, contacts, countries, currencies, invoices, items, lookup, orders, payment_types, payments, projects, quotes, reminders, taxes, timesheets


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="bexio",
        description="Command-line interface for the Bexio API",
    )
    parser.add_argument("--version", action="version", version=f"bexio-cli {__version__}")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")

    sub = parser.add_subparsers(dest="resource")

    # auth
    auth_p = sub.add_parser("auth", help="Authentication commands")
    auth_sub = auth_p.add_subparsers(dest="action")
    auth_sub.add_parser("login", help="Store API token")
    auth_sub.add_parser("logout", help="Remove stored token")
    auth_sub.add_parser("status", help="Show auth status")

    # resource commands
    bills.register(sub)
    items.register(sub)
    payments.register(sub)
    orders.register(sub)
    invoices.register(sub)
    contacts.register(sub)
    quotes.register(sub)
    countries.register(sub)
    currencies.register(sub)
    lookup.register(sub)
    accounts.register(sub)
    accounts.register_groups(sub)
    payment_types.register(sub)
    taxes.register_taxes(sub)
    taxes.register_vat_periods(sub)
    timesheets.register(sub)
    projects.register(sub)
    projects.register_milestones(sub)
    projects.register_work_packages(sub)
    reminders.register(sub)

    args = parser.parse_args()

    if not args.resource:
        parser.print_help()
        sys.exit(1)

    # auth commands don't need a token
    if args.resource == "auth":
        action = getattr(args, "action", None)
        if action == "login":
            cmd_auth_login(args)
        elif action == "logout":
            cmd_auth_logout(args)
        elif action == "status":
            cmd_auth_status(args)
        else:
            auth_p.print_help()
            sys.exit(1)
        return

    client = BexioClient(get_token())
    json_flag = args.json

    if args.resource == "bills":
        bills.handle(args, client, json_flag)
    elif args.resource == "items":
        items.handle(args, client, json_flag)
    elif args.resource == "payments":
        payments.handle(args, client, json_flag)
    elif args.resource == "orders":
        orders.handle(args, client, json_flag)
    elif args.resource == "invoices":
        invoices.handle(args, client, json_flag)
    elif args.resource == "contacts":
        contacts.handle(args, client, json_flag)
    elif args.resource == "quotes":
        quotes.handle(args, client, json_flag)
    elif args.resource == "countries":
        countries.handle(args, client, json_flag)
    elif args.resource == "currencies":
        currencies.handle(args, client, json_flag)
    elif args.resource in ("languages", "contact-groups", "business-activities"):
        lookup.handle(args, client, json_flag)
    elif args.resource == "accounts":
        accounts.handle(args, client, json_flag)
    elif args.resource == "account-groups":
        accounts.handle_groups(args, client, json_flag)
    elif args.resource == "payment-types":
        payment_types.handle(args, client, json_flag)
    elif args.resource == "taxes":
        taxes.handle_taxes(args, client, json_flag)
    elif args.resource == "vat-periods":
        taxes.handle_vat_periods(args, client, json_flag)
    elif args.resource == "timesheets":
        timesheets.handle(args, client, json_flag)
    elif args.resource == "projects":
        projects.handle(args, client, json_flag)
    elif args.resource == "milestones":
        projects.handle_milestones(args, client, json_flag)
    elif args.resource == "work-packages":
        projects.handle_work_packages(args, client, json_flag)
    elif args.resource == "reminders":
        reminders.handle(args, client, json_flag)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()

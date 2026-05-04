"""bexio CLI entrypoint."""

import argparse
import sys

from bexio import __version__
from bexio.auth import cmd_auth_login, cmd_auth_logout, cmd_auth_status, get_token
from bexio.client import BexioClient
from bexio.commands import contacts, invoices, orders, quotes


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
    orders.register(sub)
    invoices.register(sub)
    contacts.register(sub)
    quotes.register(sub)

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

    if args.resource == "orders":
        orders.handle(args, client, json_flag)
    elif args.resource == "invoices":
        invoices.handle(args, client, json_flag)
    elif args.resource == "contacts":
        contacts.handle(args, client, json_flag)
    elif args.resource == "quotes":
        quotes.handle(args, client, json_flag)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()

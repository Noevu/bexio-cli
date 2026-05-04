# bexio-cli

Command-line interface for the [Bexio API](https://docs.bexio.com). Manage orders, invoices, contacts, quotes, projects, timesheets, and more from your terminal.

```sh
bexio orders list --recurring
bexio invoices list --status open
bexio orders create-invoice 47
bexio timesheets list --limit 50
bexio projects list
```

## Installation

```sh
pipx install git+https://github.com/noevu/bexio-cli
```

Requires Python 3.10+. The `keyring` package is the only runtime dependency and is installed automatically.

## Authentication

Get your API token from **Bexio → Settings → API tokens**.

```sh
bexio auth login        # store token in system keyring (macOS Keychain, Windows Credential Manager, Linux Secret Service)
bexio auth status       # show where token is coming from
bexio auth logout       # remove stored token
```

Or set the environment variable (useful for CI/scripts):

```sh
export BEXIO_API_TOKEN=<token>
```

The env var takes priority over the keyring.

## Commands

### Orders

```sh
bexio orders list                    # all orders
bexio orders list --recurring        # only recurring orders (Aufträge)
bexio orders show <id>               # order details + repetition settings
bexio orders search <query>          # search by name
bexio orders create-invoice <id>     # create invoice from order
bexio orders delete <id>             # delete order
bexio orders pdf <id>                # download PDF (saves to order_<id>.pdf)
bexio orders pdf <id> --output out.pdf
```

### Invoices

```sh
bexio invoices list                          # all invoices
bexio invoices list --status open            # filter: draft | open | partial | paid | cancelled
bexio invoices show <id>
bexio invoices search <query>
bexio invoices send <id>                     # send by email
bexio invoices mark-sent <id>                # mark as sent without sending email
bexio invoices cancel <id>
bexio invoices issue <id>                    # finalize / issue invoice
bexio invoices revert-issue <id>             # revert issued invoice to draft
bexio invoices copy <id>                     # copy invoice
bexio invoices delete <id>
bexio invoices pdf <id>                      # download PDF
bexio invoices pdf <id> --output out.pdf
```

### Quotes

```sh
bexio quotes list                            # all quotes
bexio quotes list --status accepted          # filter: draft | sent | accepted | declined
bexio quotes show <id>
bexio quotes search <query>
bexio quotes send <id>
bexio quotes issue <id>
bexio quotes accept <id>
bexio quotes decline <id>
bexio quotes revert <id>                     # revert to draft
bexio quotes reissue <id>
bexio quotes mark-sent <id>
bexio quotes copy <id>
bexio quotes create-order <id>               # convert quote to order
bexio quotes create-invoice <id>             # convert quote to invoice
bexio quotes delete <id>
bexio quotes pdf <id>                        # download PDF
bexio quotes pdf <id> --output out.pdf
```

### Contacts

```sh
bexio contacts list
bexio contacts show <id>
bexio contacts search <query>
bexio contacts create --name "Muster AG" --email info@muster.ch
bexio contacts create --firstname Anna --lastname Muster --phone "+41 44 000 00 00" --type 2
bexio contacts edit <id> --name "New Name" --email new@example.com
bexio contacts delete <id>
```

### Payments

```sh
bexio payments list <invoice_id>             # list payments for an invoice
bexio payments show <invoice_id> <id>
bexio payments create <invoice_id> --amount 1500.00 --date 2024-03-01
bexio payments create <invoice_id> --amount 500.00 --date 2024-03-15 --payment-type-id 1
bexio payments delete <invoice_id> <id>
```

### Items / Products

```sh
bexio items list
bexio items list --limit 200
bexio items show <id>
bexio items search <query>
bexio items create --name "Widget Pro" --sale-price 25.00 --unit-id 1
bexio items edit <id> --sale-price 29.90
bexio items delete <id>
```

### Bills

```sh
bexio bills list
bexio bills show <id>
bexio bills create --title "Server Hosting Q1" --total 1200.00 --contact-id 42
bexio bills edit <id> --title "Updated Title"
bexio bills mark-paid <id>
bexio bills delete <id>
```

### Projects

```sh
bexio projects list
bexio projects show <id>
bexio projects search <query>
bexio projects create --name "Website Redesign" --contact-id 5
bexio projects edit <id> --name "Updated Name"
bexio projects archive <id>
bexio projects reactivate <id>
bexio projects delete <id>
bexio projects types                         # list project types
bexio projects statuses                      # list project statuses
```

### Milestones

```sh
bexio milestones list --project-id <id>
bexio milestones show --project-id <id> <milestone_id>
bexio milestones create --project-id <id> --name "Phase 1" --finish-date 2024-06-30
bexio milestones edit --project-id <id> <milestone_id> --name "Phase 1 Updated"
bexio milestones delete --project-id <id> <milestone_id>
```

### Work Packages

```sh
bexio work-packages list --project-id <id>
bexio work-packages show --project-id <id> <package_id>
bexio work-packages create --project-id <id> --name "Frontend Development" --hours 40
bexio work-packages edit --project-id <id> <package_id> --name "Updated"
bexio work-packages delete --project-id <id> <package_id>
```

### Timesheets

```sh
bexio timesheets list
bexio timesheets list --limit 100
bexio timesheets show <id>
bexio timesheets search <query>
bexio timesheets create --date 2024-03-15 --duration 03:30 --project-id 20 --text "Homepage work"
bexio timesheets edit <id> --duration 04:00 --text "Updated"
bexio timesheets delete <id>
bexio timesheets statuses                    # list timesheet statuses
```

### Reminders

```sh
bexio reminders list <invoice_id>
bexio reminders show <invoice_id> <reminder_id>
bexio reminders create <invoice_id> --title "Zahlungserinnerung"
bexio reminders send <invoice_id> <reminder_id>
bexio reminders mark-sent <invoice_id> <reminder_id>
bexio reminders mark-unsent <invoice_id> <reminder_id>
bexio reminders delete <invoice_id> <reminder_id>
bexio reminders pdf <invoice_id> <reminder_id>
bexio reminders pdf <invoice_id> <reminder_id> --output reminder.pdf
```

### Accounting reference data

```sh
bexio taxes list
bexio taxes show <id>
bexio accounts list
bexio accounts show <id>
bexio accounts search <query>
bexio account-groups list
bexio vat-periods list
bexio currencies list
bexio currencies show <id>
bexio currencies exchange-rates <code>      # e.g. CHF
bexio payment-types list
bexio payment-types show <id>
bexio countries list
bexio countries show <id>
bexio countries search <query>
bexio languages list
bexio contact-groups list
bexio business-activities list
bexio units list
bexio units show <id>
bexio units create --name "Stunde"
bexio units delete <id>
```

### Global flags

```sh
--json      Output raw JSON (pipe to jq, use in scripts)
--version   Show version
```

## Examples

Create invoices for all recurring orders:

```sh
bexio orders list --recurring --json \
  | jq -r '.[].id' \
  | xargs -I{} bexio orders create-invoice {}
```

List open invoices as JSON and process with jq:

```sh
bexio invoices list --status open --json | jq '.[] | {id, nr: .document_nr, total}'
```

Log today's work across projects:

```sh
bexio timesheets create --date $(date +%F) --duration 02:00 --project-id 20 --text "Client call"
bexio timesheets create --date $(date +%F) --duration 05:30 --project-id 21 --text "Development"
```

## Development

```sh
git clone https://github.com/noevu/bexio-cli
cd bexio-cli
pip install -e .
python -m unittest discover -s tests -v
```

## Need Custom Bexio Automation?

This tool is built and maintained by [Noevu](https://noevu.ch) — a Swiss web agency specialising in [AI-powered automation for Swiss SMEs](https://noevu.ch/en/services/ai-automation).

Need custom Bexio integrations, automated invoicing workflows, or AI-assisted accounting processes? [Get in touch with Noevu](https://noevu.ch/en/services/ai-automation).

## License

MIT

# bexio-cli

Command-line interface for the [Bexio](https://www.bexio.com) API. Manage orders, invoices, contacts, and quotes from your terminal.

```sh
bexio orders list --recurring
bexio invoices list --status open
bexio orders create-invoice 47
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
bexio orders create-invoice <id>     # create invoice from order
```

### Invoices

```sh
bexio invoices list                          # all invoices
bexio invoices list --status open            # filter: draft | open | partial | paid | cancelled
bexio invoices show <id>
bexio invoices send <id>                     # send by email
bexio invoices mark-sent <id>               # mark as sent without sending email
bexio invoices cancel <id>
bexio invoices issue <id>                    # finalize / issue invoice
```

### Contacts

```sh
bexio contacts list
bexio contacts show <id>
bexio contacts search <query>
```

### Quotes

```sh
bexio quotes list                            # all quotes
bexio quotes list --status accepted          # filter: draft | sent | accepted | declined
bexio quotes show <id>
bexio quotes send <id>
bexio quotes accept <id>
bexio quotes decline <id>
bexio quotes create-order <id>              # convert quote to order
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

## Development

```sh
git clone https://github.com/noevu/bexio-cli
cd bexio-cli
pip install -e .
python -m unittest discover -s tests -v
```

## License

MIT

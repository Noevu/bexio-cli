# bexio-cli + bexio-mcp

🇩🇪 [Deutsche Version](README.de.md)

A tool that lets you control your [Bexio](https://www.bexio.com) account from your computer's Terminal — without clicking through the browser. Also includes an MCP server so AI assistants like Claude can talk to Bexio directly in conversation.

**What you can do with it:**
- Create invoices from all your recurring orders in one command
- Download invoice and quote PDFs in bulk
- List everything that's overdue or in draft
- Log timesheets, manage projects, record payments
- Connect Bexio to other tools and scripts

Built and maintained by [Noevu](https://noevu.ch) — a Swiss web agency specialising in [AI-powered automation for Swiss SMEs](https://noevu.ch/en/services/ai-automation).

**Why use a Terminal tool instead of clicking through Bexio?**

- **Speed.** What takes 10 minutes of clicking takes 10 seconds.
- **Batch work.** Create invoices for 30 recurring orders at once. Download 50 PDFs in one go. You can't do that in the browser.
- **Automation.** Run it on a schedule — invoices created automatically every month, no manual steps.
- **No browser required.** Works on servers, in scripts, in CI/CD pipelines, anywhere Python runs.
- **AI-ready.** Connect it to AI tools (like Claude or ChatGPT) so your AI assistant can look up and update your Bexio data directly.
- **Free and open source.** No extra subscription. Runs on your machine.

---

## What is a Terminal?

The Terminal is a text-based way to control your computer. On a Mac, press **⌘ Space**, type `Terminal`, and press Enter. On Windows, search for **Command Prompt** or **PowerShell**. You type a command and press Enter — the computer does the rest.

---

## Setup (one time)

### Step 1 — Install Python

This tool requires Python 3.10 or newer. Check if you already have it:

```
python3 --version
```

If you see `Python 3.10` or higher, you're good. Otherwise, download it from [python.org/downloads](https://www.python.org/downloads/).

### Step 2 — Install the tool

Copy and paste this into your Terminal, then press Enter:

```
pipx install git+https://github.com/noevu/bexio-cli
```

If `pipx` is not found, install it first:

```
pip install pipx
```

Then repeat the install command above.

### Step 3 — Connect to your Bexio account

You need an API token — think of it as a password that lets this tool talk to Bexio on your behalf.

**Get your token:**
1. Log in to Bexio
2. Go to **Settings → API tokens**
3. Create a new token and copy it

**Save it:**

```
bexio auth login
```

Paste your token when asked. It gets stored securely in your system's password manager (macOS Keychain, Windows Credential Manager, or Linux Secret Service) — you won't need to enter it again.

**Check it's working:**

```
bexio auth status
```

---

## How it works

Every command follows the same pattern:

```
bexio  [what]  [action]  [number or options]
```

For example:
- `bexio invoices list` — show all your invoices
- `bexio invoices show 47` — show details of invoice number 47
- `bexio orders create-invoice 23` — create an invoice from order number 23

**How do I find the number?** Open the item in Bexio in your browser. The number is at the end of the URL — for example `https://office.bexio.com/index.php/kb_invoice/show/id/47` → the number is **47**.

---

## What you can do

### Invoices

```
bexio invoices list                      show all invoices
bexio invoices list --status open        show only open (unpaid) invoices
bexio invoices list --status draft       show only drafts
bexio invoices show 47                   show full details of invoice 47
bexio invoices search "Muster AG"        find invoices by name
bexio invoices create --file body.json   create an invoice from a JSON body
bexio invoices pdf 47                    download invoice 47 as PDF
bexio invoices send 47 --to kunde@firma.ch --subject "Rechnung 47" \
  --message "Guten Tag\n\nIhre Rechnung: [Network Link]"   really emails the recipient
bexio invoices issue 47                  finalize invoice 47
bexio invoices cancel 47                 cancel invoice 47
bexio invoices copy 47                   make a copy of invoice 47
```

`send` really sends an email through Bexio — the recipient is always explicit (`--to`), and
the message must contain the placeholder `[Network Link]`, which Bexio replaces with the link
to the document. Without it the API answers `422` and sends nothing. `--attach-pdf` attaches
the invoice PDF; HTML in `--message` is delivered as HTML, and Bexio adds no header, logo or
footer of its own — the text is entirely yours, which makes per-client templates possible.
Background:
[docs/solutions/integration-issues/kb-invoice-send-requires-body-and-network-placeholder-2026-08-06.md](docs/solutions/integration-issues/kb-invoice-send-requires-body-and-network-placeholder-2026-08-06.md).

Other status filters: `partial` (partially paid), `paid`, `cancelled`

### Orders (Aufträge)

```
bexio orders list                        show all orders
bexio orders list --recurring            show only recurring orders
bexio orders show 23                     show full details of order 23
bexio orders search "Hosting"            find orders by name
bexio orders create --file body.json     create an order from a JSON body
bexio orders create-invoice 23           create an invoice from order 23
bexio orders set-repetition 23 \         set monthly recurrence on order 23
  --start 2026-06-01 --type monthly --schedule fixed_day
bexio orders unset-repetition 23         remove recurrence from order 23
bexio orders pdf 23                      download order 23 as PDF
bexio orders delete 23                   delete order 23
```

`orders create` reads the JSON body from `--file path.json` (or `--file -` for stdin)
and validates it against a Pydantic schema before sending. Invalid payloads (missing
fields, `**markdown**` in HTML text, unknown position types, the `show_position_nr`
field that the API rejects) fail fast with a field-path error.

`orders set-repetition` accepts either explicit flags (`--start`, `--end`, `--type`,
`--interval`, `--schedule`, `--weekdays`) or `--file body.json`. `--schedule` is
required for `--type monthly` and accepts `fixed_day`, `week_day`, `first_day`, or
`last_day`. `--weekdays` is required for `--type weekly` (e.g. `monday,wednesday`).

### Quotes (Offerten)

```
bexio quotes list                        show all quotes
bexio quotes list --status accepted      show only accepted quotes
bexio quotes show 12                     show full details of quote 12
bexio quotes send 12                     send quote 12 by email
bexio quotes accept 12                   mark quote 12 as accepted
bexio quotes decline 12                  mark quote 12 as declined
bexio quotes create-order 12             turn quote 12 into an order
bexio quotes create-invoice 12           turn quote 12 directly into an invoice
bexio quotes pdf 12                      download quote 12 as PDF
```

### Contacts

```
bexio contacts list                      show all contacts
bexio contacts search "Muster"           find contacts by name
bexio contacts show 5                    show full details of contact 5
bexio contacts create --name "Muster AG" --email info@muster.ch
bexio contacts edit 5 --email new@muster.ch
bexio contacts delete 5
```

For a person (not a company), use `--firstname` and `--lastname` instead of `--name`, and add `--type 2`:

```
bexio contacts create --firstname Anna --lastname Muster --phone "+41 44 000 00 00" --type 2
```

### Payments

Record or look up payments on an invoice:

```
bexio payments list 47                   show payments made on invoice 47
bexio payments create 47 --amount 1500.00 --date 2024-03-01
```

### Bills (incoming invoices / Lieferantenrechnungen)

```
bexio bills list                         show all supplier bills
bexio bills show abc-123                 show details of a bill
bexio bills mark-paid abc-123            mark bill as paid
```

### Projects

```
bexio projects list                      show all projects
bexio projects show 20                   show project details
bexio projects create --name "Website Redesign" --contact-id 5
bexio projects archive 20                archive a finished project
```

Milestones and work packages are also available — see the full command list below.

### Time tracking

```
bexio timesheets list                    show all timesheet entries
bexio timesheets create --date 2024-03-15 --duration 02:30 --project-id 20 --text "Client call"
bexio timesheets delete 77
```

### Payment reminders (Mahnungen)

```
bexio reminders list 47                  show reminders for invoice 47
bexio reminders create 47                create a reminder for invoice 47
bexio reminders send 47 30               send reminder 30 (on invoice 47) by email
bexio reminders pdf 47 30                download reminder as PDF
```

### Manual entries (Sammelbuchungen, general ledger)

```
bexio manual-entries list --limit 20                     recent entries
bexio manual-entries list --from 2026-07-01 --to 2026-07-31
bexio manual-entries show 827                            all lines of entry 827
bexio manual-entries create --date 2026-07-01 --reference-nr 702 \
  --line "debit=1030,amount=119.84,currency=CHF,text=Rückerstattung" \
  --line "credit=4450,amount=765.35,currency=BRL,rate=0.157222,tax=Vorsteuer8.1,text=Rückerstattung" \
  --line "debit=6949,amount=0.49,currency=CHF,text=Kursdifferenz"
bexio manual-entries edit 832 --date 2026-08-05            change the date, keep all lines
bexio manual-entries edit 832 --line "..." --line "..."    replace the COMPLETE line set
bexio manual-entries delete 832                            delete (API id, not Beleg number)
```

Line fields: `debit=` **or** `credit=` (account **number**, never the internal id),
`amount=`, `currency=` (default CHF), `rate=` (default 1), `tax=` (tax **code**, e.g.
`Vorsteuer8.1` or `V00` for tax-free), `text=`. Put `text=` last if it contains commas,
or pass `--lines-file entries.json` with the same field names.

Guardrails:

- Debit and credit totals must match — a mismatch prints both sums and the difference, and **nothing is sent**.
- `--reference-nr` is the visible Beleg number (not the API id); an existing one is refused.
- The date is stored verbatim as `YYYY-MM-DD`. The Bexio web UI sometimes *displays* a neighbouring day — the API value is the truth, which matters at a month or quarter boundary.
- Tax codes must be explicit: a tax-free line needs `V00`, it never happens by omission. A sales tax code on an expense account is refused.
- `show`, `edit` and `delete` take the API id and scan recent entries (the v3 API has no single-entry GET) — raise `--limit` for older ones. Pass a Beleg number by mistake and you get told which API id it belongs to, before anything is written.
- **The v3 PUT replaces the whole line set** — verified against the live account on 2026-08-06: sending two of three lines deletes the third. `edit` therefore always writes every line back; `edit --line` means "this is the complete new set". Details: [docs/solutions/integration-issues/manual-entries-put-replaces-lines-2026-08-06.md](docs/solutions/integration-issues/manual-entries-put-replaces-lines-2026-08-06.md).
- Bexio assigns **no** Beleg number by itself — without `--reference-nr` the entry stays without one, and the CLI says so.

### Reference data (taxes, accounts, currencies, etc.)

```
bexio taxes list
bexio accounts list
bexio vat-periods list
bexio currencies list
bexio payment-types list
bexio units list
bexio countries list
```

---

## Common tasks

**Create invoices for all recurring orders at once:**

1. Find your recurring orders: `bexio orders list --recurring`
2. Note the ID numbers in the first column
3. Run `bexio orders create-invoice 23` for each one

Or if you're comfortable with scripting, this does all of them automatically — ask your developer.

**Download all open invoice PDFs:**

1. `bexio invoices list --status open` — note the IDs
2. `bexio invoices pdf 47` — repeat for each ID

---

## Saving results to a file

Add `> filename.txt` after any command to save the output to a text file:

```
bexio invoices list > invoices.txt
```

---

## Getting help

Any command supports `--help` to show what options are available:

```
bexio --help
bexio invoices --help
bexio invoices list --help
```

---

## Use with AI assistants (MCP)

bexio-cli includes an MCP server, which lets AI assistants talk to your Bexio account directly in conversation — no commands to memorize, no clicking.

You can say things like:
- *"Show me all open invoices"*
- *"Create invoices for all recurring orders"*
- *"Log 2.5 hours on project 20 for today"*
- *"Which bills are unpaid this month?"*

The AI figures out which Bexio actions to take and runs them for you.

### Installation with MCP support

Run this one command — it installs bexio-cli and automatically configures every AI tool it finds on your computer:

```
curl -sSL https://raw.githubusercontent.com/noevu/bexio-cli/main/scripts/install_mcp.py | python3
```

Or install manually:

```
pipx install "git+https://github.com/noevu/bexio-cli[mcp]"
```

Then connect it to your AI tool of choice:

---

### Claude Desktop

Config file location:
- **Mac:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "bexio": {
      "command": "bexio-mcp"
    }
  }
}
```

Restart Claude Desktop. Bexio tools appear automatically in the tools panel.

---

### Claude Code (terminal)

```
claude mcp add bexio -s user -- bexio-mcp
```

---

### Gemini CLI

Config file: `~/.gemini/settings.json`

```json
{
  "mcpServers": {
    "bexio": {
      "command": "bexio-mcp",
      "args": []
    }
  }
}
```

---

### Codex CLI (OpenAI)

Config file: `~/.codex/config.toml`

```toml
[mcp_servers.bexio]
type = "stdio"
command = "bexio-mcp"
args = []

[mcp_servers.bexio.env]
```

---

### What the AI can do

50 tools covering invoices, orders, quotes, contacts, payments, items, bills, projects, timesheets, reminders, manual entries (Sammelbuchungen), and accounting reference data. Works with any MCP-compatible AI assistant.

---

## Use as a Python library

The CLI is also a typed Python library. Pydantic v2 models validate every payload
before it leaves your process — same validation as the CLI:

```python
from bexio import Client, KbOrder, KbPositionCustom, OrderRepetition

order = KbOrder(
    contact_id=269, user_id=1,
    title="Service-Paket — example.com",
    header="Hallo Andreas<br /><br />Hier dein laufender Auftrag.",
    positions=[
        KbPositionCustom(
            text="<strong>Grow Service Paket</strong><br />Monthly service",
            unit_price="349.00", amount="1", unit_id=3, tax_id=52,
        ),
    ],
)

client = Client(token="...")
result = client.post("/kb_order", body=order.model_dump(mode="json", exclude_none=True))
order_id = result["id"]

repetition = OrderRepetition.model_validate({
    "start": "2026-06-01", "end": None,
    "repetition": {"type": "monthly", "interval": 1, "schedule": "fixed_day"},
})
client.post(f"/kb_order/{order_id}/repetition",
            body=repetition.model_dump(mode="json"))
```

Available models: `KbOrder`, `KbInvoice`, `OrderRepetition`, `KbPositionCustom`,
`KbPositionDiscount`, `KbPositionItem`, `KbPositionText`, `KbPositionSubtotal`,
`KbPositionPagebreak`, `KbPositionSubposition`. Type aliases: `Position` (the
discriminated union), `RepetitionSpec`, `OrderRepetitionType`, `MonthlySchedule`,
`Weekday`.

## Body quirks (Bexio API)

Things the API silently rejects or surprises you with — already enforced by the
Pydantic models, but worth knowing when authoring JSON bodies by hand:

- **Text fields are HTML, not Markdown.** `header`, `footer`, and position `text`
  on orders/invoices/quotes render as HTML in the PDF. `**bold**` shows up
  literal — use `<strong>...</strong>` and `<br />`. Umlauts as HTML entities
  (`&uuml;`, `&ouml;`, `&auml;`).
- **`show_position_nr` is rejected on `kb_order` POST** (works on `kb_invoice`).
  The `KbOrder` model omits the field; the API returns 422 if you sneak it in.
- **Repetition `schedule` is monthly-only.** Sending `schedule` with `type=daily`,
  `weekly`, or `yearly` returns "Diese Eingabe ist nicht korrekt." Valid values
  for monthly: `fixed_day`, `week_day`, `first_day`, `last_day`.
- **`is_recurring` only flips to `true`** after `POST /kb_order/{id}/repetition`
  succeeds — not by setting it on the order create payload.
- **Recurring orders cannot be deleted** while `is_recurring=true`. Bexio returns
  `403 Forbidden`. Remove the recurrence first with
  `bexio orders unset-repetition <id>` (or `DELETE /kb_order/{id}/repetition`),
  then `bexio orders delete <id>`.
- **Invoice generation mode** for recurring orders (draft vs. auto-send) is
  configured in the Bexio web UI, not via the API.

## For developers

Full command reference, contribution guide, and scripting examples:

```sh
git clone https://github.com/noevu/bexio-cli
cd bexio-cli
pip install -e .
python -m unittest discover -s tests -v
```

The tool is pure Python (stdlib + `keyring` + `pydantic`), no external HTTP
libraries required.

---

## Need help or custom automation?

Need someone to set this up, automate your Bexio workflows, or build custom integrations? [Get in touch with Noevu](https://noevu.ch/en/services/ai-automation) — a Swiss web agency specialising in [AI-powered automation for Swiss SMEs](https://noevu.ch/en/services/ai-automation).

## License

MIT

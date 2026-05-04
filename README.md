# bexio-cli

A tool that lets you control your [Bexio](https://www.bexio.com) account from your computer's Terminal — without clicking through the browser. Great for repetitive tasks, batch operations, and automation.

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
bexio invoices pdf 47                    download invoice 47 as PDF
bexio invoices send 47                   send invoice 47 by email
bexio invoices issue 47                  finalize invoice 47
bexio invoices cancel 47                 cancel invoice 47
bexio invoices copy 47                   make a copy of invoice 47
```

Other status filters: `partial` (partially paid), `paid`, `cancelled`

### Orders (Aufträge)

```
bexio orders list                        show all orders
bexio orders list --recurring            show only recurring orders
bexio orders show 23                     show full details of order 23
bexio orders search "Hosting"            find orders by name
bexio orders create-invoice 23           create an invoice from order 23
bexio orders pdf 23                      download order 23 as PDF
bexio orders delete 23                   delete order 23
```

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

bexio-cli includes an MCP server, which lets AI assistants like Claude talk to your Bexio account directly. You can ask Claude things like:

- *"Show me all open invoices"*
- *"Create invoices for all recurring orders"*
- *"Log 2.5 hours on project 20 for today"*
- *"Which bills are unpaid this month?"*

### Installation with MCP support

```
pipx install "git+https://github.com/noevu/bexio-cli[mcp]"
```

### Connect to Claude Desktop

Add this to your Claude Desktop config file:

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

Restart Claude Desktop. You'll see a Bexio icon in the tools panel. Claude can now read and update your Bexio data in conversation.

### Connect to Claude Code (terminal)

```
claude mcp add bexio -s user -- bexio-mcp
```

### What the AI can do

The MCP server exposes ~35 tools covering invoices, orders, quotes, contacts, payments, items, bills, projects, timesheets, reminders, and accounting reference data. Claude decides which tools to use based on your message — no commands to memorize.

---

## For developers

Full command reference, contribution guide, and scripting examples:

```sh
git clone https://github.com/noevu/bexio-cli
cd bexio-cli
pip install -e .
python -m unittest discover -s tests -v
```

The tool is pure Python (stdlib + `keyring`), no external HTTP libraries required.

---

## Need help or custom automation?

Need someone to set this up, automate your Bexio workflows, or build custom integrations? [Get in touch with Noevu](https://noevu.ch/en/services/ai-automation) — a Swiss web agency specialising in [AI-powered automation for Swiss SMEs](https://noevu.ch/en/services/ai-automation).

## License

MIT

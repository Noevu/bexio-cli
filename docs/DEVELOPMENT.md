# Development Guide

## Package structure

```
bexio/
  cli.py              # argparse wiring + main() entry point
  client.py           # BexioClient — HTTP, multi-version base URLs
  auth.py             # keyring + BEXIO_API_TOKEN env var
  output.py           # print_json(), table()
  models/             # Pydantic v2 payload models (validate before POST)
    _common.py        # shared enums, detect_markdown()
    invoice.py        # KbInvoice
    order.py          # KbOrder, OrderRepetition, position union
    position.py       # KbPositionCustom, KbPositionItem, …, Position (union)
  commands/           # one file per resource group
    invoices.py
    orders.py
    quotes.py
    contacts.py
    payments.py
    items.py
    bills.py
    projects.py       # projects + milestones + work-packages
    reminders.py
    timesheets.py
    lookup.py         # languages, contact-groups, business-activities
    accounts.py       # reference data
    taxes.py
    currencies.py
    payment_types.py
    units.py
    countries.py
  mcp_server.py       # FastMCP server — thin delegation to BexioClient
tests/
  helpers.py          # mock_client(), capture(), capture_with_responses()
  test_*.py
scripts/
  install_mcp.py      # auto-configures AI tools (Claude, Gemini, Codex)
```

## Adding a new command group

### 1. Create `bexio/commands/<resource>.py`

Every command module exports two functions:

```python
def register(sub) -> None:
    """Add subparser to the top-level argparse subparsers."""
    p = sub.add_parser("widgets", help="Widget commands")
    s = p.add_subparsers(dest="action")
    s.add_parser("list", help="List widgets")
    show = s.add_parser("show", help="Show widget")
    show.add_argument("id", type=int)


def handle(args, client: BexioClient, json_flag: bool) -> None:
    """Dispatch to sub-handlers based on args.action."""
    if args.action == "list":
        _list(args, client, json_flag)
    elif args.action == "show":
        _show(args, client, json_flag)
    else:
        sys.exit("Usage: bexio widgets {list|show}")
```

### 2. Register in `bexio/cli.py`

```python
from bexio.commands import widgets  # add to imports

widgets.register(sub)  # add to registration block

# add to the dispatch block:
elif args.resource == "widgets":
    widgets.handle(args, client, args.json)
```

### 3. Add tests

Use `capture_with_responses()` from `tests/helpers.py`:

```python
from tests.helpers import capture_with_responses

def test_list_widgets():
    out = capture_with_responses(["widgets", "list"], [[{"id": 1, "name": "Sprocket"}]])
    assert "Sprocket" in out

def test_show_widget():
    out = capture_with_responses(["widgets", "show", "1"], [{"id": 1, "name": "Sprocket"}])
    assert "Sprocket" in out
```

## API version mapping

`BexioClient` has per-version methods. Pick the right one per resource:

| Version | Base URL | Method | Resources |
|---|---|---|---|
| v2 | `api.bexio.com/2.0` | `get/post/put/delete` | contacts, invoices, orders, quotes, payments, items, projects, timesheets, reminders |
| v3 | `api.bexio.com/3.0` | `get_v3` | project milestones (`/projects/{id}/milestones`), work packages (`/projects/{id}/packages`) |
| v4 | `api.bexio.com/4.0` | `get_v4/post_v4/put_v4/delete_v4` | bills (`/purchase/bills`), bill actions |

PDF download:
```python
pdf_bytes = client.get_pdf(f"/kb_invoice/{id}/pdf")  # returns bytes
with open(path, "wb") as f:
    f.write(pdf_bytes)
```

State transitions (Bexio uses POST with action body, not dedicated endpoints):
```python
client.post(f"/kb_invoice/{id}/issue")
client.post_v4(f"/purchase/bills/{id}/actions", {"action": "mark_as_paid"})
```

## Pydantic models (when to use)

Use models when the command creates or updates a resource with a complex body. Models validate the payload and surface clear field errors before hitting the API.

```python
from bexio.models import KbInvoice

body = json.loads(raw)
try:
    invoice = KbInvoice.model_validate(body)
except Exception as e:
    sys.exit(f"Invalid body:\n{_format_validation_errors(e)}")
payload = invoice.model_dump(mode="json", exclude_none=True)
result = client.post("/kb_invoice", body=payload)
```

`_format_validation_errors()` walks Pydantic's error list and formats field paths.

### Position types

All position lists use the `Position` discriminated union — Pydantic picks the concrete type from the `"type"` field:

| `type` value | Model | Use |
|---|---|---|
| `KbPositionCustom` | `KbPositionCustom` | Free-text line item with price |
| `KbPositionArticle` | `KbPositionItem` | Reference to article catalogue |
| `KbPositionDiscount` | `KbPositionDiscount` | Percentage or flat discount |
| `KbPositionText` | `KbPositionText` | Text block, no price |
| `KbPositionSubtotal` | `KbPositionSubtotal` | Running subtotal line |
| `KbPositionPagebreak` | `KbPositionPagebreak` | PDF page break |
| `KbPositionSubposition` | `KbPositionSubposition` | Grouped sub-positions |

**HTML, not Markdown**: Bexio renders `header`, `footer`, and position `text` as HTML. The models validate and reject `**bold**` — use `<strong>bold</strong>` and `<br />` instead.

### `show_position_nr`

Accepted by `/kb_invoice`, rejected by `/kb_order`. `KbOrder` uses `extra="forbid"` to catch it early.

## Test helpers

`tests/helpers.py` provides three helpers:

```python
# Run CLI end-to-end with mocked _request, return captured stdout
out = capture_with_responses(["invoices", "list"], [[{"id": 1}]])

# Build a client with mocked _request (for unit tests of command handlers)
client = mock_client([{"id": 1}, {"id": 2}])

# Run via main() with full sys.argv + auth mock
out = capture(main, ["invoices", "list"])
```

`capture_with_responses` is the standard. It patches `BexioClient._request` directly, so `base`, `accept`, and other kwargs are transparent to tests.

## Output helpers

```python
from bexio.output import print_json, table

print_json(data)  # json.dumps with indent=2, ensure_ascii=False

table(rows, [
    ("ID",    "id",    6),
    ("Title", "title", 40),
    ("Date",  "date",  12),
])
```

`table()` truncates values to column width. Always offer `--json` / `json_flag` as an escape hatch.

## MCP server

`bexio/mcp_server.py` is a thin wrapper — each `@mcp.tool()` delegates to the same `BexioClient` methods used by the CLI. When you add a CLI command that reads data, consider adding a matching MCP tool.

The MCP server requires the `[mcp]` extra:
```
pipx install "git+https://github.com/noevu/bexio-cli[mcp]"
```

## Running tests

```sh
python -m unittest discover -s tests -v
```

Single file:
```sh
python -m unittest tests.test_invoices -v
```

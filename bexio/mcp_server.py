"""Bexio MCP server — exposes Bexio API as tools for AI assistants (Claude, etc.)."""

import json
from typing import Any

from mcp.server.fastmcp import FastMCP

from bexio.auth import get_token
from bexio.client import BexioClient

mcp = FastMCP("Bexio")
_client: BexioClient | None = None


def _c() -> BexioClient:
    global _client
    if _client is None:
        _client = BexioClient(get_token())
    return _client


def _json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)


# ─── Invoices ────────────────────────────────────────────────────────────────

STATUS_LABELS = {1: "draft", 2: "pending", 3: "billable", 4: "waiting", 7: "sent",
                 8: "partial", 9: "paid", 16: "cancelled", 19: "open"}
STATUS_MAP = {"draft": 1, "open": 19, "sent": 7, "partial": 8, "paid": 9, "cancelled": 16}


@mcp.tool()
def list_invoices(status: str | None = None, limit: int = 100) -> str:
    """List invoices from Bexio. status can be: draft, open, sent, partial, paid, cancelled."""
    params: dict = {"limit": limit}
    if status:
        params["kb_item_status_id"] = STATUS_MAP.get(status, status)
    return _json(_c().get("/kb_invoice", params=params))


@mcp.tool()
def show_invoice(invoice_id: int) -> str:
    """Show full details of a Bexio invoice by its numeric ID."""
    return _json(_c().get(f"/kb_invoice/{invoice_id}"))


@mcp.tool()
def search_invoices(query: str) -> str:
    """Search invoices by title. Returns matching invoices as JSON."""
    body = [{"field": "title", "value": query, "criteria": "like"}]
    return _json(_c().post("/kb_invoice/search", body=body))


@mcp.tool()
def send_invoice(invoice_id: int) -> str:
    """Send an invoice by email to the contact."""
    _c().post(f"/kb_invoice/{invoice_id}/send")
    return f"Invoice {invoice_id} sent."


@mcp.tool()
def issue_invoice(invoice_id: int) -> str:
    """Finalize (issue) a draft invoice, making it official."""
    _c().post(f"/kb_invoice/{invoice_id}/issue")
    return f"Invoice {invoice_id} issued."


@mcp.tool()
def cancel_invoice(invoice_id: int) -> str:
    """Cancel an invoice."""
    _c().post(f"/kb_invoice/{invoice_id}/cancel")
    return f"Invoice {invoice_id} cancelled."


@mcp.tool()
def mark_invoice_as_sent(invoice_id: int) -> str:
    """Mark an invoice as sent without actually sending an email."""
    _c().post(f"/kb_invoice/{invoice_id}/mark_as_sent")
    return f"Invoice {invoice_id} marked as sent."


@mcp.tool()
def get_invoice_pdf(invoice_id: int, output_path: str) -> str:
    """Download an invoice PDF and save it to output_path. Returns the saved path."""
    pdf = _c().get_pdf(f"/kb_invoice/{invoice_id}/pdf")
    with open(output_path, "wb") as f:
        f.write(pdf)
    return f"Invoice {invoice_id} PDF saved to {output_path}."


# ─── Orders ──────────────────────────────────────────────────────────────────

@mcp.tool()
def list_orders(recurring_only: bool = False, limit: int = 100) -> str:
    """List orders (Aufträge) from Bexio. Set recurring_only=True to show only recurring orders."""
    orders = _c().get("/kb_order", params={"limit": limit})
    if recurring_only:
        orders = [o for o in orders if o.get("is_recurring")]
    return _json(orders)


@mcp.tool()
def show_order(order_id: int) -> str:
    """Show full details of a Bexio order including repetition settings."""
    order = _c().get(f"/kb_order/{order_id}")
    rep = _c().get(f"/kb_order/{order_id}/repetition")
    return _json({"order": order, "repetition": rep})


@mcp.tool()
def search_orders(query: str) -> str:
    """Search orders by name."""
    body = [{"field": "name", "value": query, "criteria": "like"}]
    return _json(_c().post("/kb_order/search", body=body))


@mcp.tool()
def create_invoice_from_order(order_id: int) -> str:
    """Create a new invoice from an existing order. Returns the new invoice details."""
    result = _c().post(f"/kb_order/{order_id}/invoice")
    return f"Invoice {result.get('id')} ({result.get('document_nr', '—')}) created from order {order_id}."


# ─── Quotes ──────────────────────────────────────────────────────────────────

QUOTE_STATUS_MAP = {"draft": 1, "sent": 3, "accepted": 7, "declined": 8}


@mcp.tool()
def list_quotes(status: str | None = None, limit: int = 100) -> str:
    """List quotes (Offerten) from Bexio. status can be: draft, sent, accepted, declined."""
    params: dict = {"limit": limit}
    if status:
        params["kb_item_status_id"] = QUOTE_STATUS_MAP.get(status, status)
    return _json(_c().get("/kb_offer", params=params))


@mcp.tool()
def show_quote(quote_id: int) -> str:
    """Show full details of a Bexio quote."""
    return _json(_c().get(f"/kb_offer/{quote_id}"))


@mcp.tool()
def search_quotes(query: str) -> str:
    """Search quotes by title."""
    body = [{"field": "title", "value": query, "criteria": "like"}]
    return _json(_c().post("/kb_offer/search", body=body))


@mcp.tool()
def send_quote(quote_id: int) -> str:
    """Send a quote by email to the contact."""
    _c().post(f"/kb_offer/{quote_id}/send")
    return f"Quote {quote_id} sent."


@mcp.tool()
def accept_quote(quote_id: int) -> str:
    """Mark a quote as accepted."""
    _c().post(f"/kb_offer/{quote_id}/accept")
    return f"Quote {quote_id} accepted."


@mcp.tool()
def decline_quote(quote_id: int) -> str:
    """Mark a quote as declined."""
    _c().post(f"/kb_offer/{quote_id}/reject")
    return f"Quote {quote_id} declined."


@mcp.tool()
def create_order_from_quote(quote_id: int) -> str:
    """Convert an accepted quote into an order."""
    result = _c().post(f"/kb_offer/{quote_id}/order")
    return f"Order {result.get('id')} created from quote {quote_id}."


# ─── Contacts ────────────────────────────────────────────────────────────────

@mcp.tool()
def list_contacts(limit: int = 100) -> str:
    """List all contacts in Bexio."""
    return _json(_c().get("/contact", params={"limit": limit}))


@mcp.tool()
def show_contact(contact_id: int) -> str:
    """Show full details of a Bexio contact."""
    return _json(_c().get(f"/contact/{contact_id}"))


@mcp.tool()
def search_contacts(query: str) -> str:
    """Search contacts by name, company name, or email."""
    body = [{"field": "name_1", "value": query, "criteria": "like"}]
    return _json(_c().post("/contact/search", body=body))


@mcp.tool()
def create_contact(
    name: str | None = None,
    email: str | None = None,
    phone: str | None = None,
    firstname: str | None = None,
    lastname: str | None = None,
    contact_type_id: int = 1,
) -> str:
    """Create a new Bexio contact. contact_type_id: 1=company, 2=person.
    For a company use name. For a person use firstname + lastname."""
    body: dict = {"contact_type_id": contact_type_id}
    if name:
        body["name_1"] = name
    if firstname:
        body["name_1"] = firstname
    if lastname:
        body["name_2"] = lastname
    if email:
        body["mail"] = email
    if phone:
        body["phone_fixed"] = phone
    result = _c().post("/contact", body=body)
    return f"Contact {result.get('id')} created."


# ─── Payments ────────────────────────────────────────────────────────────────

@mcp.tool()
def list_payments(invoice_id: int) -> str:
    """List all payments recorded against an invoice."""
    return _json(_c().get(f"/kb_invoice/{invoice_id}/payment"))


@mcp.tool()
def create_payment(invoice_id: int, amount: float, date: str, payment_type_id: int | None = None) -> str:
    """Record a payment on an invoice. date format: YYYY-MM-DD."""
    body: dict = {"value": str(amount), "date": date}
    if payment_type_id is not None:
        body["payment_type_id"] = payment_type_id
    result = _c().post(f"/kb_invoice/{invoice_id}/payment", body=body)
    return f"Payment {result.get('id')} of {amount} recorded on invoice {invoice_id}."


# ─── Items / Products ────────────────────────────────────────────────────────

@mcp.tool()
def list_items(limit: int = 100) -> str:
    """List products/items (Artikel) in Bexio."""
    return _json(_c().get("/article", params={"limit": limit}))


@mcp.tool()
def show_item(item_id: int) -> str:
    """Show full details of a product/item."""
    return _json(_c().get(f"/article/{item_id}"))


@mcp.tool()
def search_items(query: str) -> str:
    """Search products/items by name."""
    body = [{"field": "intern_name", "value": query, "criteria": "like"}]
    return _json(_c().post("/article/search", body=body))


# ─── Bills ───────────────────────────────────────────────────────────────────

@mcp.tool()
def list_bills(limit: int = 100) -> str:
    """List supplier bills (Lieferantenrechnungen) from Bexio."""
    return _json(_c().get_v4("/purchase/bills", params={"limit": limit}))


@mcp.tool()
def show_bill(bill_id: str) -> str:
    """Show full details of a supplier bill. bill_id is a UUID string."""
    return _json(_c().get_v4(f"/purchase/bills/{bill_id}"))


@mcp.tool()
def mark_bill_paid(bill_id: str) -> str:
    """Mark a supplier bill as paid."""
    _c().post_v4(f"/purchase/bills/{bill_id}/actions", body={"action": "mark_as_paid"})
    return f"Bill {bill_id} marked as paid."


# ─── Projects ────────────────────────────────────────────────────────────────

@mcp.tool()
def list_projects(limit: int = 100) -> str:
    """List all projects in Bexio."""
    return _json(_c().get("/pr_project", params={"limit": limit}))


@mcp.tool()
def show_project(project_id: int) -> str:
    """Show full details of a project."""
    return _json(_c().get(f"/pr_project/{project_id}"))


@mcp.tool()
def search_projects(query: str) -> str:
    """Search projects by name."""
    body = [{"field": "name", "value": query, "criteria": "like"}]
    return _json(_c().post("/pr_project/search", body=body))


@mcp.tool()
def list_milestones(project_id: int) -> str:
    """List all milestones for a project."""
    return _json(_c().get_v3(f"/projects/{project_id}/milestones"))


@mcp.tool()
def list_work_packages(project_id: int) -> str:
    """List all work packages for a project."""
    return _json(_c().get_v3(f"/projects/{project_id}/packages"))


# ─── Timesheets ──────────────────────────────────────────────────────────────

@mcp.tool()
def list_timesheets(limit: int = 100) -> str:
    """List timesheet entries from Bexio."""
    return _json(_c().get("/timesheet", params={"limit": limit}))


@mcp.tool()
def show_timesheet(timesheet_id: int) -> str:
    """Show full details of a timesheet entry."""
    return _json(_c().get(f"/timesheet/{timesheet_id}"))


@mcp.tool()
def create_timesheet(
    date: str,
    duration: str,
    project_id: int | None = None,
    text: str | None = None,
    user_id: int | None = None,
) -> str:
    """Log time in Bexio. date: YYYY-MM-DD, duration: HH:MM (e.g. 02:30)."""
    body: dict = {"tracking": {"type": "duration", "date": date, "duration": duration}}
    if project_id is not None:
        body["pr_project_id"] = project_id
    if text:
        body["text"] = text
    if user_id is not None:
        body["user_id"] = user_id
    result = _c().post("/timesheet", body=body)
    return f"Timesheet {result.get('id')} created: {duration} on {date}."


# ─── Reference data ──────────────────────────────────────────────────────────

@mcp.tool()
def list_taxes() -> str:
    """List all tax rates configured in Bexio."""
    return _json(_c().get_v3("/taxes"))


@mcp.tool()
def list_accounts() -> str:
    """List all accounting accounts (Konten) in Bexio."""
    return _json(_c().get("/accounts"))


@mcp.tool()
def list_currencies() -> str:
    """List all currencies configured in Bexio."""
    return _json(_c().get_v3("/currencies"))


@mcp.tool()
def list_payment_types() -> str:
    """List all payment types (e.g. bank transfer, cash) in Bexio."""
    return _json(_c().get("/payment_type"))


@mcp.tool()
def list_vat_periods() -> str:
    """List VAT settlement periods in Bexio."""
    return _json(_c().get_v3("/accounting/vat_period"))


# ─── Reminders ───────────────────────────────────────────────────────────────

@mcp.tool()
def list_reminders(invoice_id: int) -> str:
    """List payment reminders (Mahnungen) for an invoice."""
    return _json(_c().get(f"/kb_invoice/{invoice_id}/kb_reminder"))


@mcp.tool()
def create_reminder(invoice_id: int, title: str | None = None) -> str:
    """Create a payment reminder for an invoice."""
    body: dict = {}
    if title:
        body["title"] = title
    result = _c().post(f"/kb_invoice/{invoice_id}/kb_reminder", body=body)
    return f"Reminder {result.get('id')} created for invoice {invoice_id}."


@mcp.tool()
def send_reminder(invoice_id: int, reminder_id: int) -> str:
    """Send a payment reminder by email."""
    _c().post(f"/kb_invoice/{invoice_id}/kb_reminder/{reminder_id}/send")
    return f"Reminder {reminder_id} sent."


# ─── Entry point ─────────────────────────────────────────────────────────────

def run() -> None:
    mcp.run()


if __name__ == "__main__":
    run()

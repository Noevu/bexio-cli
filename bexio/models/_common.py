"""Shared Bexio enums + scalar types."""

from typing import Literal

# `mwst_type`:
#   0 = tax exclusive (net + tax shown separately)
#   1 = tax inclusive (gross, tax included)
#   2 = no tax
MwstType = Literal[0, 1, 2]

# `language_id`: 1=DE, 2=FR, 3=EN, 4=IT
LanguageId = Literal[1, 2, 3, 4]

# `currency_id`: 1=CHF (most common). Other IDs exist per tenant; left as int elsewhere.
CurrencyId = int

# Bexio rejects this field on /kb_order POST (works on /kb_invoice).
# Models exclude it via `extra="forbid"`.
KB_ORDER_BANNED_FIELDS = frozenset({"show_position_nr"})


def detect_markdown(value: str | None, field_name: str) -> str | None:
    """Return human-readable warning if `value` looks like Markdown bold.

    Bexio renders header/footer/position text as HTML — `**bold**` shows up literal.
    Returns the warning string, or None if clean.
    """
    if not isinstance(value, str):
        return None
    if "**" in value:
        return (
            f"{field_name!r} contains '**' — Bexio renders text as HTML, not Markdown. "
            f"Use <strong>...</strong> for bold and <br /> for line breaks."
        )
    return None

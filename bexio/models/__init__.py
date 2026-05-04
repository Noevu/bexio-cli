"""Pydantic v2 models for Bexio API payloads.

Validate at the CLI/library boundary so malformed bodies fail fast with
clear field-path errors. Models also serve as the typed Python library API:

    from bexio import KbOrder, OrderRepetition, KbPositionCustom

    order = KbOrder(
        contact_id=269, user_id=1, title="...",
        positions=[KbPositionCustom(text="<strong>...</strong>", unit_price="349.00")],
    )
"""

from .invoice import KbInvoice
from .order import (
    KbOrder,
    MonthlySchedule,
    OrderRepetition,
    OrderRepetitionType,
    RepetitionSpec,
    Weekday,
)
from .position import (
    KbPositionCustom,
    KbPositionDiscount,
    KbPositionItem,
    KbPositionPagebreak,
    KbPositionSubposition,
    KbPositionSubtotal,
    KbPositionText,
    Position,
)

__all__ = [
    "KbInvoice",
    "KbOrder",
    "KbPositionCustom",
    "KbPositionDiscount",
    "KbPositionItem",
    "KbPositionPagebreak",
    "KbPositionSubposition",
    "KbPositionSubtotal",
    "KbPositionText",
    "MonthlySchedule",
    "OrderRepetition",
    "OrderRepetitionType",
    "Position",
    "RepetitionSpec",
    "Weekday",
]

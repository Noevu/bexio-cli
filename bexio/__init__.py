"""bexio-cli — Command-line interface and Python library for the Bexio API.

CLI:
    bexio orders create --file body.json
    bexio orders set-repetition 50 --start 2026-06-01 --type monthly --schedule fixed_day
    bexio invoices create --file body.json

Library:
    from bexio import Client, KbOrder, KbPositionCustom, OrderRepetition

    order = KbOrder(
        contact_id=269, user_id=1, title="Service-Paket",
        positions=[KbPositionCustom(text="<strong>Item</strong><br />Desc",
                                    unit_price="349.00")],
    )
    client = Client(token=...)
    result = client.post("/kb_order", body=order.model_dump(mode="json", exclude_none=True))
"""

from .client import BexioClient as Client
from .models import (
    KbInvoice,
    KbOrder,
    KbPositionCustom,
    KbPositionDiscount,
    KbPositionItem,
    KbPositionPagebreak,
    KbPositionSubposition,
    KbPositionSubtotal,
    KbPositionText,
    MonthlySchedule,
    OrderRepetition,
    OrderRepetitionType,
    Position,
    RepetitionSpec,
    Weekday,
)

__version__ = "0.2.0"

__all__ = [
    "Client",
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
    "__version__",
]

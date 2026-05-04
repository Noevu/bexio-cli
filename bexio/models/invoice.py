"""Bexio Rechnung (kb_invoice) model."""

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator

from ._common import CurrencyId, LanguageId, MwstType, detect_markdown
from .position import Position


class KbInvoice(BaseModel):
    """Invoice payload for POST /2.0/kb_invoice.

    Forbids unknown extras. Field validators block Markdown bold in HTML
    text fields.
    """

    model_config = ConfigDict(extra="forbid")

    contact_id: int
    contact_sub_id: int | None = None
    user_id: int
    pr_project_id: int | None = None
    title: str
    header: str | None = None
    footer: str | None = None

    mwst_type: MwstType = 0
    mwst_is_net: bool = True
    show_position_nr: bool | None = None  # accepted on /kb_invoice (unlike /kb_order)

    is_valid_from: str  # YYYY-MM-DD — required
    is_valid_to: str | None = None  # YYYY-MM-DD — due date
    language_id: LanguageId = 1
    bank_account_id: int | None = None
    currency_id: CurrencyId = 1
    payment_type_id: int | None = None
    template_slug: str | None = None
    api_reference: str | None = None

    positions: list[Position] = Field(default_factory=list)

    @field_validator("header", "footer")
    @classmethod
    def _no_markdown(cls, v: str | None, info: ValidationInfo) -> str | None:
        if v is None:
            return v
        warning = detect_markdown(v, info.field_name)
        if warning:
            raise ValueError(warning)
        return v

"""Bexio position models — discriminated union on `type`.

Mirrors Bexio's KbPosition* polymorphism. Use `Position` (the union) anywhere a
positions list is expected; pydantic picks the right concrete model from the
`type` discriminator.
"""

from typing import Annotated, Literal, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ._common import detect_markdown


class _PositionBase(BaseModel):
    model_config = ConfigDict(extra="allow")  # Bexio adds read-only fields on GET


class KbPositionCustom(_PositionBase):
    """Free-text line item with price + quantity."""

    type: Literal["KbPositionCustom"] = "KbPositionCustom"
    text: str = Field(..., description="HTML — first line in <strong> as title, then <br /> + description.")
    amount: str | float = "1"
    unit_id: int | None = None
    unit_price: str | float
    discount_in_percent: str | float = "0"
    tax_id: int | None = None
    account_id: int | None = None

    @field_validator("text")
    @classmethod
    def _no_markdown(cls, v: str) -> str:
        warning = detect_markdown(v, "text")
        if warning:
            raise ValueError(warning)
        return v


class KbPositionItem(_PositionBase):
    """Reference to an existing item from the article catalogue."""

    type: Literal["KbPositionArticle"] = "KbPositionArticle"
    article_id: int
    amount: str | float = "1"
    unit_id: int | None = None
    unit_price: str | float | None = None  # falls back to article default
    discount_in_percent: str | float = "0"
    tax_id: int | None = None
    account_id: int | None = None
    text: str | None = None  # override item description


class KbPositionDiscount(_PositionBase):
    """Discount applied to all preceding positions."""

    type: Literal["KbPositionDiscount"] = "KbPositionDiscount"
    text: str
    is_percentual: bool = True
    value: str | float


class KbPositionText(_PositionBase):
    """Text-only block (no price)."""

    type: Literal["KbPositionText"] = "KbPositionText"
    text: str
    show_pos_nr: bool = False

    @field_validator("text")
    @classmethod
    def _no_markdown(cls, v: str) -> str:
        warning = detect_markdown(v, "text")
        if warning:
            raise ValueError(warning)
        return v


class KbPositionSubtotal(_PositionBase):
    """Subtotal line."""

    type: Literal["KbPositionSubtotal"] = "KbPositionSubtotal"
    text: str | None = None


class KbPositionPagebreak(_PositionBase):
    """Force a page break in the PDF."""

    type: Literal["KbPositionPagebreak"] = "KbPositionPagebreak"


class KbPositionSubposition(_PositionBase):
    """Container holding nested positions."""

    type: Literal["KbPositionSubposition"] = "KbPositionSubposition"
    text: str | None = None
    show_pos_nr: bool = False


Position = Annotated[
    Union[
        KbPositionCustom,
        KbPositionItem,
        KbPositionDiscount,
        KbPositionText,
        KbPositionSubtotal,
        KbPositionPagebreak,
        KbPositionSubposition,
    ],
    Field(discriminator="type"),
]

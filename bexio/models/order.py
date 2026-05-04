"""Bexio Auftrag (kb_order) models + repetition spec."""

from typing import Annotated, Literal, Union

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator, model_validator

from ._common import CurrencyId, LanguageId, MwstType, detect_markdown
from .position import Position

OrderRepetitionType = Literal["daily", "weekly", "monthly", "yearly"]
MonthlySchedule = Literal["fixed_day", "week_day", "first_day", "last_day"]
Weekday = Literal["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


class KbOrder(BaseModel):
    """Sales order (Auftrag) payload for POST /2.0/kb_order.

    Forbids unknown extras — `show_position_nr` is rejected by the API on this
    endpoint (works on /kb_invoice). Field validators block Markdown bold in
    HTML text fields.
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

    is_valid_from: str | None = None  # YYYY-MM-DD
    language_id: LanguageId = 1
    bank_account_id: int | None = None
    currency_id: CurrencyId = 1
    payment_type_id: int | None = None
    template_slug: str | None = None
    delivery_address_type: int | None = None

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


class _DailyRepetition(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["daily"] = "daily"
    interval: int = Field(ge=1)


class _WeeklyRepetition(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["weekly"] = "weekly"
    interval: int = Field(ge=1)
    weekdays: list[Weekday] = Field(min_length=1)


class _MonthlyRepetition(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["monthly"] = "monthly"
    interval: int = Field(ge=1)
    schedule: MonthlySchedule


class _YearlyRepetition(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["yearly"] = "yearly"
    interval: int = Field(ge=1)


RepetitionSpec = Annotated[
    Union[_DailyRepetition, _WeeklyRepetition, _MonthlyRepetition, _YearlyRepetition],
    Field(discriminator="type"),
]


class OrderRepetition(BaseModel):
    """Recurrence settings for POST /2.0/kb_order/{id}/repetition."""

    model_config = ConfigDict(extra="forbid")

    start: str  # YYYY-MM-DD
    end: str | None = None  # YYYY-MM-DD or None for indefinite
    repetition: RepetitionSpec

    @model_validator(mode="after")
    def _check_dates(self):
        if self.end and self.end < self.start:
            raise ValueError("end date is before start date")
        return self

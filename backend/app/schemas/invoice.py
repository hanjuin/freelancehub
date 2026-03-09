from __future__ import annotations

import sys
from datetime import date, datetime
from pathlib import Path
import uuid

_PROJECT_ROOT = str(Path(__file__).resolve().parents[4])
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from models import InvoiceStatus  # noqa: E402

from pydantic import BaseModel, ConfigDict, Field


class InvoiceLineItemBase(BaseModel):
    description: str = Field(max_length=500)
    quantity: float = Field(default=1.0, gt=0)
    unit_price_cents: int
    discount_percent: float = Field(default=0.0, ge=0, le=100)
    sort_order: int = 0


class InvoiceLineItemCreate(InvoiceLineItemBase):
    pass


class InvoiceLineItemUpdate(BaseModel):
    description: str | None = Field(default=None, max_length=500)
    quantity: float | None = Field(default=None, gt=0)
    unit_price_cents: int | None = None
    discount_percent: float | None = Field(default=None, ge=0, le=100)
    sort_order: int | None = None


class InvoiceLineItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    invoice_id: uuid.UUID
    description: str
    quantity: float
    unit_price_cents: int
    discount_percent: float
    line_total_cents: int
    sort_order: int


class InvoiceBase(BaseModel):
    customer_id: uuid.UUID
    booking_id: uuid.UUID | None = None
    issue_date: date
    due_date: date | None = None
    notes: str | None = None
    payment_terms: str | None = None


class InvoiceCreate(InvoiceBase):
    line_items: list[InvoiceLineItemCreate]


class InvoiceUpdate(BaseModel):
    status: InvoiceStatus | None = None
    notes: str | None = None
    paid_at: datetime | None = None
    due_date: date | None = None
    payment_terms: str | None = None
    line_items: list[InvoiceLineItemCreate] | None = None


class InvoiceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    freelancer_id: uuid.UUID
    customer_id: uuid.UUID
    booking_id: uuid.UUID | None
    invoice_number: str
    issue_date: date
    due_date: date | None
    status: InvoiceStatus
    sent_at: datetime | None
    paid_at: datetime | None
    subtotal_cents: int
    discount_cents: int
    tax_rate_bps: int
    tax_cents: int
    total_cents: int
    notes: str | None
    payment_terms: str | None
    line_items: list[InvoiceLineItemResponse]
    created_at: datetime
    updated_at: datetime

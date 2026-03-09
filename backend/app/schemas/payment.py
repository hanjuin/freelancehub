from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
import uuid

_PROJECT_ROOT = str(Path(__file__).resolve().parents[4])
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from models import PaymentMethod, PaymentStatus  # noqa: E402

from pydantic import BaseModel, ConfigDict, Field


class PaymentCreate(BaseModel):
    invoice_id: uuid.UUID
    amount_cents: int = Field(gt=0)
    method: PaymentMethod
    paid_at: datetime
    reference: str | None = Field(default=None, max_length=255)
    notes: str | None = Field(default=None, max_length=500)
    gateway_payment_id: str | None = Field(default=None, max_length=255)


class PaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    invoice_id: uuid.UUID
    freelancer_id: uuid.UUID
    amount_cents: int
    method: PaymentMethod
    status: PaymentStatus
    paid_at: datetime
    reference: str | None
    notes: str | None
    gateway_payment_id: str | None
    created_at: datetime
    updated_at: datetime

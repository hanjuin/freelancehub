from __future__ import annotations

import sys
from datetime import date, datetime, time
from pathlib import Path
import uuid

_PROJECT_ROOT = str(Path(__file__).resolve().parents[4])
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from models import BookingStatus, RecurringFrequency  # noqa: E402

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class BookingBase(BaseModel):
    service_id: uuid.UUID
    staff_member_id: uuid.UUID | None = None
    start_time: datetime
    customer_notes: str | None = None


class BookingCreate(BookingBase):
    customer_id: uuid.UUID
    custom_answers: list[dict] | None = None


class BookingUpdate(BaseModel):
    status: BookingStatus | None = None
    internal_notes: str | None = None
    staff_member_id: uuid.UUID | None = None


class BookingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    freelancer_id: uuid.UUID
    customer_id: uuid.UUID
    service_id: uuid.UUID
    staff_member_id: uuid.UUID | None
    recurring_rule_id: uuid.UUID | None
    start_time: datetime
    end_time: datetime
    duration_minutes: int
    status: BookingStatus
    price_cents: int
    cancel_token: str
    customer_notes: str | None
    internal_notes: str | None
    cancellation_reason: str | None
    cancelled_by: str | None
    reminder_24h_sent: bool
    reminder_2h_sent: bool
    created_at: datetime
    updated_at: datetime


class BookingStatusUpdate(BaseModel):
    status: BookingStatus
    cancellation_reason: str | None = None


class PublicBookingCreate(BaseModel):
    service_id: uuid.UUID
    staff_member_id: uuid.UUID | None = None
    start_time: datetime
    first_name: str = Field(max_length=100)
    last_name: str | None = Field(default=None, max_length=100)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=30)
    customer_notes: str | None = None
    custom_answers: list[dict] | None = None


class WaitlistEntryCreate(BaseModel):
    service_id: uuid.UUID
    requested_date: date
    guest_name: str | None = Field(default=None, max_length=200)
    guest_email: str | None = None
    guest_phone: str | None = Field(default=None, max_length=30)
    customer_id: uuid.UUID | None = None


class WaitlistEntryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    freelancer_id: uuid.UUID
    service_id: uuid.UUID
    customer_id: uuid.UUID | None
    guest_name: str | None
    guest_email: str | None
    guest_phone: str | None
    requested_date: date
    is_notified: bool
    is_booked: bool
    created_at: datetime


class RecurringRuleCreate(BaseModel):
    customer_id: uuid.UUID
    service_id: uuid.UUID
    staff_member_id: uuid.UUID | None = None
    frequency: RecurringFrequency
    preferred_time: time
    start_date: date
    end_date: date | None = None


class RecurringRuleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    freelancer_id: uuid.UUID
    customer_id: uuid.UUID
    service_id: uuid.UUID
    staff_member_id: uuid.UUID | None
    frequency: RecurringFrequency
    preferred_time: time
    start_date: date
    end_date: date | None
    is_active: bool
    last_generated_date: date | None
    created_at: datetime
    updated_at: datetime

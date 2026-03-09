from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class FreelancerSettingsUpdate(BaseModel):
    logo_url: str | None = Field(default=None, max_length=500)
    accent_color: str | None = Field(default=None, max_length=7)
    booking_page_headline: str | None = Field(default=None, max_length=255)
    booking_page_description: str | None = None
    tax_name: str | None = Field(default=None, max_length=50)
    tax_rate_bps: int | None = Field(default=None, ge=0)
    tax_number: str | None = Field(default=None, max_length=50)
    invoice_prefix: str | None = Field(default=None, max_length=10)
    invoice_footer: str | None = None
    payment_terms_days: int | None = Field(default=None, ge=0)
    booking_advance_days: int | None = Field(default=None, ge=1)
    cancellation_window_hours: int | None = Field(default=None, ge=0)
    auto_confirm_bookings: bool | None = None
    max_bookings_per_day: int | None = Field(default=None, ge=1)


class FreelancerSettingsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    freelancer_id: uuid.UUID
    logo_url: str | None
    accent_color: str | None
    booking_page_headline: str | None
    booking_page_description: str | None
    tax_name: str | None
    tax_rate_bps: int
    tax_number: str | None
    invoice_prefix: str
    invoice_footer: str | None
    payment_terms_days: int
    invoice_sequence: int
    booking_advance_days: int
    cancellation_window_hours: int
    auto_confirm_bookings: bool
    max_bookings_per_day: int | None
    stripe_account_id: str | None
    stripe_onboarding_complete: bool
    google_calendar_id: str | None
    created_at: datetime
    updated_at: datetime


class NotificationPreferencesUpdate(BaseModel):
    email_new_booking: bool | None = None
    email_booking_cancelled: bool | None = None
    email_booking_reminder: bool | None = None
    email_invoice_paid: bool | None = None
    email_invoice_overdue: bool | None = None
    email_new_review: bool | None = None
    inapp_new_booking: bool | None = None
    inapp_booking_cancelled: bool | None = None
    inapp_invoice_paid: bool | None = None
    inapp_new_review: bool | None = None
    sms_enabled: bool | None = None
    sms_new_booking: bool | None = None
    sms_booking_reminder: bool | None = None


class NotificationPreferencesResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    freelancer_id: uuid.UUID
    email_new_booking: bool
    email_booking_cancelled: bool
    email_booking_reminder: bool
    email_invoice_paid: bool
    email_invoice_overdue: bool
    email_new_review: bool
    inapp_new_booking: bool
    inapp_booking_cancelled: bool
    inapp_invoice_paid: bool
    inapp_new_review: bool
    sms_enabled: bool
    sms_new_booking: bool
    sms_booking_reminder: bool
    created_at: datetime
    updated_at: datetime

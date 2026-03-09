"""
FreelanceHub — SQLAlchemy ORM Models
=====================================
Database: PostgreSQL 16
ORM:      SQLAlchemy 2.x (async, declarative)
Naming:   snake_case tables, plural names
Currency: All monetary values stored as INTEGER (cents) to avoid float rounding.
Datetime: All timestamps stored as UTC (timezone=True).

Table index
-----------
  Core / Auth
    freelancers              — tenant accounts (one per business)
    refresh_tokens           — JWT refresh token store
    password_reset_tokens    — one-time password reset OTPs

  Business Setup
    service_categories       — barber, plumber, electrician … (seed + custom)
    services                 — freelancer's service catalogue
    staff_members            — team members under a freelancer account
    working_hours            — weekly schedule (per freelancer or staff member)
    blocked_dates            — holidays, one-off unavailability

  Customers (CRM)
    customers                — per-freelancer customer records
    customer_tags            — normalised tag list
    customer_tag_assignments — M2M: customers ↔ tags

  Bookings
    bookings                 — core appointment record
    booking_custom_answers   — answers to freelancer's custom form questions
    booking_form_fields      — custom questions per freelancer / service
    waitlist_entries         — customers waiting for a cancelled slot
    recurring_booking_rules  — rules for repeat appointments

  Invoicing
    invoices                 — billing documents
    invoice_line_items       — line items within an invoice
    payments                 — payment records against invoices

  Reviews
    reviews                  — post-appointment customer reviews

  Notifications
    notifications            — in-app notification log

  Settings / Config
    freelancer_settings      — per-freelancer config (tax, branding, prefs)
    notification_preferences — which email/in-app events the freelancer receives
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime, time

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    Time,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------

class Base(DeclarativeBase):
    """Shared base: UUID primary key + audit timestamps on every table."""

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class DayOfWeek(str, enum.Enum):
    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"


class BookingStatus(str, enum.Enum):
    PENDING = "pending"         # Awaiting freelancer confirmation
    CONFIRMED = "confirmed"     # Confirmed by freelancer
    COMPLETED = "completed"     # Service delivered
    CANCELLED = "cancelled"     # Cancelled by either party
    NO_SHOW = "no_show"         # Customer did not attend


class InvoiceStatus(str, enum.Enum):
    DRAFT = "draft"
    SENT = "sent"
    PAID = "paid"
    OVERDUE = "overdue"
    VOID = "void"


class PaymentMethod(str, enum.Enum):
    CASH = "cash"
    BANK_TRANSFER = "bank_transfer"
    STRIPE = "stripe"
    PAYPAL = "paypal"
    OTHER = "other"


class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class RecurringFrequency(str, enum.Enum):
    WEEKLY = "weekly"
    FORTNIGHTLY = "fortnightly"
    MONTHLY = "monthly"


class NotificationType(str, enum.Enum):
    BOOKING_NEW = "booking_new"
    BOOKING_CONFIRMED = "booking_confirmed"
    BOOKING_CANCELLED = "booking_cancelled"
    BOOKING_REMINDER = "booking_reminder"
    BOOKING_COMPLETED = "booking_completed"
    INVOICE_SENT = "invoice_sent"
    INVOICE_PAID = "invoice_paid"
    INVOICE_OVERDUE = "invoice_overdue"
    REVIEW_RECEIVED = "review_received"
    WAITLIST_SLOT_AVAILABLE = "waitlist_slot_available"


class FormFieldType(str, enum.Enum):
    TEXT = "text"
    TEXTAREA = "textarea"
    SELECT = "select"
    CHECKBOX = "checkbox"
    PHONE = "phone"


class StorageBackend(str, enum.Enum):
    LOCAL = "local"
    S3 = "s3"


# ---------------------------------------------------------------------------
# Core / Auth
# ---------------------------------------------------------------------------

class Freelancer(Base):
    """
    Primary tenant account. One record per freelancer / business.

    Multi-tenancy note:
        Every other model that is "owned" by a freelancer carries a
        freelancer_id FK. All queries MUST filter by this column.
    """
    __tablename__ = "freelancers"

    # --- Auth ---
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    email_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # --- Identity ---
    username: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True,
        comment="Used in public booking URL: freelancehub.app/{username}",
    )
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(30))
    avatar_url: Mapped[str | None] = mapped_column(String(500))

    # --- Business ---
    business_name: Mapped[str | None] = mapped_column(String(200))
    bio: Mapped[str | None] = mapped_column(Text)
    address_line1: Mapped[str | None] = mapped_column(String(255))
    address_line2: Mapped[str | None] = mapped_column(String(255))
    city: Mapped[str | None] = mapped_column(String(100))
    state: Mapped[str | None] = mapped_column(String(100))
    postcode: Mapped[str | None] = mapped_column(String(20))
    country: Mapped[str] = mapped_column(String(2), default="AU", nullable=False,
                                         comment="ISO 3166-1 alpha-2")
    timezone: Mapped[str] = mapped_column(String(50), default="UTC", nullable=False,
                                          comment="IANA timezone, e.g. Australia/Sydney")
    currency: Mapped[str] = mapped_column(String(3), default="AUD", nullable=False,
                                          comment="ISO 4217 currency code")

    # --- Category ---
    service_category_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("service_categories.id", ondelete="SET NULL")
    )

    # --- OAuth ---
    google_oauth_id: Mapped[str | None] = mapped_column(String(255), unique=True)

    # --- Relationships ---
    service_category: Mapped["ServiceCategory | None"] = relationship(
        back_populates="freelancers", foreign_keys=[service_category_id]
    )
    services: Mapped[list["Service"]] = relationship(back_populates="freelancer", cascade="all, delete-orphan")
    staff_members: Mapped[list["StaffMember"]] = relationship(back_populates="freelancer", cascade="all, delete-orphan")
    working_hours: Mapped[list["WorkingHours"]] = relationship(back_populates="freelancer", cascade="all, delete-orphan")
    blocked_dates: Mapped[list["BlockedDate"]] = relationship(back_populates="freelancer", cascade="all, delete-orphan")
    customers: Mapped[list["Customer"]] = relationship(back_populates="freelancer", cascade="all, delete-orphan")
    bookings: Mapped[list["Booking"]] = relationship(back_populates="freelancer", cascade="all, delete-orphan")
    invoices: Mapped[list["Invoice"]] = relationship(back_populates="freelancer", cascade="all, delete-orphan")
    notifications: Mapped[list["Notification"]] = relationship(back_populates="freelancer", cascade="all, delete-orphan")
    settings: Mapped["FreelancerSettings | None"] = relationship(back_populates="freelancer", uselist=False, cascade="all, delete-orphan")
    notification_preferences: Mapped["NotificationPreferences | None"] = relationship(back_populates="freelancer", uselist=False, cascade="all, delete-orphan")
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(back_populates="freelancer", cascade="all, delete-orphan")
    booking_form_fields: Mapped[list["BookingFormField"]] = relationship(back_populates="freelancer", cascade="all, delete-orphan")
    customer_tags: Mapped[list["CustomerTag"]] = relationship(back_populates="freelancer", cascade="all, delete-orphan")
    reviews: Mapped[list["Review"]] = relationship(back_populates="freelancer", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("char_length(username) >= 3", name="ck_freelancer_username_min_length"),
    )


class RefreshToken(Base):
    """
    Stored refresh tokens for JWT rotation.
    On every token refresh, old token is marked used and a new one is issued.
    """
    __tablename__ = "refresh_tokens"

    freelancer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("freelancers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    token_hash: Mapped[str] = mapped_column(String(255), unique=True, nullable=False,
                                             comment="SHA-256 hash of the raw token")
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    user_agent: Mapped[str | None] = mapped_column(String(500))
    ip_address: Mapped[str | None] = mapped_column(String(45), comment="IPv4 or IPv6")

    freelancer: Mapped["Freelancer"] = relationship(back_populates="refresh_tokens")


class PasswordResetToken(Base):
    """Short-lived OTP for password reset flow."""
    __tablename__ = "password_reset_tokens"

    freelancer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("freelancers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    token_hash: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


# ---------------------------------------------------------------------------
# Business Setup
# ---------------------------------------------------------------------------

class ServiceCategory(Base):
    """
    Lookup table of freelancer types.
    Seeded with common categories; freelancers can also create custom ones.
    """
    __tablename__ = "service_categories"

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    icon: Mapped[str | None] = mapped_column(String(100), comment="Icon name or emoji")
    is_system: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False,
                                             comment="True = seeded by platform; False = user-created")
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("freelancers.id", ondelete="SET NULL"),
        comment="Null for system categories"
    )

    freelancers: Mapped[list["Freelancer"]] = relationship(
        back_populates="service_category", foreign_keys="[Freelancer.service_category_id]"
    )


class Service(Base):
    """
    A service offered by a freelancer (e.g. 'Men's Haircut', 'Drain Unblocking').
    Prices stored in smallest currency unit (cents).
    """
    __tablename__ = "services"

    freelancer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("freelancers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    duration_minutes: Mapped[int] = mapped_column(SmallInteger, nullable=False,
                                                   comment="Appointment duration in minutes")
    buffer_minutes: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False,
                                                 comment="Gap after appointment before next slot opens")
    price_cents: Mapped[int] = mapped_column(Integer, nullable=False,
                                              comment="Price in smallest currency unit (e.g. cents)")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_bookable_online: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sort_order: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    color: Mapped[str | None] = mapped_column(String(7), comment="Hex color for calendar display")

    freelancer: Mapped["Freelancer"] = relationship(back_populates="services")
    bookings: Mapped[list["Booking"]] = relationship(back_populates="service")
    form_fields: Mapped[list["BookingFormField"]] = relationship(back_populates="service")

    __table_args__ = (
        CheckConstraint("duration_minutes > 0", name="ck_service_duration_positive"),
        CheckConstraint("price_cents >= 0", name="ck_service_price_non_negative"),
        CheckConstraint("buffer_minutes >= 0", name="ck_service_buffer_non_negative"),
    )


class StaffMember(Base):
    """
    Team member under a freelancer account (e.g. second barber in a shop).
    Has their own working_hours and can be assigned to bookings.
    """
    __tablename__ = "staff_members"

    freelancer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("freelancers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str | None] = mapped_column(String(320))
    phone: Mapped[str | None] = mapped_column(String(30))
    avatar_url: Mapped[str | None] = mapped_column(String(500))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    color: Mapped[str | None] = mapped_column(String(7), comment="Hex color for calendar")

    freelancer: Mapped["Freelancer"] = relationship(back_populates="staff_members")
    working_hours: Mapped[list["WorkingHours"]] = relationship(back_populates="staff_member", cascade="all, delete-orphan")
    bookings: Mapped[list["Booking"]] = relationship(back_populates="staff_member")


class WorkingHours(Base):
    """
    Weekly availability schedule for a freelancer or a specific staff member.
    One row per day per person. Null staff_member_id = applies to the freelancer directly.
    """
    __tablename__ = "working_hours"

    freelancer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("freelancers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    staff_member_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("staff_members.id", ondelete="CASCADE"), index=True
    )
    day_of_week: Mapped[DayOfWeek] = mapped_column(Enum(DayOfWeek), nullable=False)
    is_open: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    open_time: Mapped[time | None] = mapped_column(Time, comment="Local time (stored naive, interpreted in freelancer timezone)")
    close_time: Mapped[time | None] = mapped_column(Time)
    break_start: Mapped[time | None] = mapped_column(Time, comment="Optional mid-day break start")
    break_end: Mapped[time | None] = mapped_column(Time)

    freelancer: Mapped["Freelancer"] = relationship(back_populates="working_hours")
    staff_member: Mapped["StaffMember | None"] = relationship(back_populates="working_hours")

    __table_args__ = (
        UniqueConstraint("freelancer_id", "staff_member_id", "day_of_week",
                         name="uq_working_hours_per_day"),
    )


class BlockedDate(Base):
    """
    One-off dates or date ranges where the freelancer (or staff member)
    is unavailable — holidays, sick days, etc.
    """
    __tablename__ = "blocked_dates"

    freelancer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("freelancers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    staff_member_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("staff_members.id", ondelete="CASCADE"), index=True
    )
    start_date: Mapped[datetime] = mapped_column(Date, nullable=False)
    end_date: Mapped[datetime] = mapped_column(Date, nullable=False)
    reason: Mapped[str | None] = mapped_column(String(255))
    all_day: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    block_start_time: Mapped[time | None] = mapped_column(Time, comment="Only used when all_day=False")
    block_end_time: Mapped[time | None] = mapped_column(Time)

    freelancer: Mapped["Freelancer"] = relationship(back_populates="blocked_dates")

    __table_args__ = (
        CheckConstraint("end_date >= start_date", name="ck_blocked_date_range"),
    )


# ---------------------------------------------------------------------------
# Customers (CRM)
# ---------------------------------------------------------------------------

class Customer(Base):
    """
    Per-freelancer customer record. Auto-created when a booking is made;
    can also be added manually.
    """
    __tablename__ = "customers"

    freelancer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("freelancers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str | None] = mapped_column(String(100))
    email: Mapped[str | None] = mapped_column(String(320), index=True)
    phone: Mapped[str | None] = mapped_column(String(30))
    address_line1: Mapped[str | None] = mapped_column(String(255))
    address_line2: Mapped[str | None] = mapped_column(String(255))
    city: Mapped[str | None] = mapped_column(String(100))
    state: Mapped[str | None] = mapped_column(String(100))
    postcode: Mapped[str | None] = mapped_column(String(20))
    country: Mapped[str | None] = mapped_column(String(2), comment="ISO 3166-1 alpha-2")
    notes: Mapped[str | None] = mapped_column(Text, comment="Internal notes visible only to freelancer")
    date_of_birth: Mapped[datetime | None] = mapped_column(Date)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    freelancer: Mapped["Freelancer"] = relationship(back_populates="customers")
    bookings: Mapped[list["Booking"]] = relationship(back_populates="customer")
    invoices: Mapped[list["Invoice"]] = relationship(back_populates="customer")
    tag_assignments: Mapped[list["CustomerTagAssignment"]] = relationship(back_populates="customer", cascade="all, delete-orphan")
    reviews: Mapped[list["Review"]] = relationship(back_populates="customer")

    __table_args__ = (
        # A customer's email must be unique per freelancer (not globally)
        UniqueConstraint("freelancer_id", "email", name="uq_customer_email_per_freelancer"),
        Index("ix_customer_search", "freelancer_id", "first_name", "last_name", "email"),
    )


class CustomerTag(Base):
    """Normalised tag labels owned by a freelancer (e.g. 'VIP', 'Repeat', 'Corporate')."""
    __tablename__ = "customer_tags"

    freelancer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("freelancers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    color: Mapped[str | None] = mapped_column(String(7), comment="Hex color for UI badge")

    freelancer: Mapped["Freelancer"] = relationship(back_populates="customer_tags")
    assignments: Mapped[list["CustomerTagAssignment"]] = relationship(back_populates="tag", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("freelancer_id", "name", name="uq_tag_name_per_freelancer"),
    )


class CustomerTagAssignment(Base):
    """M2M join: customers ↔ customer_tags."""
    __tablename__ = "customer_tag_assignments"

    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False
    )
    tag_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customer_tags.id", ondelete="CASCADE"), nullable=False
    )

    customer: Mapped["Customer"] = relationship(back_populates="tag_assignments")
    tag: Mapped["CustomerTag"] = relationship(back_populates="assignments")

    __table_args__ = (
        UniqueConstraint("customer_id", "tag_id", name="uq_customer_tag_assignment"),
    )


# ---------------------------------------------------------------------------
# Bookings
# ---------------------------------------------------------------------------

class BookingFormField(Base):
    """
    Custom question the freelancer adds to their booking form
    (e.g. 'What style do you want?', 'Do you have allergies?').
    Can be scoped to a specific service or shown for all services (service_id=NULL).
    """
    __tablename__ = "booking_form_fields"

    freelancer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("freelancers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    service_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("services.id", ondelete="CASCADE"),
        comment="Null = show for all services"
    )
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    field_type: Mapped[FormFieldType] = mapped_column(Enum(FormFieldType), nullable=False)
    options: Mapped[list | None] = mapped_column(JSONB, comment="Options list for SELECT type")
    is_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sort_order: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    freelancer: Mapped["Freelancer"] = relationship(back_populates="booking_form_fields")
    service: Mapped["Service | None"] = relationship(back_populates="form_fields")
    answers: Mapped[list["BookingCustomAnswer"]] = relationship(back_populates="field", cascade="all, delete-orphan")


class Booking(Base):
    """
    Core appointment record. Links a freelancer, customer, and service.

    Business rules:
    - start_time and end_time stored in UTC.
    - end_time = start_time + service.duration_minutes (computed on creation).
    - Overlapping bookings for the same freelancer/staff member are prevented
      at the service layer (not enforced by DB constraint to allow flexibility).
    - cancel_token is a one-time-use secret sent to the customer for
      self-service cancellation/rescheduling.
    """
    __tablename__ = "bookings"

    freelancer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("freelancers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    service_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("services.id", ondelete="RESTRICT"), nullable=False
    )
    staff_member_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("staff_members.id", ondelete="SET NULL"), index=True
    )
    recurring_rule_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("recurring_booking_rules.id", ondelete="SET NULL"),
        comment="Non-null if this booking was generated from a recurring rule"
    )

    # --- Scheduling ---
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    duration_minutes: Mapped[int] = mapped_column(SmallInteger, nullable=False,
                                                    comment="Snapshot of service.duration_minutes at booking time")

    # --- Status ---
    status: Mapped[BookingStatus] = mapped_column(
        Enum(BookingStatus), default=BookingStatus.PENDING, nullable=False, index=True
    )
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cancellation_reason: Mapped[str | None] = mapped_column(String(500))
    cancelled_by: Mapped[str | None] = mapped_column(String(20),
                                                       comment="'freelancer' or 'customer'")

    # --- Pricing snapshot ---
    price_cents: Mapped[int] = mapped_column(Integer, nullable=False,
                                              comment="Snapshot of service price at time of booking")

    # --- Notes ---
    customer_notes: Mapped[str | None] = mapped_column(Text, comment="Notes provided by the customer at booking")
    internal_notes: Mapped[str | None] = mapped_column(Text, comment="Private notes by the freelancer")

    # --- Customer self-service ---
    cancel_token: Mapped[str] = mapped_column(String(64), unique=True, nullable=False,
                                               comment="Secret token in cancellation/reschedule email link")
    cancel_token_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # --- Reminders ---
    reminder_24h_sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    reminder_2h_sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # --- Relationships ---
    freelancer: Mapped["Freelancer"] = relationship(back_populates="bookings")
    customer: Mapped["Customer"] = relationship(back_populates="bookings")
    service: Mapped["Service"] = relationship(back_populates="bookings")
    staff_member: Mapped["StaffMember | None"] = relationship(back_populates="bookings")
    recurring_rule: Mapped["RecurringBookingRule | None"] = relationship(back_populates="bookings")
    custom_answers: Mapped[list["BookingCustomAnswer"]] = relationship(back_populates="booking", cascade="all, delete-orphan")
    invoice: Mapped["Invoice | None"] = relationship(back_populates="booking", uselist=False)
    review: Mapped["Review | None"] = relationship(back_populates="booking", uselist=False)

    __table_args__ = (
        CheckConstraint("end_time > start_time", name="ck_booking_time_range"),
        CheckConstraint("price_cents >= 0", name="ck_booking_price_non_negative"),
        Index("ix_booking_freelancer_time", "freelancer_id", "start_time", "status"),
    )


class BookingCustomAnswer(Base):
    """Customer's answers to the freelancer's custom booking form fields."""
    __tablename__ = "booking_custom_answers"

    booking_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    field_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("booking_form_fields.id", ondelete="CASCADE"), nullable=False
    )
    answer: Mapped[str | None] = mapped_column(Text)

    booking: Mapped["Booking"] = relationship(back_populates="custom_answers")
    field: Mapped["BookingFormField"] = relationship(back_populates="answers")

    __table_args__ = (
        UniqueConstraint("booking_id", "field_id", name="uq_booking_answer_per_field"),
    )


class WaitlistEntry(Base):
    """
    A customer who wants to be notified if a slot opens up for a
    specific service on a specific date.
    """
    __tablename__ = "waitlist_entries"

    freelancer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("freelancers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    service_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("services.id", ondelete="CASCADE"), nullable=False
    )
    customer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customers.id", ondelete="SET NULL"),
        comment="Null if the customer is not yet in the CRM"
    )
    # Guest info (used when customer_id is null)
    guest_name: Mapped[str | None] = mapped_column(String(200))
    guest_email: Mapped[str | None] = mapped_column(String(320))
    guest_phone: Mapped[str | None] = mapped_column(String(30))

    requested_date: Mapped[datetime] = mapped_column(Date, nullable=False)
    is_notified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_booked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False,
                                             comment="True if the customer went on to book the opened slot")

    __table_args__ = (
        Index("ix_waitlist_freelancer_date", "freelancer_id", "requested_date", "is_notified"),
    )


class RecurringBookingRule(Base):
    """
    Defines a recurring appointment pattern.
    Individual Booking records are generated from this rule by a Celery task.
    """
    __tablename__ = "recurring_booking_rules"

    freelancer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("freelancers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False
    )
    service_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("services.id", ondelete="CASCADE"), nullable=False
    )
    staff_member_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("staff_members.id", ondelete="SET NULL")
    )
    frequency: Mapped[RecurringFrequency] = mapped_column(Enum(RecurringFrequency), nullable=False)
    preferred_time: Mapped[time] = mapped_column(Time, nullable=False,
                                                  comment="Preferred time of day (local, interpreted in freelancer tz)")
    start_date: Mapped[datetime] = mapped_column(Date, nullable=False)
    end_date: Mapped[datetime | None] = mapped_column(Date, comment="Null = indefinite")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_generated_date: Mapped[datetime | None] = mapped_column(Date,
                                                                   comment="Date up to which bookings have been auto-generated")

    bookings: Mapped[list["Booking"]] = relationship(back_populates="recurring_rule")


# ---------------------------------------------------------------------------
# Invoicing
# ---------------------------------------------------------------------------

class Invoice(Base):
    """
    Billing document issued to a customer.
    Can be auto-generated from a booking or created manually.
    All monetary values in cents.
    """
    __tablename__ = "invoices"

    freelancer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("freelancers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    booking_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("bookings.id", ondelete="SET NULL"), unique=True,
        comment="Null for manually created invoices"
    )

    # --- Numbering ---
    invoice_number: Mapped[str] = mapped_column(String(50), nullable=False,
                                                  comment="Human-readable, e.g. INV-2025-0001")
    # --- Dates ---
    issue_date: Mapped[datetime] = mapped_column(Date, nullable=False)
    due_date: Mapped[datetime | None] = mapped_column(Date)

    # --- Status ---
    status: Mapped[InvoiceStatus] = mapped_column(
        Enum(InvoiceStatus), default=InvoiceStatus.DRAFT, nullable=False, index=True
    )
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # --- Amounts (all in cents) ---
    subtotal_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    discount_cents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    tax_rate_bps: Mapped[int] = mapped_column(Integer, default=0, nullable=False,
                                               comment="Tax rate in basis points (e.g. 1000 = 10%)")
    tax_cents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_cents: Mapped[int] = mapped_column(Integer, nullable=False)

    # --- Customisation ---
    notes: Mapped[str | None] = mapped_column(Text, comment="Visible on the invoice PDF")
    payment_terms: Mapped[str | None] = mapped_column(String(500))

    # --- PDF ---
    pdf_url: Mapped[str | None] = mapped_column(String(500), comment="Path or URL to generated PDF")
    pdf_generated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # --- Relationships ---
    freelancer: Mapped["Freelancer"] = relationship(back_populates="invoices")
    customer: Mapped["Customer"] = relationship(back_populates="invoices")
    booking: Mapped["Booking | None"] = relationship(back_populates="invoice")
    line_items: Mapped[list["InvoiceLineItem"]] = relationship(back_populates="invoice", cascade="all, delete-orphan")
    payments: Mapped[list["Payment"]] = relationship(back_populates="invoice", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("freelancer_id", "invoice_number", name="uq_invoice_number_per_freelancer"),
        CheckConstraint("total_cents >= 0", name="ck_invoice_total_non_negative"),
        Index("ix_invoice_freelancer_status", "freelancer_id", "status"),
    )


class InvoiceLineItem(Base):
    """A single line item within an invoice."""
    __tablename__ = "invoice_line_items"

    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False, index=True
    )
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    quantity: Mapped[float] = mapped_column(Numeric(10, 2), default=1, nullable=False)
    unit_price_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    discount_percent: Mapped[float] = mapped_column(Numeric(5, 2), default=0, nullable=False,
                                                     comment="Per-item discount, 0–100")
    line_total_cents: Mapped[int] = mapped_column(Integer, nullable=False,
                                                   comment="(unit_price * qty) * (1 - discount/100), in cents")
    sort_order: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)

    invoice: Mapped["Invoice"] = relationship(back_populates="line_items")

    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_line_item_qty_positive"),
        CheckConstraint("discount_percent >= 0 AND discount_percent <= 100",
                        name="ck_line_item_discount_range"),
    )


class Payment(Base):
    """
    A payment record against an invoice.
    An invoice may have multiple partial payments.
    """
    __tablename__ = "payments"

    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False, index=True
    )
    freelancer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("freelancers.id", ondelete="CASCADE"), nullable=False, index=True,
        comment="Denormalised for fast finance queries without joining invoices"
    )
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    method: Mapped[PaymentMethod] = mapped_column(Enum(PaymentMethod), nullable=False)
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus), default=PaymentStatus.COMPLETED, nullable=False
    )
    paid_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    reference: Mapped[str | None] = mapped_column(String(255),
                                                    comment="Bank ref, Stripe charge ID, etc.")
    notes: Mapped[str | None] = mapped_column(String(500))

    # --- Stripe / PayPal integration ---
    gateway_payment_id: Mapped[str | None] = mapped_column(String(255), index=True,
                                                             comment="External payment gateway ID")
    gateway_response: Mapped[dict | None] = mapped_column(JSONB, comment="Raw gateway webhook payload")

    invoice: Mapped["Invoice"] = relationship(back_populates="payments")

    __table_args__ = (
        CheckConstraint("amount_cents > 0", name="ck_payment_amount_positive"),
    )


# ---------------------------------------------------------------------------
# Reviews
# ---------------------------------------------------------------------------

class Review(Base):
    """
    Post-appointment review left by the customer.
    One review per booking. Displayed on the freelancer's public page.
    """
    __tablename__ = "reviews"

    freelancer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("freelancers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    booking_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False
    )
    rating: Mapped[int] = mapped_column(SmallInteger, nullable=False, comment="1–5 stars")
    comment: Mapped[str | None] = mapped_column(Text)
    is_published: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    reply: Mapped[str | None] = mapped_column(Text, comment="Freelancer's reply to the review")
    replied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Review submitted via unique token sent in post-completion email
    review_token: Mapped[str | None] = mapped_column(String(64), unique=True)
    review_token_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    freelancer: Mapped["Freelancer"] = relationship(back_populates="reviews")
    booking: Mapped["Booking"] = relationship(back_populates="review")
    customer: Mapped["Customer"] = relationship(back_populates="reviews")

    __table_args__ = (
        CheckConstraint("rating >= 1 AND rating <= 5", name="ck_review_rating_range"),
    )


# ---------------------------------------------------------------------------
# Notifications
# ---------------------------------------------------------------------------

class Notification(Base):
    """
    In-app notification log. Displayed in the freelancer's notification bell.
    """
    __tablename__ = "notifications"

    freelancer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("freelancers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    type: Mapped[NotificationType] = mapped_column(Enum(NotificationType), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str | None] = mapped_column(Text)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Polymorphic reference to the related entity
    entity_type: Mapped[str | None] = mapped_column(String(50),
                                                      comment="e.g. 'booking', 'invoice'")
    entity_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True),
                                                          comment="ID of the related booking/invoice/etc.")

    freelancer: Mapped["Freelancer"] = relationship(back_populates="notifications")

    __table_args__ = (
        Index("ix_notification_freelancer_unread", "freelancer_id", "is_read"),
    )


# ---------------------------------------------------------------------------
# Settings / Config
# ---------------------------------------------------------------------------

class FreelancerSettings(Base):
    """
    Extended per-freelancer configuration: branding, tax, invoice defaults,
    booking policies, and integration keys.
    One-to-one with Freelancer.
    """
    __tablename__ = "freelancer_settings"

    freelancer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("freelancers.id", ondelete="CASCADE"),
        nullable=False, unique=True, index=True
    )

    # --- Branding ---
    logo_url: Mapped[str | None] = mapped_column(String(500))
    accent_color: Mapped[str | None] = mapped_column(String(7), default="#6366f1",
                                                       comment="Hex color for public booking page")
    booking_page_headline: Mapped[str | None] = mapped_column(String(255))
    booking_page_description: Mapped[str | None] = mapped_column(Text)

    # --- Tax ---
    tax_name: Mapped[str | None] = mapped_column(String(50), default="GST",
                                                   comment="e.g. GST, VAT")
    tax_rate_bps: Mapped[int] = mapped_column(Integer, default=0, nullable=False,
                                               comment="Default tax rate in basis points (1000 = 10%)")
    tax_number: Mapped[str | None] = mapped_column(String(50),
                                                    comment="ABN, VAT number, etc.")

    # --- Invoice defaults ---
    invoice_prefix: Mapped[str] = mapped_column(String(10), default="INV", nullable=False)
    invoice_footer: Mapped[str | None] = mapped_column(Text)
    payment_terms_days: Mapped[int] = mapped_column(SmallInteger, default=7, nullable=False)
    invoice_sequence: Mapped[int] = mapped_column(Integer, default=0, nullable=False,
                                                    comment="Auto-incremented for each new invoice")

    # --- Booking policies ---
    booking_advance_days: Mapped[int] = mapped_column(SmallInteger, default=60, nullable=False,
                                                        comment="How many days ahead customers can book")
    cancellation_window_hours: Mapped[int] = mapped_column(SmallInteger, default=2, nullable=False,
                                                             comment="Hours before appointment within which cancellation is blocked")
    auto_confirm_bookings: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False,
                                                          comment="Auto-confirm without manual approval")
    max_bookings_per_day: Mapped[int | None] = mapped_column(SmallInteger,
                                                               comment="Daily booking cap; null = unlimited")

    # --- Stripe ---
    stripe_account_id: Mapped[str | None] = mapped_column(String(255), comment="Stripe Connect account ID")
    stripe_onboarding_complete: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # --- Google Calendar ---
    google_calendar_token: Mapped[dict | None] = mapped_column(JSONB,
                                                                comment="Encrypted OAuth tokens for GCal sync")
    google_calendar_id: Mapped[str | None] = mapped_column(String(255))

    freelancer: Mapped["Freelancer"] = relationship(back_populates="settings")


class NotificationPreferences(Base):
    """
    Which in-app and email events the freelancer wants to be notified about.
    One-to-one with Freelancer.
    """
    __tablename__ = "notification_preferences"

    freelancer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("freelancers.id", ondelete="CASCADE"),
        nullable=False, unique=True, index=True
    )

    # --- Email ---
    email_new_booking: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    email_booking_cancelled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    email_booking_reminder: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    email_invoice_paid: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    email_invoice_overdue: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    email_new_review: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # --- In-app ---
    inapp_new_booking: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    inapp_booking_cancelled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    inapp_invoice_paid: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    inapp_new_review: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # --- SMS (v2) ---
    sms_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sms_new_booking: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sms_booking_reminder: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    freelancer: Mapped["Freelancer"] = relationship(back_populates="notification_preferences")


# ---------------------------------------------------------------------------
# All models exposed for Alembic autodiscovery
# ---------------------------------------------------------------------------

__all__ = [
    "Base",
    # Enums
    "DayOfWeek", "BookingStatus", "InvoiceStatus", "PaymentMethod",
    "PaymentStatus", "RecurringFrequency", "NotificationType",
    "FormFieldType", "StorageBackend",
    # Models
    "Freelancer", "RefreshToken", "PasswordResetToken",
    "ServiceCategory", "Service", "StaffMember",
    "WorkingHours", "BlockedDate",
    "Customer", "CustomerTag", "CustomerTagAssignment",
    "BookingFormField", "Booking", "BookingCustomAnswer",
    "WaitlistEntry", "RecurringBookingRule",
    "Invoice", "InvoiceLineItem", "Payment",
    "Review",
    "Notification",
    "FreelancerSettings", "NotificationPreferences",
]

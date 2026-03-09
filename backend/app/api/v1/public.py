from __future__ import annotations

"""
Public booking API — no authentication required.
NOTE: In production, apply rate limiting (e.g., slowapi) to all endpoints here.
"""

import sys
import uuid
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path

_PROJECT_ROOT = str(Path(__file__).resolve().parents[4])
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from models import (  # noqa: E402
    BlockedDate,
    Booking,
    BookingCustomAnswer,
    BookingStatus,
    Customer,
    Freelancer,
    Review,
    Service,
    WorkingHours,
)

import secrets
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.crud.crud_availability import crud_blocked_date, crud_working_hours
from app.crud.crud_booking import crud_booking
from app.crud.crud_customer import crud_customer
from app.crud.crud_review import crud_review
from app.crud.crud_service import crud_service
from app.crud.crud_settings import crud_settings
from app.db.session import get_db
from app.schemas.availability import AvailableSlot
from app.schemas.booking import BookingResponse, PublicBookingCreate
from app.schemas.review import PublicReviewCreate, ReviewResponse
from app.schemas.service import ServiceResponse

router = APIRouter(prefix="/public", tags=["public"])


async def _get_freelancer_by_username(
    db: AsyncSession, username: str
) -> Freelancer:
    result = await db.execute(
        select(Freelancer).where(
            Freelancer.username == username.lower(),
            Freelancer.is_active.is_(True),
        )
    )
    freelancer = result.scalar_one_or_none()
    if not freelancer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Freelancer not found",
        )
    return freelancer


@router.get("/{username}")
async def get_public_profile(
    username: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Public freelancer profile — rate limit: 60 req/min per IP."""
    freelancer = await _get_freelancer_by_username(db, username)

    services = await crud_service.get_multi_by_freelancer(
        db, freelancer.id, active_only=True
    )
    avg_rating = await crud_review.get_average_rating(db, freelancer.id)

    return {
        "id": str(freelancer.id),
        "username": freelancer.username,
        "first_name": freelancer.first_name,
        "last_name": freelancer.last_name,
        "business_name": freelancer.business_name,
        "bio": freelancer.bio,
        "avatar_url": freelancer.avatar_url,
        "timezone": freelancer.timezone,
        "currency": freelancer.currency,
        "average_rating": avg_rating,
        "services": [ServiceResponse.model_validate(s).model_dump() for s in services],
    }


@router.get("/{username}/services", response_model=list[ServiceResponse])
async def get_public_services(
    username: str,
    db: AsyncSession = Depends(get_db),
) -> list[ServiceResponse]:
    """Active bookable services — rate limit: 60 req/min per IP."""
    freelancer = await _get_freelancer_by_username(db, username)
    services = await crud_service.get_multi_by_freelancer(
        db, freelancer.id, active_only=True
    )
    return [
        ServiceResponse.model_validate(s)
        for s in services
        if s.is_bookable_online
    ]


def _compute_slots(
    target_date: date,
    working_hours: WorkingHours,
    duration_minutes: int,
    buffer_minutes: int,
    blocked_dates: list[BlockedDate],
    existing_bookings: list[Booking],
    freelancer_tz: str = "UTC",
) -> list[AvailableSlot]:
    """
    Compute available time slots for a given day.

    Logic:
    1. Check working hours — if closed, return empty.
    2. Build candidate slots every (duration + buffer) minutes within open_time..close_time.
    3. Remove slots that overlap with break time.
    4. Remove slots blocked by blocked_dates.
    5. Remove slots that conflict with existing bookings.
    """
    if not working_hours.is_open or not working_hours.open_time or not working_hours.close_time:
        return []

    # Check if entire day is blocked
    for bd in blocked_dates:
        if bd.all_day and bd.start_date <= target_date <= bd.end_date:
            return []

    slot_duration = timedelta(minutes=duration_minutes + buffer_minutes)

    open_dt = datetime.combine(target_date, working_hours.open_time, tzinfo=timezone.utc)
    close_dt = datetime.combine(target_date, working_hours.close_time, tzinfo=timezone.utc)

    # Break window
    break_start_dt: datetime | None = None
    break_end_dt: datetime | None = None
    if working_hours.break_start and working_hours.break_end:
        break_start_dt = datetime.combine(target_date, working_hours.break_start, tzinfo=timezone.utc)
        break_end_dt = datetime.combine(target_date, working_hours.break_end, tzinfo=timezone.utc)

    slots: list[AvailableSlot] = []
    current = open_dt
    step = timedelta(minutes=duration_minutes + buffer_minutes)

    while current + timedelta(minutes=duration_minutes) <= close_dt:
        slot_end = current + timedelta(minutes=duration_minutes)

        # Skip if overlaps break
        if break_start_dt and break_end_dt:
            if current < break_end_dt and slot_end > break_start_dt:
                current += step
                continue

        # Skip if overlaps a partial-day blocked period
        skip = False
        for bd in blocked_dates:
            if bd.start_date <= target_date <= bd.end_date:
                if not bd.all_day and bd.block_start_time and bd.block_end_time:
                    block_start = datetime.combine(
                        target_date, bd.block_start_time, tzinfo=timezone.utc
                    )
                    block_end = datetime.combine(
                        target_date, bd.block_end_time, tzinfo=timezone.utc
                    )
                    if current < block_end and slot_end > block_start:
                        skip = True
                        break
        if skip:
            current += step
            continue

        # Skip if overlaps existing booking
        conflict = False
        for booking in existing_bookings:
            if booking.start_time < slot_end and booking.end_time > current:
                conflict = True
                break
        if not conflict:
            slots.append(AvailableSlot(start_time=current, end_time=slot_end))

        current += step

    return slots


@router.get("/{username}/available-slots", response_model=list[AvailableSlot])
async def get_available_slots(
    username: str,
    service_id: uuid.UUID = Query(...),
    date: date = Query(...),
    staff_member_id: uuid.UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> list[AvailableSlot]:
    """Available booking slots for a given service and date — rate limit: 30 req/min per IP."""
    freelancer = await _get_freelancer_by_username(db, username)

    service_result = await db.execute(
        select(Service).where(
            Service.freelancer_id == freelancer.id,
            Service.id == service_id,
            Service.is_active.is_(True),
            Service.is_bookable_online.is_(True),
        )
    )
    service = service_result.scalar_one_or_none()
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not available",
        )

    # Get settings for advance booking limit
    settings_obj = await crud_settings.get_or_create(db, freelancer.id)
    max_date = date.today() + timedelta(days=settings_obj.booking_advance_days)
    if date > max_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot book more than {settings_obj.booking_advance_days} days in advance",
        )
    if date < date.today():
        return []

    # Get working hours for this day
    day_name = date.strftime("%A").upper()  # e.g. "MONDAY"
    wh_list = await crud_working_hours.get_by_freelancer(
        db, freelancer.id, staff_member_id=staff_member_id
    )
    wh: WorkingHours | None = None
    for h in wh_list:
        if h.day_of_week.value == day_name or h.day_of_week == day_name:
            wh = h
            break
    if not wh:
        return []

    # Get blocked dates overlapping this date
    blocked = await crud_blocked_date.get_multi_by_freelancer(
        db, freelancer.id, from_date=date, to_date=date
    )

    # Get existing bookings for this day
    day_start = datetime.combine(date, time.min, tzinfo=timezone.utc)
    day_end = datetime.combine(date, time.max, tzinfo=timezone.utc)
    existing, _ = await crud_booking.get_multi_by_freelancer(
        db,
        freelancer.id,
        skip=0,
        limit=500,
        from_date=day_start,
        to_date=day_end,
    )
    # Filter to only active bookings
    active_bookings = [
        b for b in existing
        if b.status in (BookingStatus.PENDING, BookingStatus.CONFIRMED)
        and (staff_member_id is None or b.staff_member_id == staff_member_id)
    ]

    return _compute_slots(
        target_date=date,
        working_hours=wh,
        duration_minutes=service.duration_minutes,
        buffer_minutes=service.buffer_minutes,
        blocked_dates=blocked,
        existing_bookings=active_bookings,
        freelancer_tz=freelancer.timezone,
    )


@router.post("/{username}/bookings", status_code=status.HTTP_201_CREATED)
async def create_public_booking(
    username: str,
    obj_in: PublicBookingCreate,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Public booking creation — rate limit: 10 req/min per IP."""
    freelancer = await _get_freelancer_by_username(db, username)

    service_result = await db.execute(
        select(Service).where(
            Service.freelancer_id == freelancer.id,
            Service.id == obj_in.service_id,
            Service.is_active.is_(True),
            Service.is_bookable_online.is_(True),
        )
    )
    service = service_result.scalar_one_or_none()
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not available",
        )

    settings_obj = await crud_settings.get_or_create(db, freelancer.id)

    # Check advance booking window
    max_date = date.today() + timedelta(days=settings_obj.booking_advance_days)
    if obj_in.start_time.date() > max_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Requested time is too far in advance",
        )

    end_time = obj_in.start_time + timedelta(minutes=service.duration_minutes)

    # Check for conflicts
    overlapping = await crud_booking.get_overlapping(
        db,
        freelancer.id,
        obj_in.start_time,
        end_time,
        obj_in.staff_member_id,
    )
    if overlapping:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This time slot is no longer available",
        )

    # Find or create customer
    customer: Customer | None = None
    if obj_in.email:
        customer = await crud_customer.get_by_email(db, freelancer.id, obj_in.email)
    if not customer:
        from app.schemas.customer import CustomerCreate

        customer_data = CustomerCreate(
            first_name=obj_in.first_name,
            last_name=obj_in.last_name,
            email=obj_in.email,
            phone=obj_in.phone,
        )
        customer = await crud_customer.create_for_freelancer(
            db, freelancer.id, customer_data
        )

    cancel_token = secrets.token_hex(32)
    status_val = BookingStatus.CONFIRMED if settings_obj.auto_confirm_bookings else BookingStatus.PENDING

    booking = Booking(
        freelancer_id=freelancer.id,
        customer_id=customer.id,
        service_id=service.id,
        staff_member_id=obj_in.staff_member_id,
        start_time=obj_in.start_time,
        end_time=end_time,
        duration_minutes=service.duration_minutes,
        price_cents=service.price_cents,
        status=status_val,
        cancel_token=cancel_token,
        customer_notes=obj_in.customer_notes,
    )
    db.add(booking)
    await db.flush()

    if obj_in.custom_answers:
        for ans in obj_in.custom_answers:
            db.add(
                BookingCustomAnswer(
                    booking_id=booking.id,
                    field_id=ans.get("field_id"),
                    answer=ans.get("answer"),
                )
            )

    await db.commit()
    await db.refresh(booking)

    return {
        "booking_id": str(booking.id),
        "cancel_token": cancel_token,
        "message": "Booking created successfully",
        "status": booking.status.value if hasattr(booking.status, "value") else str(booking.status),
    }


@router.get("/cancel/{cancel_token}")
async def get_cancellation_details(
    cancel_token: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get booking details for cancellation page — rate limit: 20 req/min per IP."""
    booking = await crud_booking.get_by_cancel_token(db, cancel_token)
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid cancellation token",
        )
    return {
        "booking_id": str(booking.id),
        "service_id": str(booking.service_id),
        "start_time": booking.start_time.isoformat(),
        "end_time": booking.end_time.isoformat(),
        "status": booking.status.value if hasattr(booking.status, "value") else str(booking.status),
        "duration_minutes": booking.duration_minutes,
        "price_cents": booking.price_cents,
    }


@router.post("/cancel/{cancel_token}")
async def cancel_booking_via_token(
    cancel_token: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Cancel a booking via the cancel token link — rate limit: 10 req/min per IP."""
    booking = await crud_booking.get_by_cancel_token(db, cancel_token)
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid cancellation token",
        )
    if booking.status == BookingStatus.CANCELLED:
        return {"message": "Booking is already cancelled"}
    if booking.status not in (BookingStatus.PENDING, BookingStatus.CONFIRMED):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This booking cannot be cancelled",
        )

    # Check cancellation window
    settings_obj = await crud_settings.get_or_create(db, booking.freelancer_id)
    window_hours = settings_obj.cancellation_window_hours
    if window_hours > 0:
        cutoff = booking.start_time - timedelta(hours=window_hours)
        if datetime.now(timezone.utc) > cutoff:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cancellations must be made at least {window_hours} hours before the appointment",
            )

    booking = await crud_booking.update_status(
        db, booking, BookingStatus.CANCELLED, cancelled_by="customer"
    )
    return {"message": "Booking cancelled successfully"}


@router.get("/review/{review_token}", response_model=ReviewResponse)
async def get_review_by_token(
    review_token: str,
    db: AsyncSession = Depends(get_db),
) -> ReviewResponse:
    """Get review form by token — rate limit: 20 req/min per IP."""
    review = await crud_review.get_by_token(db, review_token)
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid or expired review token",
        )
    # Check expiry
    if review.review_token_expires_at:
        expires = review.review_token_expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc) > expires:
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="Review link has expired",
            )
    return ReviewResponse.model_validate(review)


@router.post("/review/{review_token}", response_model=ReviewResponse)
async def submit_review(
    review_token: str,
    body: PublicReviewCreate,
    db: AsyncSession = Depends(get_db),
) -> ReviewResponse:
    """Submit a review via token — rate limit: 5 req/min per IP."""
    review = await crud_review.get_by_token(db, review_token)
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid or expired review token",
        )
    if review.review_token_expires_at:
        expires = review.review_token_expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc) > expires:
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="Review link has expired",
            )
    # Token must match
    if body.token != review_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token mismatch",
        )
    if review.review_token is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Review has already been submitted",
        )

    review = await crud_review.create_from_token(
        db, review, rating=body.rating, comment=body.comment
    )
    return ReviewResponse.model_validate(review)

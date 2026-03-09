from __future__ import annotations

import sys
import uuid
from datetime import datetime
from pathlib import Path

_PROJECT_ROOT = str(Path(__file__).resolve().parents[4])
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from models import BookingStatus, Freelancer  # noqa: E402

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_freelancer
from app.crud.crud_booking import crud_booking, crud_recurring_rule, crud_waitlist
from app.crud.crud_service import crud_service
from app.crud.crud_settings import crud_settings
from app.db.session import get_db
from app.schemas.booking import (
    BookingCreate,
    BookingResponse,
    BookingStatusUpdate,
    BookingUpdate,
    RecurringRuleCreate,
    RecurringRuleResponse,
    WaitlistEntryCreate,
    WaitlistEntryResponse,
)
from app.schemas.common import MessageResponse, PaginatedResponse

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.get("/waitlist", response_model=list[WaitlistEntryResponse])
async def list_waitlist(
    db: AsyncSession = Depends(get_db),
    current_freelancer: Freelancer = Depends(get_current_active_freelancer),
) -> list[WaitlistEntryResponse]:
    entries = await crud_waitlist.get_multi_by_freelancer(db, current_freelancer.id)
    return [WaitlistEntryResponse.model_validate(e) for e in entries]


@router.post(
    "/waitlist",
    response_model=WaitlistEntryResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_waitlist_entry(
    obj_in: WaitlistEntryCreate,
    db: AsyncSession = Depends(get_db),
    current_freelancer: Freelancer = Depends(get_current_active_freelancer),
) -> WaitlistEntryResponse:
    entry = await crud_waitlist.create(db, current_freelancer.id, obj_in)
    return WaitlistEntryResponse.model_validate(entry)


@router.get("/recurring", response_model=list[RecurringRuleResponse])
async def list_recurring_rules(
    db: AsyncSession = Depends(get_db),
    current_freelancer: Freelancer = Depends(get_current_active_freelancer),
) -> list[RecurringRuleResponse]:
    rules = await crud_recurring_rule.get_multi_by_freelancer(db, current_freelancer.id)
    return [RecurringRuleResponse.model_validate(r) for r in rules]


@router.post(
    "/recurring",
    response_model=RecurringRuleResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_recurring_rule(
    obj_in: RecurringRuleCreate,
    db: AsyncSession = Depends(get_db),
    current_freelancer: Freelancer = Depends(get_current_active_freelancer),
) -> RecurringRuleResponse:
    rule = await crud_recurring_rule.create_for_freelancer(db, current_freelancer.id, obj_in)
    return RecurringRuleResponse.model_validate(rule)


@router.delete("/recurring/{rule_id}", response_model=MessageResponse)
async def deactivate_recurring_rule(
    rule_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_freelancer: Freelancer = Depends(get_current_active_freelancer),
) -> MessageResponse:
    await crud_recurring_rule.deactivate(db, rule_id)
    return MessageResponse(message="Recurring rule deactivated")


@router.get("/", response_model=PaginatedResponse[BookingResponse])
async def list_bookings(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status: BookingStatus | None = Query(default=None),
    from_date: datetime | None = Query(default=None),
    to_date: datetime | None = Query(default=None),
    customer_id: uuid.UUID | None = Query(default=None),
    service_id: uuid.UUID | None = Query(default=None),
    search: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_freelancer: Freelancer = Depends(get_current_active_freelancer),
) -> PaginatedResponse[BookingResponse]:
    skip = (page - 1) * page_size
    bookings, total = await crud_booking.get_multi_by_freelancer(
        db,
        current_freelancer.id,
        skip=skip,
        limit=page_size,
        status=status,
        from_date=from_date,
        to_date=to_date,
        customer_id=customer_id,
        service_id=service_id,
        search=search,
    )
    pages = max(1, (total + page_size - 1) // page_size)
    return PaginatedResponse(
        items=[BookingResponse.model_validate(b) for b in bookings],
        total=total,
        page=page,
        pages=pages,
    )


@router.post("/", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
async def create_booking(
    obj_in: BookingCreate,
    db: AsyncSession = Depends(get_db),
    current_freelancer: Freelancer = Depends(get_current_active_freelancer),
) -> BookingResponse:
    service = await crud_service.get_by_freelancer(
        db, current_freelancer.id, obj_in.service_id
    )
    if not service:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")

    # Check for conflicts
    from datetime import timedelta

    end_time = obj_in.start_time + timedelta(minutes=service.duration_minutes)
    overlapping = await crud_booking.get_overlapping(
        db,
        current_freelancer.id,
        obj_in.start_time,
        end_time,
        obj_in.staff_member_id,
    )
    if overlapping:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Time slot is not available",
        )

    settings_obj = await crud_settings.get_or_create(db, current_freelancer.id)
    booking = await crud_booking.create_for_freelancer(
        db,
        current_freelancer.id,
        obj_in,
        service_duration=service.duration_minutes,
        service_price=service.price_cents,
        auto_confirm=settings_obj.auto_confirm_bookings,
    )
    return BookingResponse.model_validate(booking)


@router.get("/{booking_id}", response_model=BookingResponse)
async def get_booking(
    booking_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_freelancer: Freelancer = Depends(get_current_active_freelancer),
) -> BookingResponse:
    booking = await crud_booking.get_by_freelancer(db, current_freelancer.id, booking_id)
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    return BookingResponse.model_validate(booking)


@router.patch("/{booking_id}/status", response_model=BookingResponse)
async def update_booking_status(
    booking_id: uuid.UUID,
    body: BookingStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_freelancer: Freelancer = Depends(get_current_active_freelancer),
) -> BookingResponse:
    booking = await crud_booking.get_by_freelancer(db, current_freelancer.id, booking_id)
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    booking = await crud_booking.update_status(
        db,
        booking,
        body.status,
        cancellation_reason=body.cancellation_reason,
        cancelled_by="freelancer",
    )
    return BookingResponse.model_validate(booking)


@router.put("/{booking_id}", response_model=BookingResponse)
async def update_booking(
    booking_id: uuid.UUID,
    obj_in: BookingUpdate,
    db: AsyncSession = Depends(get_db),
    current_freelancer: Freelancer = Depends(get_current_active_freelancer),
) -> BookingResponse:
    booking = await crud_booking.get_by_freelancer(db, current_freelancer.id, booking_id)
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    update_data = obj_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(booking, key, value)
    db.add(booking)
    await db.commit()
    await db.refresh(booking)
    return BookingResponse.model_validate(booking)


@router.delete("/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_booking(
    booking_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_freelancer: Freelancer = Depends(get_current_active_freelancer),
) -> None:
    booking = await crud_booking.get_by_freelancer(db, current_freelancer.id, booking_id)
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    if booking.status != BookingStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PENDING bookings can be deleted",
        )
    await db.delete(booking)
    await db.commit()

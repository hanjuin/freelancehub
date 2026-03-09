from __future__ import annotations

import secrets
import sys
import uuid
from datetime import date, datetime
from pathlib import Path

_PROJECT_ROOT = str(Path(__file__).resolve().parents[4])
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from models import (  # noqa: E402
    Booking,
    BookingCustomAnswer,
    BookingStatus,
    RecurringBookingRule,
    WaitlistEntry,
)

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.schemas.booking import (
    BookingCreate,
    BookingUpdate,
    RecurringRuleCreate,
    WaitlistEntryCreate,
)


class CRUDBooking(CRUDBase[Booking, BookingCreate, BookingUpdate]):
    async def get_multi_by_freelancer(
        self,
        db: AsyncSession,
        freelancer_id: uuid.UUID,
        *,
        skip: int = 0,
        limit: int = 100,
        status: BookingStatus | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        customer_id: uuid.UUID | None = None,
    ) -> tuple[list[Booking], int]:
        stmt = select(Booking).where(Booking.freelancer_id == freelancer_id)
        if status is not None:
            stmt = stmt.where(Booking.status == status)
        if from_date is not None:
            stmt = stmt.where(Booking.start_time >= from_date)
        if to_date is not None:
            stmt = stmt.where(Booking.start_time <= to_date)
        if customer_id is not None:
            stmt = stmt.where(Booking.customer_id == customer_id)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        count_result = await db.execute(count_stmt)
        total = count_result.scalar_one()

        stmt = stmt.order_by(Booking.start_time.desc()).offset(skip).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all()), total

    async def get_by_freelancer(
        self, db: AsyncSession, freelancer_id: uuid.UUID, id: uuid.UUID
    ) -> Booking | None:
        result = await db.execute(
            select(Booking).where(
                Booking.freelancer_id == freelancer_id,
                Booking.id == id,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_cancel_token(
        self, db: AsyncSession, token: str
    ) -> Booking | None:
        result = await db.execute(
            select(Booking).where(Booking.cancel_token == token)
        )
        return result.scalar_one_or_none()

    async def create_for_freelancer(
        self,
        db: AsyncSession,
        freelancer_id: uuid.UUID,
        obj_in: BookingCreate,
        service_duration: int,
        service_price: int,
        auto_confirm: bool = False,
    ) -> Booking:
        from datetime import timedelta

        start_time = obj_in.start_time
        end_time = start_time + timedelta(minutes=service_duration)
        status = BookingStatus.CONFIRMED if auto_confirm else BookingStatus.PENDING
        cancel_token = secrets.token_hex(32)

        booking = Booking(
            freelancer_id=freelancer_id,
            customer_id=obj_in.customer_id,
            service_id=obj_in.service_id,
            staff_member_id=obj_in.staff_member_id,
            start_time=start_time,
            end_time=end_time,
            duration_minutes=service_duration,
            price_cents=service_price,
            status=status,
            cancel_token=cancel_token,
            customer_notes=obj_in.customer_notes,
        )
        db.add(booking)
        await db.flush()  # get ID before adding answers

        if obj_in.custom_answers:
            for answer_data in obj_in.custom_answers:
                answer = BookingCustomAnswer(
                    booking_id=booking.id,
                    field_id=answer_data.get("field_id"),
                    answer=answer_data.get("answer"),
                )
                db.add(answer)

        await db.commit()
        await db.refresh(booking)
        return booking

    async def update_status(
        self,
        db: AsyncSession,
        booking: Booking,
        status: BookingStatus,
        cancellation_reason: str | None = None,
        cancelled_by: str | None = None,
    ) -> Booking:
        from datetime import timezone

        booking.status = status
        if status == BookingStatus.CANCELLED:
            booking.cancelled_at = datetime.now(timezone.utc)
            if cancellation_reason:
                booking.cancellation_reason = cancellation_reason
            if cancelled_by:
                booking.cancelled_by = cancelled_by
        db.add(booking)
        await db.commit()
        await db.refresh(booking)
        return booking

    async def get_overlapping(
        self,
        db: AsyncSession,
        freelancer_id: uuid.UUID,
        start_time: datetime,
        end_time: datetime,
        staff_member_id: uuid.UUID | None,
        exclude_id: uuid.UUID | None = None,
    ) -> list[Booking]:
        active_statuses = [BookingStatus.PENDING, BookingStatus.CONFIRMED]
        stmt = select(Booking).where(
            Booking.freelancer_id == freelancer_id,
            Booking.status.in_(active_statuses),
            Booking.start_time < end_time,
            Booking.end_time > start_time,
        )
        if staff_member_id is not None:
            stmt = stmt.where(Booking.staff_member_id == staff_member_id)
        if exclude_id is not None:
            stmt = stmt.where(Booking.id != exclude_id)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def get_upcoming_for_reminder(
        self,
        db: AsyncSession,
        from_dt: datetime,
        to_dt: datetime,
        reminder_type: str,
    ) -> list[Booking]:
        stmt = select(Booking).where(
            Booking.status == BookingStatus.CONFIRMED,
            Booking.start_time >= from_dt,
            Booking.start_time <= to_dt,
        )
        if reminder_type == "24h":
            stmt = stmt.where(Booking.reminder_24h_sent.is_(False))
        elif reminder_type == "2h":
            stmt = stmt.where(Booking.reminder_2h_sent.is_(False))
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def mark_reminder_sent(
        self, db: AsyncSession, booking_id: uuid.UUID, reminder_type: str
    ) -> None:
        if reminder_type == "24h":
            await db.execute(
                update(Booking)
                .where(Booking.id == booking_id)
                .values(reminder_24h_sent=True)
            )
        elif reminder_type == "2h":
            await db.execute(
                update(Booking)
                .where(Booking.id == booking_id)
                .values(reminder_2h_sent=True)
            )
        await db.commit()


class CRUDWaitlist(CRUDBase[WaitlistEntry, WaitlistEntryCreate, WaitlistEntryCreate]):
    async def create(
        self,
        db: AsyncSession,
        freelancer_id: uuid.UUID,
        obj_in: WaitlistEntryCreate,
    ) -> WaitlistEntry:
        entry = WaitlistEntry(
            freelancer_id=freelancer_id,
            **obj_in.model_dump(),
        )
        db.add(entry)
        await db.commit()
        await db.refresh(entry)
        return entry

    async def get_pending_for_service_date(
        self,
        db: AsyncSession,
        freelancer_id: uuid.UUID,
        service_id: uuid.UUID,
        requested_date: date,
    ) -> list[WaitlistEntry]:
        result = await db.execute(
            select(WaitlistEntry).where(
                WaitlistEntry.freelancer_id == freelancer_id,
                WaitlistEntry.service_id == service_id,
                WaitlistEntry.requested_date == requested_date,
                WaitlistEntry.is_notified.is_(False),
                WaitlistEntry.is_booked.is_(False),
            )
        )
        return list(result.scalars().all())

    async def mark_notified(self, db: AsyncSession, entry_id: uuid.UUID) -> None:
        from datetime import timezone

        await db.execute(
            update(WaitlistEntry)
            .where(WaitlistEntry.id == entry_id)
            .values(is_notified=True, notified_at=datetime.now(timezone.utc))
        )
        await db.commit()

    async def get_multi_by_freelancer(
        self, db: AsyncSession, freelancer_id: uuid.UUID
    ) -> list[WaitlistEntry]:
        result = await db.execute(
            select(WaitlistEntry)
            .where(WaitlistEntry.freelancer_id == freelancer_id)
            .order_by(WaitlistEntry.requested_date)
        )
        return list(result.scalars().all())


class CRUDRecurringRule(
    CRUDBase[RecurringBookingRule, RecurringRuleCreate, RecurringRuleCreate]
):
    async def get_multi_by_freelancer(
        self, db: AsyncSession, freelancer_id: uuid.UUID
    ) -> list[RecurringBookingRule]:
        result = await db.execute(
            select(RecurringBookingRule).where(
                RecurringBookingRule.freelancer_id == freelancer_id
            )
        )
        return list(result.scalars().all())

    async def create_for_freelancer(
        self,
        db: AsyncSession,
        freelancer_id: uuid.UUID,
        obj_in: RecurringRuleCreate,
    ) -> RecurringBookingRule:
        rule = RecurringBookingRule(
            freelancer_id=freelancer_id,
            **obj_in.model_dump(),
        )
        db.add(rule)
        await db.commit()
        await db.refresh(rule)
        return rule

    async def deactivate(self, db: AsyncSession, id: uuid.UUID) -> None:
        await db.execute(
            update(RecurringBookingRule)
            .where(RecurringBookingRule.id == id)
            .values(is_active=False)
        )
        await db.commit()

    async def update_last_generated(
        self, db: AsyncSession, id: uuid.UUID, last_date: date
    ) -> None:
        await db.execute(
            update(RecurringBookingRule)
            .where(RecurringBookingRule.id == id)
            .values(last_generated_date=last_date)
        )
        await db.commit()


crud_booking = CRUDBooking(Booking)
crud_waitlist = CRUDWaitlist(WaitlistEntry)
crud_recurring_rule = CRUDRecurringRule(RecurringBookingRule)

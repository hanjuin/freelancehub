from __future__ import annotations

import sys
import uuid
from datetime import date
from pathlib import Path

_PROJECT_ROOT = str(Path(__file__).resolve().parents[4])
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from models import BlockedDate, DayOfWeek, WorkingHours  # noqa: E402

from sqlalchemy import and_, delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.schemas.availability import (
    BlockedDateCreate,
    BlockedDateUpdate,
    WorkingHoursCreate,
    WorkingHoursUpdate,
)


class CRUDWorkingHours(CRUDBase[WorkingHours, WorkingHoursCreate, WorkingHoursUpdate]):
    async def get_by_freelancer(
        self,
        db: AsyncSession,
        freelancer_id: uuid.UUID,
        staff_member_id: uuid.UUID | None = None,
    ) -> list[WorkingHours]:
        stmt = select(WorkingHours).where(
            WorkingHours.freelancer_id == freelancer_id
        )
        if staff_member_id is not None:
            stmt = stmt.where(WorkingHours.staff_member_id == staff_member_id)
        else:
            stmt = stmt.where(WorkingHours.staff_member_id.is_(None))
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def upsert(
        self,
        db: AsyncSession,
        freelancer_id: uuid.UUID,
        obj_in: WorkingHoursCreate,
    ) -> WorkingHours:
        stmt = select(WorkingHours).where(
            WorkingHours.freelancer_id == freelancer_id,
            WorkingHours.day_of_week == obj_in.day_of_week,
            WorkingHours.staff_member_id == obj_in.staff_member_id
            if obj_in.staff_member_id
            else WorkingHours.staff_member_id.is_(None),
        )
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            data = obj_in.model_dump(exclude_unset=True, exclude={"staff_member_id"})
            for key, value in data.items():
                setattr(existing, key, value)
            db.add(existing)
            await db.commit()
            await db.refresh(existing)
            return existing
        else:
            wh = WorkingHours(
                freelancer_id=freelancer_id,
                **obj_in.model_dump(),
            )
            db.add(wh)
            await db.commit()
            await db.refresh(wh)
            return wh

    async def bulk_upsert(
        self,
        db: AsyncSession,
        freelancer_id: uuid.UUID,
        items: list[WorkingHoursCreate],
    ) -> list[WorkingHours]:
        results = []
        for item in items:
            wh = await self.upsert(db, freelancer_id, item)
            results.append(wh)
        return results

    async def delete_day(
        self,
        db: AsyncSession,
        freelancer_id: uuid.UUID,
        day_of_week: DayOfWeek,
        staff_member_id: uuid.UUID | None,
    ) -> None:
        conditions = [
            WorkingHours.freelancer_id == freelancer_id,
            WorkingHours.day_of_week == day_of_week,
        ]
        if staff_member_id is not None:
            conditions.append(WorkingHours.staff_member_id == staff_member_id)
        else:
            conditions.append(WorkingHours.staff_member_id.is_(None))
        await db.execute(delete(WorkingHours).where(and_(*conditions)))
        await db.commit()


class CRUDBlockedDate(CRUDBase[BlockedDate, BlockedDateCreate, BlockedDateUpdate]):
    async def get_multi_by_freelancer(
        self,
        db: AsyncSession,
        freelancer_id: uuid.UUID,
        *,
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> list[BlockedDate]:
        stmt = select(BlockedDate).where(BlockedDate.freelancer_id == freelancer_id)
        if from_date is not None:
            stmt = stmt.where(BlockedDate.end_date >= from_date)
        if to_date is not None:
            stmt = stmt.where(BlockedDate.start_date <= to_date)
        stmt = stmt.order_by(BlockedDate.start_date)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def create_for_freelancer(
        self,
        db: AsyncSession,
        freelancer_id: uuid.UUID,
        obj_in: BlockedDateCreate,
    ) -> BlockedDate:
        bd = BlockedDate(
            freelancer_id=freelancer_id,
            **obj_in.model_dump(),
        )
        db.add(bd)
        await db.commit()
        await db.refresh(bd)
        return bd

    async def delete_for_freelancer(
        self,
        db: AsyncSession,
        freelancer_id: uuid.UUID,
        id: uuid.UUID,
    ) -> BlockedDate | None:
        result = await db.execute(
            select(BlockedDate).where(
                BlockedDate.freelancer_id == freelancer_id,
                BlockedDate.id == id,
            )
        )
        bd = result.scalar_one_or_none()
        if bd:
            await db.delete(bd)
            await db.commit()
        return bd


crud_working_hours = CRUDWorkingHours(WorkingHours)
crud_blocked_date = CRUDBlockedDate(BlockedDate)

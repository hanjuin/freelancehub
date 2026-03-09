from __future__ import annotations

import sys
import uuid
from pathlib import Path

_PROJECT_ROOT = str(Path(__file__).resolve().parents[4])
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from models import StaffMember  # noqa: E402

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.schemas.staff import StaffMemberCreate, StaffMemberUpdate


class CRUDStaffMember(CRUDBase[StaffMember, StaffMemberCreate, StaffMemberUpdate]):
    async def get_multi_by_freelancer(
        self,
        db: AsyncSession,
        freelancer_id: uuid.UUID,
        *,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = False,
    ) -> list[StaffMember]:
        stmt = select(StaffMember).where(StaffMember.freelancer_id == freelancer_id)
        if active_only:
            stmt = stmt.where(StaffMember.is_active.is_(True))
        stmt = stmt.order_by(StaffMember.first_name).offset(skip).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_freelancer(
        self, db: AsyncSession, freelancer_id: uuid.UUID, id: uuid.UUID
    ) -> StaffMember | None:
        result = await db.execute(
            select(StaffMember).where(
                StaffMember.freelancer_id == freelancer_id,
                StaffMember.id == id,
            )
        )
        return result.scalar_one_or_none()

    async def create_for_freelancer(
        self,
        db: AsyncSession,
        freelancer_id: uuid.UUID,
        obj_in: StaffMemberCreate,
    ) -> StaffMember:
        staff = StaffMember(
            freelancer_id=freelancer_id,
            **obj_in.model_dump(),
        )
        db.add(staff)
        await db.commit()
        await db.refresh(staff)
        return staff

    async def update_for_freelancer(
        self,
        db: AsyncSession,
        freelancer_id: uuid.UUID,
        id: uuid.UUID,
        obj_in: StaffMemberUpdate,
    ) -> StaffMember | None:
        staff = await self.get_by_freelancer(db, freelancer_id, id)
        if not staff:
            return None
        return await self.update(db, db_obj=staff, obj_in=obj_in)

    async def delete_for_freelancer(
        self,
        db: AsyncSession,
        freelancer_id: uuid.UUID,
        id: uuid.UUID,
    ) -> StaffMember | None:
        staff = await self.get_by_freelancer(db, freelancer_id, id)
        if not staff:
            return None
        await db.delete(staff)
        await db.commit()
        return staff


crud_staff = CRUDStaffMember(StaffMember)

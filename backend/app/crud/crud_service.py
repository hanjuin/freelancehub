from __future__ import annotations

import sys
import uuid
from pathlib import Path

_PROJECT_ROOT = str(Path(__file__).resolve().parents[4])
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from models import Service  # noqa: E402

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.schemas.service import ServiceCreate, ServiceUpdate


class CRUDService(CRUDBase[Service, ServiceCreate, ServiceUpdate]):
    async def get_multi_by_freelancer(
        self,
        db: AsyncSession,
        freelancer_id: uuid.UUID,
        *,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = False,
    ) -> list[Service]:
        stmt = select(Service).where(Service.freelancer_id == freelancer_id)
        if active_only:
            stmt = stmt.where(Service.is_active.is_(True))
        stmt = stmt.order_by(Service.sort_order, Service.name).offset(skip).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_freelancer(
        self, db: AsyncSession, freelancer_id: uuid.UUID, id: uuid.UUID
    ) -> Service | None:
        result = await db.execute(
            select(Service).where(
                Service.freelancer_id == freelancer_id,
                Service.id == id,
            )
        )
        return result.scalar_one_or_none()

    async def create_for_freelancer(
        self,
        db: AsyncSession,
        freelancer_id: uuid.UUID,
        obj_in: ServiceCreate,
    ) -> Service:
        service = Service(
            freelancer_id=freelancer_id,
            **obj_in.model_dump(),
        )
        db.add(service)
        await db.commit()
        await db.refresh(service)
        return service

    async def update_for_freelancer(
        self,
        db: AsyncSession,
        freelancer_id: uuid.UUID,
        id: uuid.UUID,
        obj_in: ServiceUpdate,
    ) -> Service | None:
        service = await self.get_by_freelancer(db, freelancer_id, id)
        if not service:
            return None
        return await self.update(db, db_obj=service, obj_in=obj_in)

    async def delete_for_freelancer(
        self,
        db: AsyncSession,
        freelancer_id: uuid.UUID,
        id: uuid.UUID,
    ) -> Service | None:
        service = await self.get_by_freelancer(db, freelancer_id, id)
        if not service:
            return None
        await db.delete(service)
        await db.commit()
        return service


crud_service = CRUDService(Service)

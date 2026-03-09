from __future__ import annotations

import sys
import uuid
from pathlib import Path

_PROJECT_ROOT = str(Path(__file__).resolve().parents[4])
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from models import ServiceCategory  # noqa: E402

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase


class CRUDServiceCategory(CRUDBase[ServiceCategory, ServiceCategory, ServiceCategory]):
    async def get_by_slug(
        self, db: AsyncSession, slug: str
    ) -> ServiceCategory | None:
        result = await db.execute(
            select(ServiceCategory).where(ServiceCategory.slug == slug)
        )
        return result.scalar_one_or_none()

    async def get_all_for_freelancer(
        self, db: AsyncSession, freelancer_id: uuid.UUID
    ) -> list[ServiceCategory]:
        result = await db.execute(
            select(ServiceCategory).where(
                or_(
                    ServiceCategory.is_system.is_(True),
                    ServiceCategory.created_by_id == freelancer_id,
                )
            ).order_by(ServiceCategory.name)
        )
        return list(result.scalars().all())


crud_service_category = CRUDServiceCategory(ServiceCategory)

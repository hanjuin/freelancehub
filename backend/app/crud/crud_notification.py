from __future__ import annotations

import sys
import uuid
from datetime import datetime
from pathlib import Path

_PROJECT_ROOT = str(Path(__file__).resolve().parents[4])
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from models import Notification, NotificationType  # noqa: E402

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase


class CRUDNotification(CRUDBase[Notification, Notification, Notification]):
    async def get_multi_by_freelancer(
        self,
        db: AsyncSession,
        freelancer_id: uuid.UUID,
        *,
        unread_only: bool = False,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[Notification], int]:
        stmt = select(Notification).where(Notification.freelancer_id == freelancer_id)
        if unread_only:
            stmt = stmt.where(Notification.is_read.is_(False))

        count_stmt = select(func.count()).select_from(stmt.subquery())
        count_result = await db.execute(count_stmt)
        total = count_result.scalar_one()

        stmt = stmt.order_by(Notification.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all()), total

    async def create(
        self,
        db: AsyncSession,
        freelancer_id: uuid.UUID,
        type: NotificationType,
        title: str,
        body: str | None,
        entity_type: str | None,
        entity_id: uuid.UUID | None,
    ) -> Notification:
        notification = Notification(
            freelancer_id=freelancer_id,
            type=type,
            title=title,
            body=body,
            entity_type=entity_type,
            entity_id=entity_id,
        )
        db.add(notification)
        await db.commit()
        await db.refresh(notification)
        return notification

    async def mark_read(
        self,
        db: AsyncSession,
        freelancer_id: uuid.UUID,
        notification_ids: list[uuid.UUID],
    ) -> int:
        from datetime import timezone

        now = datetime.now(timezone.utc)
        result = await db.execute(
            update(Notification)
            .where(
                Notification.freelancer_id == freelancer_id,
                Notification.id.in_(notification_ids),
                Notification.is_read.is_(False),
            )
            .values(is_read=True, read_at=now)
        )
        await db.commit()
        return result.rowcount  # type: ignore[return-value]

    async def mark_all_read(
        self, db: AsyncSession, freelancer_id: uuid.UUID
    ) -> int:
        from datetime import timezone

        now = datetime.now(timezone.utc)
        result = await db.execute(
            update(Notification)
            .where(
                Notification.freelancer_id == freelancer_id,
                Notification.is_read.is_(False),
            )
            .values(is_read=True, read_at=now)
        )
        await db.commit()
        return result.rowcount  # type: ignore[return-value]

    async def get_unread_count(
        self, db: AsyncSession, freelancer_id: uuid.UUID
    ) -> int:
        result = await db.execute(
            select(func.count()).where(
                Notification.freelancer_id == freelancer_id,
                Notification.is_read.is_(False),
            )
        )
        return result.scalar_one()


crud_notification = CRUDNotification(Notification)

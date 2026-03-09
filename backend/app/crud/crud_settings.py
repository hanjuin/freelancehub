from __future__ import annotations

import sys
import uuid
from pathlib import Path

_PROJECT_ROOT = str(Path(__file__).resolve().parents[4])
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from models import FreelancerSettings, NotificationPreferences  # noqa: E402

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.schemas.settings import (
    FreelancerSettingsUpdate,
    NotificationPreferencesUpdate,
)


class CRUDFreelancerSettings(
    CRUDBase[FreelancerSettings, FreelancerSettingsUpdate, FreelancerSettingsUpdate]
):
    async def get_by_freelancer(
        self, db: AsyncSession, freelancer_id: uuid.UUID
    ) -> FreelancerSettings | None:
        result = await db.execute(
            select(FreelancerSettings).where(
                FreelancerSettings.freelancer_id == freelancer_id
            )
        )
        return result.scalar_one_or_none()

    async def get_or_create(
        self, db: AsyncSession, freelancer_id: uuid.UUID
    ) -> FreelancerSettings:
        existing = await self.get_by_freelancer(db, freelancer_id)
        if existing:
            return existing
        settings_obj = FreelancerSettings(freelancer_id=freelancer_id)
        db.add(settings_obj)
        await db.commit()
        await db.refresh(settings_obj)
        return settings_obj

    async def update(  # type: ignore[override]
        self,
        db: AsyncSession,
        freelancer_id: uuid.UUID,
        obj_in: FreelancerSettingsUpdate,
    ) -> FreelancerSettings:
        settings_obj = await self.get_or_create(db, freelancer_id)
        update_data = obj_in.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(settings_obj, key, value)
        db.add(settings_obj)
        await db.commit()
        await db.refresh(settings_obj)
        return settings_obj


class CRUDNotificationPreferences(
    CRUDBase[
        NotificationPreferences,
        NotificationPreferencesUpdate,
        NotificationPreferencesUpdate,
    ]
):
    async def get_or_create(
        self, db: AsyncSession, freelancer_id: uuid.UUID
    ) -> NotificationPreferences:
        result = await db.execute(
            select(NotificationPreferences).where(
                NotificationPreferences.freelancer_id == freelancer_id
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            return existing
        prefs = NotificationPreferences(freelancer_id=freelancer_id)
        db.add(prefs)
        await db.commit()
        await db.refresh(prefs)
        return prefs

    async def update(  # type: ignore[override]
        self,
        db: AsyncSession,
        freelancer_id: uuid.UUID,
        obj_in: NotificationPreferencesUpdate,
    ) -> NotificationPreferences:
        prefs = await self.get_or_create(db, freelancer_id)
        update_data = obj_in.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(prefs, key, value)
        db.add(prefs)
        await db.commit()
        await db.refresh(prefs)
        return prefs


crud_settings = CRUDFreelancerSettings(FreelancerSettings)
crud_notification_prefs = CRUDNotificationPreferences(NotificationPreferences)

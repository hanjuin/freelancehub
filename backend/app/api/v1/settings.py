from __future__ import annotations

import sys
from pathlib import Path

_PROJECT_ROOT = str(Path(__file__).resolve().parents[4])
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from models import Freelancer  # noqa: E402

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_freelancer
from app.crud.crud_settings import crud_notification_prefs, crud_settings
from app.db.session import get_db
from app.schemas.settings import (
    FreelancerSettingsResponse,
    FreelancerSettingsUpdate,
    NotificationPreferencesResponse,
    NotificationPreferencesUpdate,
)

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/", response_model=FreelancerSettingsResponse)
async def get_settings(
    db: AsyncSession = Depends(get_db),
    current_freelancer: Freelancer = Depends(get_current_active_freelancer),
) -> FreelancerSettingsResponse:
    settings_obj = await crud_settings.get_or_create(db, current_freelancer.id)
    return FreelancerSettingsResponse.model_validate(settings_obj)


@router.put("/", response_model=FreelancerSettingsResponse)
async def update_settings(
    obj_in: FreelancerSettingsUpdate,
    db: AsyncSession = Depends(get_db),
    current_freelancer: Freelancer = Depends(get_current_active_freelancer),
) -> FreelancerSettingsResponse:
    settings_obj = await crud_settings.update(db, current_freelancer.id, obj_in)
    return FreelancerSettingsResponse.model_validate(settings_obj)


@router.get("/notifications", response_model=NotificationPreferencesResponse)
async def get_notification_preferences(
    db: AsyncSession = Depends(get_db),
    current_freelancer: Freelancer = Depends(get_current_active_freelancer),
) -> NotificationPreferencesResponse:
    prefs = await crud_notification_prefs.get_or_create(db, current_freelancer.id)
    return NotificationPreferencesResponse.model_validate(prefs)


@router.put("/notifications", response_model=NotificationPreferencesResponse)
async def update_notification_preferences(
    obj_in: NotificationPreferencesUpdate,
    db: AsyncSession = Depends(get_db),
    current_freelancer: Freelancer = Depends(get_current_active_freelancer),
) -> NotificationPreferencesResponse:
    prefs = await crud_notification_prefs.update(db, current_freelancer.id, obj_in)
    return NotificationPreferencesResponse.model_validate(prefs)

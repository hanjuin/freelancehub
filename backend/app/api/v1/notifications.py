from __future__ import annotations

import sys
from pathlib import Path

_PROJECT_ROOT = str(Path(__file__).resolve().parents[4])
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from models import Freelancer  # noqa: E402

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_freelancer
from app.crud.crud_notification import crud_notification
from app.db.session import get_db
from app.schemas.common import PaginatedResponse
from app.schemas.notification import MarkReadRequest, NotificationResponse

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/count")
async def get_unread_count(
    db: AsyncSession = Depends(get_db),
    current_freelancer: Freelancer = Depends(get_current_active_freelancer),
) -> dict[str, int]:
    count = await crud_notification.get_unread_count(db, current_freelancer.id)
    return {"unread": count}


@router.get("/", response_model=PaginatedResponse[NotificationResponse])
async def list_notifications(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    unread_only: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
    current_freelancer: Freelancer = Depends(get_current_active_freelancer),
) -> PaginatedResponse[NotificationResponse]:
    skip = (page - 1) * page_size
    notifications, total = await crud_notification.get_multi_by_freelancer(
        db,
        current_freelancer.id,
        unread_only=unread_only,
        skip=skip,
        limit=page_size,
    )
    pages = max(1, (total + page_size - 1) // page_size)
    return PaginatedResponse(
        items=[NotificationResponse.model_validate(n) for n in notifications],
        total=total,
        page=page,
        pages=pages,
    )


@router.post("/mark-read")
async def mark_notifications_read(
    body: MarkReadRequest,
    db: AsyncSession = Depends(get_db),
    current_freelancer: Freelancer = Depends(get_current_active_freelancer),
) -> dict[str, int]:
    updated = await crud_notification.mark_read(
        db, current_freelancer.id, body.notification_ids
    )
    return {"updated": updated}


@router.post("/mark-all-read")
async def mark_all_notifications_read(
    db: AsyncSession = Depends(get_db),
    current_freelancer: Freelancer = Depends(get_current_active_freelancer),
) -> dict[str, int]:
    updated = await crud_notification.mark_all_read(db, current_freelancer.id)
    return {"updated": updated}

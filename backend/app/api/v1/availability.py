from __future__ import annotations

import sys
import uuid
from datetime import date
from pathlib import Path

_PROJECT_ROOT = str(Path(__file__).resolve().parents[4])
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from models import Freelancer  # noqa: E402

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_freelancer
from app.crud.crud_availability import crud_blocked_date, crud_working_hours
from app.db.session import get_db
from app.schemas.availability import (
    BlockedDateCreate,
    BlockedDateResponse,
    WorkingHoursCreate,
    WorkingHoursResponse,
)

router = APIRouter(prefix="/availability", tags=["availability"])


@router.get("/working-hours", response_model=list[WorkingHoursResponse])
async def get_working_hours(
    staff_member_id: uuid.UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_freelancer: Freelancer = Depends(get_current_active_freelancer),
) -> list[WorkingHoursResponse]:
    hours = await crud_working_hours.get_by_freelancer(
        db, current_freelancer.id, staff_member_id=staff_member_id
    )
    return [WorkingHoursResponse.model_validate(h) for h in hours]


@router.put("/working-hours", response_model=list[WorkingHoursResponse])
async def upsert_working_hours(
    items: list[WorkingHoursCreate],
    db: AsyncSession = Depends(get_db),
    current_freelancer: Freelancer = Depends(get_current_active_freelancer),
) -> list[WorkingHoursResponse]:
    results = await crud_working_hours.bulk_upsert(db, current_freelancer.id, items)
    return [WorkingHoursResponse.model_validate(h) for h in results]


@router.get("/blocked-dates", response_model=list[BlockedDateResponse])
async def get_blocked_dates(
    from_date: date | None = Query(default=None, alias="from"),
    to_date: date | None = Query(default=None, alias="to"),
    db: AsyncSession = Depends(get_db),
    current_freelancer: Freelancer = Depends(get_current_active_freelancer),
) -> list[BlockedDateResponse]:
    blocked = await crud_blocked_date.get_multi_by_freelancer(
        db,
        current_freelancer.id,
        from_date=from_date,
        to_date=to_date,
    )
    return [BlockedDateResponse.model_validate(b) for b in blocked]


@router.post(
    "/blocked-dates",
    response_model=BlockedDateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_blocked_date(
    obj_in: BlockedDateCreate,
    db: AsyncSession = Depends(get_db),
    current_freelancer: Freelancer = Depends(get_current_active_freelancer),
) -> BlockedDateResponse:
    blocked = await crud_blocked_date.create_for_freelancer(
        db, current_freelancer.id, obj_in
    )
    return BlockedDateResponse.model_validate(blocked)


@router.delete("/blocked-dates/{blocked_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_blocked_date(
    blocked_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_freelancer: Freelancer = Depends(get_current_active_freelancer),
) -> None:
    result = await crud_blocked_date.delete_for_freelancer(
        db, current_freelancer.id, blocked_id
    )
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Blocked date not found",
        )

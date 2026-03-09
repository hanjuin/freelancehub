from __future__ import annotations

import sys
import uuid
from pathlib import Path

_PROJECT_ROOT = str(Path(__file__).resolve().parents[4])
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from models import Freelancer  # noqa: E402

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_freelancer
from app.crud.crud_staff import crud_staff
from app.db.session import get_db
from app.schemas.common import MessageResponse
from app.schemas.staff import StaffMemberCreate, StaffMemberResponse, StaffMemberUpdate

router = APIRouter(prefix="/staff", tags=["staff"])


@router.get("/", response_model=list[StaffMemberResponse])
async def list_staff(
    active_only: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
    current_freelancer: Freelancer = Depends(get_current_active_freelancer),
) -> list[StaffMemberResponse]:
    staff = await crud_staff.get_multi_by_freelancer(
        db, current_freelancer.id, active_only=active_only
    )
    return [StaffMemberResponse.model_validate(s) for s in staff]


@router.post("/", response_model=StaffMemberResponse, status_code=status.HTTP_201_CREATED)
async def create_staff(
    obj_in: StaffMemberCreate,
    db: AsyncSession = Depends(get_db),
    current_freelancer: Freelancer = Depends(get_current_active_freelancer),
) -> StaffMemberResponse:
    staff = await crud_staff.create_for_freelancer(db, current_freelancer.id, obj_in)
    return StaffMemberResponse.model_validate(staff)


@router.get("/{staff_id}", response_model=StaffMemberResponse)
async def get_staff_member(
    staff_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_freelancer: Freelancer = Depends(get_current_active_freelancer),
) -> StaffMemberResponse:
    staff = await crud_staff.get_by_freelancer(db, current_freelancer.id, staff_id)
    if not staff:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff member not found")
    return StaffMemberResponse.model_validate(staff)


@router.put("/{staff_id}", response_model=StaffMemberResponse)
async def update_staff_member(
    staff_id: uuid.UUID,
    obj_in: StaffMemberUpdate,
    db: AsyncSession = Depends(get_db),
    current_freelancer: Freelancer = Depends(get_current_active_freelancer),
) -> StaffMemberResponse:
    staff = await crud_staff.update_for_freelancer(
        db, current_freelancer.id, staff_id, obj_in
    )
    if not staff:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff member not found")
    return StaffMemberResponse.model_validate(staff)


@router.delete("/{staff_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_staff_member(
    staff_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_freelancer: Freelancer = Depends(get_current_active_freelancer),
) -> None:
    staff = await crud_staff.delete_for_freelancer(
        db, current_freelancer.id, staff_id
    )
    if not staff:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff member not found")

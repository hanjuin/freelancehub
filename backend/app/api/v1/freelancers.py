from __future__ import annotations

import sys
from pathlib import Path

_PROJECT_ROOT = str(Path(__file__).resolve().parents[4])
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from models import Freelancer  # noqa: E402

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_freelancer
from app.db.session import get_db
from app.schemas.common import MessageResponse
from app.schemas.freelancer import FreelancerResponse, FreelancerUpdate

router = APIRouter(prefix="/freelancers", tags=["freelancers"])


@router.get("/me", response_model=FreelancerResponse)
async def get_me(
    current_freelancer: Freelancer = Depends(get_current_active_freelancer),
) -> FreelancerResponse:
    return FreelancerResponse.model_validate(current_freelancer)


@router.put("/me", response_model=FreelancerResponse)
async def update_me(
    obj_in: FreelancerUpdate,
    db: AsyncSession = Depends(get_db),
    current_freelancer: Freelancer = Depends(get_current_active_freelancer),
) -> FreelancerResponse:
    update_data = obj_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(current_freelancer, key, value)
    db.add(current_freelancer)
    await db.commit()
    await db.refresh(current_freelancer)
    return FreelancerResponse.model_validate(current_freelancer)


@router.delete("/me", response_model=MessageResponse)
async def deactivate_me(
    db: AsyncSession = Depends(get_db),
    current_freelancer: Freelancer = Depends(get_current_active_freelancer),
) -> MessageResponse:
    current_freelancer.is_active = False
    db.add(current_freelancer)
    await db.commit()
    return MessageResponse(message="Account deactivated")

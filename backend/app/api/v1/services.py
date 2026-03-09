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
from app.crud.crud_service import crud_service
from app.crud.crud_service_category import crud_service_category
from app.db.session import get_db
from app.schemas.common import MessageResponse, PaginatedResponse, PaginationParams
from app.schemas.service import (
    ServiceCategoryResponse,
    ServiceCreate,
    ServiceResponse,
    ServiceUpdate,
)

router = APIRouter(prefix="/services", tags=["services"])


@router.get("/categories", response_model=list[ServiceCategoryResponse])
async def list_categories(
    db: AsyncSession = Depends(get_db),
) -> list[ServiceCategoryResponse]:
    categories = await crud_service_category.get_multi(db, skip=0, limit=200)
    return [ServiceCategoryResponse.model_validate(c) for c in categories]


@router.get("/", response_model=PaginatedResponse[ServiceResponse])
async def list_services(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    active_only: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
    current_freelancer: Freelancer = Depends(get_current_active_freelancer),
) -> PaginatedResponse[ServiceResponse]:
    skip = (page - 1) * page_size
    services = await crud_service.get_multi_by_freelancer(
        db,
        current_freelancer.id,
        skip=skip,
        limit=page_size,
        active_only=active_only,
    )
    # Get total count
    all_services = await crud_service.get_multi_by_freelancer(
        db, current_freelancer.id, skip=0, limit=10000, active_only=active_only
    )
    total = len(all_services)
    pages = max(1, (total + page_size - 1) // page_size)
    return PaginatedResponse(
        items=[ServiceResponse.model_validate(s) for s in services],
        total=total,
        page=page,
        pages=pages,
    )


@router.post("/", response_model=ServiceResponse, status_code=status.HTTP_201_CREATED)
async def create_service(
    obj_in: ServiceCreate,
    db: AsyncSession = Depends(get_db),
    current_freelancer: Freelancer = Depends(get_current_active_freelancer),
) -> ServiceResponse:
    service = await crud_service.create_for_freelancer(
        db, current_freelancer.id, obj_in
    )
    return ServiceResponse.model_validate(service)


@router.get("/{service_id}", response_model=ServiceResponse)
async def get_service(
    service_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_freelancer: Freelancer = Depends(get_current_active_freelancer),
) -> ServiceResponse:
    service = await crud_service.get_by_freelancer(db, current_freelancer.id, service_id)
    if not service:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")
    return ServiceResponse.model_validate(service)


@router.put("/{service_id}", response_model=ServiceResponse)
async def update_service(
    service_id: uuid.UUID,
    obj_in: ServiceUpdate,
    db: AsyncSession = Depends(get_db),
    current_freelancer: Freelancer = Depends(get_current_active_freelancer),
) -> ServiceResponse:
    service = await crud_service.update_for_freelancer(
        db, current_freelancer.id, service_id, obj_in
    )
    if not service:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")
    return ServiceResponse.model_validate(service)


@router.delete("/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_service(
    service_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_freelancer: Freelancer = Depends(get_current_active_freelancer),
) -> None:
    service = await crud_service.delete_for_freelancer(
        db, current_freelancer.id, service_id
    )
    if not service:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")

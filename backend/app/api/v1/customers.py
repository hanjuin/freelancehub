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
from app.crud.crud_booking import crud_booking
from app.crud.crud_customer import crud_customer, crud_customer_tag
from app.crud.crud_invoice import crud_invoice
from app.db.session import get_db
from app.schemas.booking import BookingResponse
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.customer import (
    CustomerCreate,
    CustomerResponse,
    CustomerTagCreate,
    CustomerTagResponse,
    CustomerTagUpdate,
    CustomerUpdate,
)
from app.schemas.invoice import InvoiceResponse

router = APIRouter(prefix="/customers", tags=["customers"])


@router.get("/tags", response_model=list[CustomerTagResponse])
async def list_tags(
    db: AsyncSession = Depends(get_db),
    current_freelancer: Freelancer = Depends(get_current_active_freelancer),
) -> list[CustomerTagResponse]:
    tags = await crud_customer_tag.get_multi_by_freelancer(db, current_freelancer.id)
    return [CustomerTagResponse.model_validate(t) for t in tags]


@router.post(
    "/tags",
    response_model=CustomerTagResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_tag(
    obj_in: CustomerTagCreate,
    db: AsyncSession = Depends(get_db),
    current_freelancer: Freelancer = Depends(get_current_active_freelancer),
) -> CustomerTagResponse:
    tag = await crud_customer_tag.create_for_freelancer(db, current_freelancer.id, obj_in)
    return CustomerTagResponse.model_validate(tag)


@router.put("/tags/{tag_id}", response_model=CustomerTagResponse)
async def update_tag(
    tag_id: uuid.UUID,
    obj_in: CustomerTagUpdate,
    db: AsyncSession = Depends(get_db),
    current_freelancer: Freelancer = Depends(get_current_active_freelancer),
) -> CustomerTagResponse:
    tag = await crud_customer_tag.update_for_freelancer(
        db, current_freelancer.id, tag_id, obj_in
    )
    if not tag:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found")
    return CustomerTagResponse.model_validate(tag)


@router.delete("/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag(
    tag_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_freelancer: Freelancer = Depends(get_current_active_freelancer),
) -> None:
    tag = await crud_customer_tag.delete_for_freelancer(
        db, current_freelancer.id, tag_id
    )
    if not tag:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found")


@router.get("/", response_model=PaginatedResponse[CustomerResponse])
async def list_customers(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: str | None = Query(default=None),
    active_only: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
    current_freelancer: Freelancer = Depends(get_current_active_freelancer),
) -> PaginatedResponse[CustomerResponse]:
    skip = (page - 1) * page_size
    customers, total = await crud_customer.get_multi_by_freelancer(
        db,
        current_freelancer.id,
        skip=skip,
        limit=page_size,
        search=search,
        active_only=active_only,
    )
    pages = max(1, (total + page_size - 1) // page_size)
    return PaginatedResponse(
        items=[CustomerResponse.model_validate(c) for c in customers],
        total=total,
        page=page,
        pages=pages,
    )


@router.post("/", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
async def create_customer(
    obj_in: CustomerCreate,
    db: AsyncSession = Depends(get_db),
    current_freelancer: Freelancer = Depends(get_current_active_freelancer),
) -> CustomerResponse:
    customer = await crud_customer.create_for_freelancer(
        db, current_freelancer.id, obj_in
    )
    return CustomerResponse.model_validate(customer)


@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_freelancer: Freelancer = Depends(get_current_active_freelancer),
) -> CustomerResponse:
    customer = await crud_customer.get_by_freelancer(db, current_freelancer.id, customer_id)
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
    return CustomerResponse.model_validate(customer)


@router.put("/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: uuid.UUID,
    obj_in: CustomerUpdate,
    db: AsyncSession = Depends(get_db),
    current_freelancer: Freelancer = Depends(get_current_active_freelancer),
) -> CustomerResponse:
    customer = await crud_customer.update_for_freelancer(
        db, current_freelancer.id, customer_id, obj_in
    )
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
    return CustomerResponse.model_validate(customer)


@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_customer(
    customer_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_freelancer: Freelancer = Depends(get_current_active_freelancer),
) -> None:
    customer = await crud_customer.delete_for_freelancer(
        db, current_freelancer.id, customer_id
    )
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")


@router.get("/{customer_id}/bookings", response_model=list[BookingResponse])
async def get_customer_bookings(
    customer_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_freelancer: Freelancer = Depends(get_current_active_freelancer),
) -> list[BookingResponse]:
    customer = await crud_customer.get_by_freelancer(db, current_freelancer.id, customer_id)
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
    bookings, _ = await crud_booking.get_multi_by_freelancer(
        db,
        current_freelancer.id,
        skip=0,
        limit=200,
        customer_id=customer_id,
    )
    return [BookingResponse.model_validate(b) for b in bookings]


@router.get("/{customer_id}/invoices", response_model=list[InvoiceResponse])
async def get_customer_invoices(
    customer_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_freelancer: Freelancer = Depends(get_current_active_freelancer),
) -> list[InvoiceResponse]:
    from sqlalchemy import select
    from models import Invoice
    from sqlalchemy.orm import selectinload

    customer = await crud_customer.get_by_freelancer(db, current_freelancer.id, customer_id)
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")

    result = await db.execute(
        select(Invoice)
        .where(
            Invoice.freelancer_id == current_freelancer.id,
            Invoice.customer_id == customer_id,
        )
        .options(selectinload(Invoice.line_items))
        .order_by(Invoice.issue_date.desc())
    )
    invoices = list(result.scalars().all())
    return [InvoiceResponse.model_validate(i) for i in invoices]


@router.post("/{customer_id}/tags/{tag_id}", response_model=MessageResponse)
async def add_tag_to_customer(
    customer_id: uuid.UUID,
    tag_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_freelancer: Freelancer = Depends(get_current_active_freelancer),
) -> MessageResponse:
    customer = await crud_customer.get_by_freelancer(db, current_freelancer.id, customer_id)
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
    tag = await crud_customer_tag.get_by_freelancer(db, current_freelancer.id, tag_id)
    if not tag:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found")
    await crud_customer.add_tag(db, customer_id=customer_id, tag_id=tag_id)
    return MessageResponse(message="Tag added")


@router.delete(
    "/{customer_id}/tags/{tag_id}",
    response_model=MessageResponse,
)
async def remove_tag_from_customer(
    customer_id: uuid.UUID,
    tag_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_freelancer: Freelancer = Depends(get_current_active_freelancer),
) -> MessageResponse:
    customer = await crud_customer.get_by_freelancer(db, current_freelancer.id, customer_id)
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
    await crud_customer.remove_tag(db, customer_id=customer_id, tag_id=tag_id)
    return MessageResponse(message="Tag removed")

from __future__ import annotations

import sys
import uuid
from datetime import datetime
from pathlib import Path

_PROJECT_ROOT = str(Path(__file__).resolve().parents[4])
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from models import Freelancer, InvoiceStatus  # noqa: E402

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_freelancer
from app.crud.crud_invoice import crud_invoice
from app.crud.crud_settings import crud_settings
from app.db.session import get_db
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.invoice import InvoiceCreate, InvoiceResponse, InvoiceUpdate

router = APIRouter(prefix="/invoices", tags=["invoices"])


@router.get("/", response_model=PaginatedResponse[InvoiceResponse])
async def list_invoices(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    invoice_status: InvoiceStatus | None = Query(default=None, alias="status"),
    db: AsyncSession = Depends(get_db),
    current_freelancer: Freelancer = Depends(get_current_active_freelancer),
) -> PaginatedResponse[InvoiceResponse]:
    skip = (page - 1) * page_size
    invoices, total = await crud_invoice.get_multi_by_freelancer(
        db,
        current_freelancer.id,
        skip=skip,
        limit=page_size,
        status=invoice_status,
    )
    pages = max(1, (total + page_size - 1) // page_size)
    return PaginatedResponse(
        items=[InvoiceResponse.model_validate(i) for i in invoices],
        total=total,
        page=page,
        pages=pages,
    )


@router.post("/", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
async def create_invoice(
    obj_in: InvoiceCreate,
    db: AsyncSession = Depends(get_db),
    current_freelancer: Freelancer = Depends(get_current_active_freelancer),
) -> InvoiceResponse:
    settings_obj = await crud_settings.get_or_create(db, current_freelancer.id)
    invoice = await crud_invoice.create_for_freelancer(
        db,
        current_freelancer.id,
        obj_in,
        tax_rate_bps=settings_obj.tax_rate_bps,
    )
    return InvoiceResponse.model_validate(invoice)


@router.get("/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(
    invoice_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_freelancer: Freelancer = Depends(get_current_active_freelancer),
) -> InvoiceResponse:
    invoice = await crud_invoice.get_by_freelancer(db, current_freelancer.id, invoice_id)
    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    return InvoiceResponse.model_validate(invoice)


@router.put("/{invoice_id}", response_model=InvoiceResponse)
async def update_invoice(
    invoice_id: uuid.UUID,
    obj_in: InvoiceUpdate,
    db: AsyncSession = Depends(get_db),
    current_freelancer: Freelancer = Depends(get_current_active_freelancer),
) -> InvoiceResponse:
    invoice = await crud_invoice.get_by_freelancer(db, current_freelancer.id, invoice_id)
    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    update_data = obj_in.model_dump(exclude_unset=True, exclude={"line_items"})
    for key, value in update_data.items():
        setattr(invoice, key, value)
    db.add(invoice)
    await db.commit()
    await db.refresh(invoice)
    return InvoiceResponse.model_validate(invoice)


@router.post("/{invoice_id}/send", response_model=InvoiceResponse)
async def send_invoice(
    invoice_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_freelancer: Freelancer = Depends(get_current_active_freelancer),
) -> InvoiceResponse:
    invoice = await crud_invoice.get_by_freelancer(db, current_freelancer.id, invoice_id)
    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    if invoice.status not in (InvoiceStatus.DRAFT, InvoiceStatus.SENT):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot send invoice with status {invoice.status}",
        )
    invoice = await crud_invoice.update_status(db, invoice, InvoiceStatus.SENT)
    return InvoiceResponse.model_validate(invoice)


@router.post("/{invoice_id}/mark-paid", response_model=InvoiceResponse)
async def mark_invoice_paid(
    invoice_id: uuid.UUID,
    paid_at: datetime | None = None,
    db: AsyncSession = Depends(get_db),
    current_freelancer: Freelancer = Depends(get_current_active_freelancer),
) -> InvoiceResponse:
    invoice = await crud_invoice.get_by_freelancer(db, current_freelancer.id, invoice_id)
    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    invoice = await crud_invoice.update_status(
        db, invoice, InvoiceStatus.PAID, paid_at=paid_at
    )
    return InvoiceResponse.model_validate(invoice)


@router.post("/{invoice_id}/void", response_model=InvoiceResponse)
async def void_invoice(
    invoice_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_freelancer: Freelancer = Depends(get_current_active_freelancer),
) -> InvoiceResponse:
    invoice = await crud_invoice.get_by_freelancer(db, current_freelancer.id, invoice_id)
    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    if invoice.status == InvoiceStatus.PAID:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot void a paid invoice",
        )
    invoice = await crud_invoice.update_status(db, invoice, InvoiceStatus.VOID)
    return InvoiceResponse.model_validate(invoice)


@router.delete("/{invoice_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_invoice(
    invoice_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_freelancer: Freelancer = Depends(get_current_active_freelancer),
) -> None:
    invoice = await crud_invoice.get_by_freelancer(db, current_freelancer.id, invoice_id)
    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    if invoice.status != InvoiceStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only DRAFT invoices can be deleted",
        )
    await db.delete(invoice)
    await db.commit()

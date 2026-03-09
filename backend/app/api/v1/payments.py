from __future__ import annotations

import sys
import uuid
from datetime import datetime
from pathlib import Path

_PROJECT_ROOT = str(Path(__file__).resolve().parents[4])
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from models import Freelancer  # noqa: E402

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_freelancer
from app.crud.crud_invoice import crud_invoice
from app.crud.crud_payment import crud_payment
from app.db.session import get_db
from app.schemas.payment import PaymentCreate, PaymentResponse

router = APIRouter(prefix="/payments", tags=["payments"])


@router.get("/revenue")
async def get_revenue_summary(
    from_date: datetime = Query(...),
    to_date: datetime = Query(...),
    db: AsyncSession = Depends(get_db),
    current_freelancer: Freelancer = Depends(get_current_active_freelancer),
) -> dict:
    return await crud_payment.get_revenue_summary(
        db, current_freelancer.id, from_date, to_date
    )


@router.get("/", response_model=list[PaymentResponse])
async def list_payments(
    invoice_id: uuid.UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_freelancer: Freelancer = Depends(get_current_active_freelancer),
) -> list[PaymentResponse]:
    payments = await crud_payment.get_multi_by_freelancer(
        db, current_freelancer.id, invoice_id=invoice_id
    )
    return [PaymentResponse.model_validate(p) for p in payments]


@router.post("/", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def create_payment(
    obj_in: PaymentCreate,
    db: AsyncSession = Depends(get_db),
    current_freelancer: Freelancer = Depends(get_current_active_freelancer),
) -> PaymentResponse:
    # Verify invoice belongs to this freelancer
    invoice = await crud_invoice.get_by_freelancer(
        db, current_freelancer.id, obj_in.invoice_id
    )
    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")

    payment = await crud_payment.create_for_freelancer(
        db, current_freelancer.id, obj_in
    )
    return PaymentResponse.model_validate(payment)

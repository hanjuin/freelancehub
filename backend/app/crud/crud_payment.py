from __future__ import annotations

import sys
import uuid
from datetime import datetime
from pathlib import Path

_PROJECT_ROOT = str(Path(__file__).resolve().parents[4])
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from models import Payment, PaymentMethod, PaymentStatus  # noqa: E402

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.schemas.payment import PaymentCreate


class CRUDPayment(CRUDBase[Payment, PaymentCreate, PaymentCreate]):
    async def get_multi_by_invoice(
        self, db: AsyncSession, invoice_id: uuid.UUID
    ) -> list[Payment]:
        result = await db.execute(
            select(Payment)
            .where(Payment.invoice_id == invoice_id)
            .order_by(Payment.paid_at.desc())
        )
        return list(result.scalars().all())

    async def create_for_freelancer(
        self,
        db: AsyncSession,
        freelancer_id: uuid.UUID,
        obj_in: PaymentCreate,
    ) -> Payment:
        payment = Payment(
            freelancer_id=freelancer_id,
            invoice_id=obj_in.invoice_id,
            amount_cents=obj_in.amount_cents,
            method=obj_in.method,
            status=PaymentStatus.COMPLETED,
            paid_at=obj_in.paid_at,
            reference=obj_in.reference,
            notes=obj_in.notes,
            gateway_payment_id=obj_in.gateway_payment_id,
        )
        db.add(payment)
        await db.commit()
        await db.refresh(payment)
        return payment

    async def get_revenue_summary(
        self,
        db: AsyncSession,
        freelancer_id: uuid.UUID,
        from_date: datetime,
        to_date: datetime,
    ) -> dict:
        stmt = select(Payment).where(
            Payment.freelancer_id == freelancer_id,
            Payment.status == PaymentStatus.COMPLETED,
            Payment.paid_at >= from_date,
            Payment.paid_at <= to_date,
        )
        result = await db.execute(stmt)
        payments = list(result.scalars().all())

        total_cents = sum(p.amount_cents for p in payments)
        count = len(payments)

        by_method: dict[str, int] = {}
        for p in payments:
            method_key = p.method.value if hasattr(p.method, "value") else str(p.method)
            by_method[method_key] = by_method.get(method_key, 0) + p.amount_cents

        return {
            "total_cents": total_cents,
            "count": count,
            "by_method": by_method,
        }

    async def get_multi_by_freelancer(
        self,
        db: AsyncSession,
        freelancer_id: uuid.UUID,
        invoice_id: uuid.UUID | None = None,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Payment]:
        stmt = select(Payment).where(Payment.freelancer_id == freelancer_id)
        if invoice_id is not None:
            stmt = stmt.where(Payment.invoice_id == invoice_id)
        stmt = stmt.order_by(Payment.paid_at.desc()).offset(skip).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())


crud_payment = CRUDPayment(Payment)

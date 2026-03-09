from __future__ import annotations

import sys
import uuid
from datetime import date, datetime
from pathlib import Path

_PROJECT_ROOT = str(Path(__file__).resolve().parents[4])
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from models import FreelancerSettings, Invoice, InvoiceLineItem, InvoiceStatus  # noqa: E402

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.crud.base import CRUDBase
from app.schemas.invoice import InvoiceCreate, InvoiceLineItemCreate, InvoiceUpdate


class CRUDInvoice(CRUDBase[Invoice, InvoiceCreate, InvoiceUpdate]):
    async def get_multi_by_freelancer(
        self,
        db: AsyncSession,
        freelancer_id: uuid.UUID,
        *,
        skip: int = 0,
        limit: int = 100,
        status: InvoiceStatus | None = None,
    ) -> tuple[list[Invoice], int]:
        stmt = (
            select(Invoice)
            .where(Invoice.freelancer_id == freelancer_id)
            .options(selectinload(Invoice.line_items))
        )
        if status is not None:
            stmt = stmt.where(Invoice.status == status)

        count_stmt = select(func.count()).select_from(
            select(Invoice).where(Invoice.freelancer_id == freelancer_id).subquery()
        )
        if status is not None:
            count_stmt = select(func.count()).select_from(
                select(Invoice)
                .where(Invoice.freelancer_id == freelancer_id, Invoice.status == status)
                .subquery()
            )
        count_result = await db.execute(count_stmt)
        total = count_result.scalar_one()

        stmt = stmt.order_by(Invoice.issue_date.desc()).offset(skip).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all()), total

    async def get_by_freelancer(
        self, db: AsyncSession, freelancer_id: uuid.UUID, id: uuid.UUID
    ) -> Invoice | None:
        result = await db.execute(
            select(Invoice)
            .where(Invoice.freelancer_id == freelancer_id, Invoice.id == id)
            .options(selectinload(Invoice.line_items))
        )
        return result.scalar_one_or_none()

    async def get_next_invoice_number(
        self, db: AsyncSession, freelancer_id: uuid.UUID
    ) -> str:
        # Atomically increment the sequence
        result = await db.execute(
            select(FreelancerSettings).where(
                FreelancerSettings.freelancer_id == freelancer_id
            )
        )
        settings_obj = result.scalar_one_or_none()
        if not settings_obj:
            # fallback
            prefix = "INV"
            seq = 1
        else:
            await db.execute(
                update(FreelancerSettings)
                .where(FreelancerSettings.freelancer_id == freelancer_id)
                .values(invoice_sequence=FreelancerSettings.invoice_sequence + 1)
            )
            await db.commit()
            # Re-fetch to get updated value
            result2 = await db.execute(
                select(FreelancerSettings).where(
                    FreelancerSettings.freelancer_id == freelancer_id
                )
            )
            settings_obj = result2.scalar_one()
            prefix = settings_obj.invoice_prefix or "INV"
            seq = settings_obj.invoice_sequence

        year = datetime.now().year
        return f"{prefix}-{year}-{seq:04d}"

    async def create_for_freelancer(
        self,
        db: AsyncSession,
        freelancer_id: uuid.UUID,
        obj_in: InvoiceCreate,
        tax_rate_bps: int = 0,
    ) -> Invoice:
        invoice_number = await self.get_next_invoice_number(db, freelancer_id)

        # Compute totals from line items
        subtotal_cents = 0
        line_item_objects: list[InvoiceLineItem] = []
        for li in obj_in.line_items:
            line_total = int(li.unit_price_cents * li.quantity * (1 - li.discount_percent / 100))
            subtotal_cents += line_total
            line_item_objects.append(
                InvoiceLineItem(
                    description=li.description,
                    quantity=li.quantity,
                    unit_price_cents=li.unit_price_cents,
                    discount_percent=li.discount_percent,
                    line_total_cents=line_total,
                    sort_order=li.sort_order,
                )
            )

        tax_cents = int(subtotal_cents * tax_rate_bps / 10000)
        total_cents = subtotal_cents + tax_cents

        invoice = Invoice(
            freelancer_id=freelancer_id,
            customer_id=obj_in.customer_id,
            booking_id=obj_in.booking_id,
            invoice_number=invoice_number,
            issue_date=obj_in.issue_date,
            due_date=obj_in.due_date,
            notes=obj_in.notes,
            payment_terms=obj_in.payment_terms,
            status=InvoiceStatus.DRAFT,
            subtotal_cents=subtotal_cents,
            discount_cents=0,
            tax_rate_bps=tax_rate_bps,
            tax_cents=tax_cents,
            total_cents=total_cents,
        )
        db.add(invoice)
        await db.flush()

        for li_obj in line_item_objects:
            li_obj.invoice_id = invoice.id
            db.add(li_obj)

        await db.commit()
        await db.refresh(invoice)
        # Reload with line items
        result = await db.execute(
            select(Invoice)
            .where(Invoice.id == invoice.id)
            .options(selectinload(Invoice.line_items))
        )
        return result.scalar_one()

    async def update_status(
        self,
        db: AsyncSession,
        invoice: Invoice,
        status: InvoiceStatus,
        paid_at: datetime | None = None,
    ) -> Invoice:
        invoice.status = status
        if status == InvoiceStatus.SENT:
            invoice.sent_at = datetime.utcnow()
        if status == InvoiceStatus.PAID and paid_at:
            invoice.paid_at = paid_at
        elif status == InvoiceStatus.PAID:
            invoice.paid_at = datetime.utcnow()
        db.add(invoice)
        await db.commit()
        await db.refresh(invoice)
        return invoice

    async def add_line_item(
        self,
        db: AsyncSession,
        invoice_id: uuid.UUID,
        obj_in: InvoiceLineItemCreate,
    ) -> InvoiceLineItem:
        line_total = int(
            obj_in.unit_price_cents * obj_in.quantity * (1 - obj_in.discount_percent / 100)
        )
        li = InvoiceLineItem(
            invoice_id=invoice_id,
            description=obj_in.description,
            quantity=obj_in.quantity,
            unit_price_cents=obj_in.unit_price_cents,
            discount_percent=obj_in.discount_percent,
            line_total_cents=line_total,
            sort_order=obj_in.sort_order,
        )
        db.add(li)
        await db.commit()
        await db.refresh(li)
        return li

    async def get_overdue_invoices(
        self, db: AsyncSession, freelancer_id: uuid.UUID
    ) -> list[Invoice]:
        today = date.today()
        result = await db.execute(
            select(Invoice)
            .where(
                Invoice.freelancer_id == freelancer_id,
                Invoice.status == InvoiceStatus.SENT,
                Invoice.due_date < today,
            )
            .options(selectinload(Invoice.line_items))
        )
        return list(result.scalars().all())


crud_invoice = CRUDInvoice(Invoice)

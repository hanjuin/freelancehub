from __future__ import annotations

import sys
import uuid
from pathlib import Path

_PROJECT_ROOT = str(Path(__file__).resolve().parents[4])
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from models import Customer, CustomerTag, CustomerTagAssignment  # noqa: E402

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.schemas.customer import (
    CustomerCreate,
    CustomerTagCreate,
    CustomerTagUpdate,
    CustomerUpdate,
)


class CRUDCustomer(CRUDBase[Customer, CustomerCreate, CustomerUpdate]):
    async def get_multi_by_freelancer(
        self,
        db: AsyncSession,
        freelancer_id: uuid.UUID,
        *,
        skip: int = 0,
        limit: int = 100,
        search: str | None = None,
        active_only: bool = False,
    ) -> tuple[list[Customer], int]:
        stmt = select(Customer).where(Customer.freelancer_id == freelancer_id)
        if active_only:
            stmt = stmt.where(Customer.is_active.is_(True))
        if search:
            pattern = f"%{search}%"
            stmt = stmt.where(
                Customer.first_name.ilike(pattern)
                | Customer.last_name.ilike(pattern)
                | Customer.email.ilike(pattern)
                | Customer.phone.ilike(pattern)
            )

        count_stmt = select(func.count()).select_from(stmt.subquery())
        count_result = await db.execute(count_stmt)
        total = count_result.scalar_one()

        stmt = stmt.order_by(Customer.first_name).offset(skip).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all()), total

    async def get_by_freelancer(
        self, db: AsyncSession, freelancer_id: uuid.UUID, id: uuid.UUID
    ) -> Customer | None:
        result = await db.execute(
            select(Customer).where(
                Customer.freelancer_id == freelancer_id,
                Customer.id == id,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_email(
        self, db: AsyncSession, freelancer_id: uuid.UUID, email: str
    ) -> Customer | None:
        result = await db.execute(
            select(Customer).where(
                Customer.freelancer_id == freelancer_id,
                Customer.email == email.lower(),
            )
        )
        return result.scalar_one_or_none()

    async def create_for_freelancer(
        self,
        db: AsyncSession,
        freelancer_id: uuid.UUID,
        obj_in: CustomerCreate,
    ) -> Customer:
        data = obj_in.model_dump()
        if data.get("email"):
            data["email"] = data["email"].lower()
        customer = Customer(freelancer_id=freelancer_id, **data)
        db.add(customer)
        await db.commit()
        await db.refresh(customer)
        return customer

    async def update_for_freelancer(
        self,
        db: AsyncSession,
        freelancer_id: uuid.UUID,
        id: uuid.UUID,
        obj_in: CustomerUpdate,
    ) -> Customer | None:
        customer = await self.get_by_freelancer(db, freelancer_id, id)
        if not customer:
            return None
        return await self.update(db, db_obj=customer, obj_in=obj_in)

    async def delete_for_freelancer(
        self,
        db: AsyncSession,
        freelancer_id: uuid.UUID,
        id: uuid.UUID,
    ) -> Customer | None:
        customer = await self.get_by_freelancer(db, freelancer_id, id)
        if not customer:
            return None
        await db.delete(customer)
        await db.commit()
        return customer

    async def add_tag(
        self, db: AsyncSession, customer_id: uuid.UUID, tag_id: uuid.UUID
    ) -> None:
        # Check if already assigned
        result = await db.execute(
            select(CustomerTagAssignment).where(
                CustomerTagAssignment.customer_id == customer_id,
                CustomerTagAssignment.tag_id == tag_id,
            )
        )
        if result.scalar_one_or_none() is None:
            assignment = CustomerTagAssignment(
                customer_id=customer_id, tag_id=tag_id
            )
            db.add(assignment)
            await db.commit()

    async def remove_tag(
        self, db: AsyncSession, customer_id: uuid.UUID, tag_id: uuid.UUID
    ) -> None:
        await db.execute(
            delete(CustomerTagAssignment).where(
                CustomerTagAssignment.customer_id == customer_id,
                CustomerTagAssignment.tag_id == tag_id,
            )
        )
        await db.commit()

    async def get_tags(
        self, db: AsyncSession, customer_id: uuid.UUID
    ) -> list[CustomerTag]:
        result = await db.execute(
            select(CustomerTag)
            .join(
                CustomerTagAssignment,
                CustomerTagAssignment.tag_id == CustomerTag.id,
            )
            .where(CustomerTagAssignment.customer_id == customer_id)
        )
        return list(result.scalars().all())


class CRUDCustomerTag(CRUDBase[CustomerTag, CustomerTagCreate, CustomerTagUpdate]):
    async def get_multi_by_freelancer(
        self,
        db: AsyncSession,
        freelancer_id: uuid.UUID,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[CustomerTag]:
        result = await db.execute(
            select(CustomerTag)
            .where(CustomerTag.freelancer_id == freelancer_id)
            .order_by(CustomerTag.name)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_freelancer(
        self, db: AsyncSession, freelancer_id: uuid.UUID, id: uuid.UUID
    ) -> CustomerTag | None:
        result = await db.execute(
            select(CustomerTag).where(
                CustomerTag.freelancer_id == freelancer_id,
                CustomerTag.id == id,
            )
        )
        return result.scalar_one_or_none()

    async def create_for_freelancer(
        self,
        db: AsyncSession,
        freelancer_id: uuid.UUID,
        obj_in: CustomerTagCreate,
    ) -> CustomerTag:
        tag = CustomerTag(freelancer_id=freelancer_id, **obj_in.model_dump())
        db.add(tag)
        await db.commit()
        await db.refresh(tag)
        return tag

    async def update_for_freelancer(
        self,
        db: AsyncSession,
        freelancer_id: uuid.UUID,
        id: uuid.UUID,
        obj_in: CustomerTagUpdate,
    ) -> CustomerTag | None:
        tag = await self.get_by_freelancer(db, freelancer_id, id)
        if not tag:
            return None
        return await self.update(db, db_obj=tag, obj_in=obj_in)

    async def delete_for_freelancer(
        self,
        db: AsyncSession,
        freelancer_id: uuid.UUID,
        id: uuid.UUID,
    ) -> CustomerTag | None:
        tag = await self.get_by_freelancer(db, freelancer_id, id)
        if not tag:
            return None
        await db.delete(tag)
        await db.commit()
        return tag


crud_customer = CRUDCustomer(Customer)
crud_customer_tag = CRUDCustomerTag(CustomerTag)

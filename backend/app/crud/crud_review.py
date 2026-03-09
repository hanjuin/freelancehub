from __future__ import annotations

import sys
import uuid
from datetime import datetime
from pathlib import Path

_PROJECT_ROOT = str(Path(__file__).resolve().parents[4])
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from models import Review  # noqa: E402

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase


class CRUDReview(CRUDBase[Review, Review, Review]):
    async def get_multi_by_freelancer(
        self,
        db: AsyncSession,
        freelancer_id: uuid.UUID,
        *,
        skip: int = 0,
        limit: int = 100,
        published_only: bool = True,
    ) -> list[Review]:
        stmt = select(Review).where(Review.freelancer_id == freelancer_id)
        if published_only:
            stmt = stmt.where(Review.is_published.is_(True))
        stmt = stmt.order_by(Review.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_booking(
        self, db: AsyncSession, booking_id: uuid.UUID
    ) -> Review | None:
        result = await db.execute(
            select(Review).where(Review.booking_id == booking_id)
        )
        return result.scalar_one_or_none()

    async def get_by_token(
        self, db: AsyncSession, token: str
    ) -> Review | None:
        result = await db.execute(
            select(Review).where(Review.review_token == token)
        )
        return result.scalar_one_or_none()

    async def create_from_token(
        self,
        db: AsyncSession,
        review: Review,
        rating: int,
        comment: str | None,
    ) -> Review:
        from datetime import timezone

        review.rating = rating
        review.comment = comment
        review.is_published = True
        review.review_token = None  # consume the token
        review.review_token_expires_at = None
        db.add(review)
        await db.commit()
        await db.refresh(review)
        return review

    async def add_reply(
        self, db: AsyncSession, review: Review, reply: str
    ) -> Review:
        from datetime import timezone

        review.reply = reply
        review.replied_at = datetime.now(timezone.utc)
        db.add(review)
        await db.commit()
        await db.refresh(review)
        return review

    async def get_average_rating(
        self, db: AsyncSession, freelancer_id: uuid.UUID
    ) -> float | None:
        result = await db.execute(
            select(func.avg(Review.rating)).where(
                Review.freelancer_id == freelancer_id,
                Review.is_published.is_(True),
            )
        )
        avg = result.scalar_one_or_none()
        return float(avg) if avg is not None else None

    async def toggle_published(
        self, db: AsyncSession, review: Review
    ) -> Review:
        review.is_published = not review.is_published
        db.add(review)
        await db.commit()
        await db.refresh(review)
        return review

    async def get_by_freelancer_and_id(
        self, db: AsyncSession, freelancer_id: uuid.UUID, id: uuid.UUID
    ) -> Review | None:
        result = await db.execute(
            select(Review).where(
                Review.freelancer_id == freelancer_id,
                Review.id == id,
            )
        )
        return result.scalar_one_or_none()


crud_review = CRUDReview(Review)

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
from app.crud.crud_review import crud_review
from app.db.session import get_db
from app.schemas.common import PaginatedResponse
from app.schemas.review import ReviewReply, ReviewResponse

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.get("/", response_model=PaginatedResponse[ReviewResponse])
async def list_reviews(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    published_only: bool = Query(default=True),
    db: AsyncSession = Depends(get_db),
    current_freelancer: Freelancer = Depends(get_current_active_freelancer),
) -> PaginatedResponse[ReviewResponse]:
    skip = (page - 1) * page_size
    reviews = await crud_review.get_multi_by_freelancer(
        db,
        current_freelancer.id,
        skip=skip,
        limit=page_size,
        published_only=published_only,
    )
    # Simple count
    all_reviews = await crud_review.get_multi_by_freelancer(
        db, current_freelancer.id, skip=0, limit=100000, published_only=published_only
    )
    total = len(all_reviews)
    pages = max(1, (total + page_size - 1) // page_size)
    return PaginatedResponse(
        items=[ReviewResponse.model_validate(r) for r in reviews],
        total=total,
        page=page,
        pages=pages,
    )


@router.get("/{review_id}", response_model=ReviewResponse)
async def get_review(
    review_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_freelancer: Freelancer = Depends(get_current_active_freelancer),
) -> ReviewResponse:
    review = await crud_review.get_by_freelancer_and_id(
        db, current_freelancer.id, review_id
    )
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")
    return ReviewResponse.model_validate(review)


@router.post("/{review_id}/reply", response_model=ReviewResponse)
async def reply_to_review(
    review_id: uuid.UUID,
    body: ReviewReply,
    db: AsyncSession = Depends(get_db),
    current_freelancer: Freelancer = Depends(get_current_active_freelancer),
) -> ReviewResponse:
    review = await crud_review.get_by_freelancer_and_id(
        db, current_freelancer.id, review_id
    )
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")
    review = await crud_review.add_reply(db, review, body.reply)
    return ReviewResponse.model_validate(review)


@router.patch("/{review_id}/publish", response_model=ReviewResponse)
async def toggle_review_published(
    review_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_freelancer: Freelancer = Depends(get_current_active_freelancer),
) -> ReviewResponse:
    review = await crud_review.get_by_freelancer_and_id(
        db, current_freelancer.id, review_id
    )
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")
    review = await crud_review.toggle_published(db, review)
    return ReviewResponse.model_validate(review)

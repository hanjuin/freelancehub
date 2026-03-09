from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ReviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    freelancer_id: uuid.UUID
    booking_id: uuid.UUID
    customer_id: uuid.UUID
    rating: int
    comment: str | None
    is_published: bool
    reply: str | None
    replied_at: datetime | None
    created_at: datetime
    updated_at: datetime


class ReviewReply(BaseModel):
    reply: str


class PublicReviewCreate(BaseModel):
    token: str
    rating: int = Field(ge=1, le=5)
    comment: str | None = None

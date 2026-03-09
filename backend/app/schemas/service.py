from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ServiceCategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str
    icon: str | None
    is_system: bool


class ServiceBase(BaseModel):
    name: str = Field(max_length=200)
    description: str | None = None
    duration_minutes: int = Field(gt=0)
    buffer_minutes: int = Field(default=0, ge=0)
    price_cents: int = Field(ge=0)
    is_active: bool = True
    is_bookable_online: bool = True
    sort_order: int = 0
    color: str | None = Field(default=None, max_length=7)


class ServiceCreate(ServiceBase):
    pass


class ServiceUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=200)
    description: str | None = None
    duration_minutes: int | None = Field(default=None, gt=0)
    buffer_minutes: int | None = Field(default=None, ge=0)
    price_cents: int | None = Field(default=None, ge=0)
    is_active: bool | None = None
    is_bookable_online: bool | None = None
    sort_order: int | None = None
    color: str | None = Field(default=None, max_length=7)


class ServiceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    freelancer_id: uuid.UUID
    name: str
    description: str | None
    duration_minutes: int
    buffer_minutes: int
    price_cents: int
    is_active: bool
    is_bookable_online: bool
    sort_order: int
    color: str | None
    created_at: datetime
    updated_at: datetime

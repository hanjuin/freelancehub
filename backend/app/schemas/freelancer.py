from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class FreelancerBase(BaseModel):
    first_name: str = Field(max_length=100)
    last_name: str = Field(max_length=100)
    phone: str | None = Field(default=None, max_length=30)
    business_name: str | None = Field(default=None, max_length=200)
    bio: str | None = None
    address_line1: str | None = Field(default=None, max_length=255)
    address_line2: str | None = Field(default=None, max_length=255)
    city: str | None = Field(default=None, max_length=100)
    state: str | None = Field(default=None, max_length=100)
    postcode: str | None = Field(default=None, max_length=20)
    country: str = Field(default="AU", max_length=2)
    timezone: str = Field(default="UTC", max_length=50)
    currency: str = Field(default="AUD", max_length=3)


class FreelancerCreate(FreelancerBase):
    email: EmailStr
    password: str = Field(min_length=8)
    username: str = Field(min_length=3, max_length=50)


class FreelancerUpdate(BaseModel):
    first_name: str | None = Field(default=None, max_length=100)
    last_name: str | None = Field(default=None, max_length=100)
    phone: str | None = Field(default=None, max_length=30)
    business_name: str | None = Field(default=None, max_length=200)
    bio: str | None = None
    address_line1: str | None = Field(default=None, max_length=255)
    address_line2: str | None = Field(default=None, max_length=255)
    city: str | None = Field(default=None, max_length=100)
    state: str | None = Field(default=None, max_length=100)
    postcode: str | None = Field(default=None, max_length=20)
    country: str | None = Field(default=None, max_length=2)
    timezone: str | None = Field(default=None, max_length=50)
    currency: str | None = Field(default=None, max_length=3)
    avatar_url: str | None = Field(default=None, max_length=500)
    service_category_id: uuid.UUID | None = None


class FreelancerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    username: str
    first_name: str
    last_name: str
    phone: str | None
    business_name: str | None
    bio: str | None
    address_line1: str | None
    address_line2: str | None
    city: str | None
    state: str | None
    postcode: str | None
    country: str
    timezone: str
    currency: str
    avatar_url: str | None
    service_category_id: uuid.UUID | None
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime

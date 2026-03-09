from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class StaffMemberBase(BaseModel):
    first_name: str = Field(max_length=100)
    last_name: str = Field(max_length=100)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=30)
    avatar_url: str | None = Field(default=None, max_length=500)
    is_active: bool = True
    color: str | None = Field(default=None, max_length=7)


class StaffMemberCreate(StaffMemberBase):
    pass


class StaffMemberUpdate(BaseModel):
    first_name: str | None = Field(default=None, max_length=100)
    last_name: str | None = Field(default=None, max_length=100)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=30)
    avatar_url: str | None = Field(default=None, max_length=500)
    is_active: bool | None = None
    color: str | None = Field(default=None, max_length=7)


class StaffMemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    freelancer_id: uuid.UUID
    first_name: str
    last_name: str
    email: str | None
    phone: str | None
    avatar_url: str | None
    is_active: bool
    color: str | None
    created_at: datetime
    updated_at: datetime

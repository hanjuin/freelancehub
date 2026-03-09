from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class CustomerBase(BaseModel):
    first_name: str = Field(max_length=100)
    last_name: str | None = Field(default=None, max_length=100)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=30)
    address_line1: str | None = Field(default=None, max_length=255)
    address_line2: str | None = Field(default=None, max_length=255)
    city: str | None = Field(default=None, max_length=100)
    state: str | None = Field(default=None, max_length=100)
    postcode: str | None = Field(default=None, max_length=20)
    country: str | None = Field(default=None, max_length=2)
    notes: str | None = None
    date_of_birth: date | None = None
    is_active: bool = True


class CustomerCreate(CustomerBase):
    pass


class CustomerUpdate(BaseModel):
    first_name: str | None = Field(default=None, max_length=100)
    last_name: str | None = Field(default=None, max_length=100)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=30)
    address_line1: str | None = Field(default=None, max_length=255)
    address_line2: str | None = Field(default=None, max_length=255)
    city: str | None = Field(default=None, max_length=100)
    state: str | None = Field(default=None, max_length=100)
    postcode: str | None = Field(default=None, max_length=20)
    country: str | None = Field(default=None, max_length=2)
    notes: str | None = None
    date_of_birth: date | None = None
    is_active: bool | None = None


class CustomerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    freelancer_id: uuid.UUID
    first_name: str
    last_name: str | None
    email: str | None
    phone: str | None
    address_line1: str | None
    address_line2: str | None
    city: str | None
    state: str | None
    postcode: str | None
    country: str | None
    notes: str | None
    date_of_birth: date | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class CustomerTagBase(BaseModel):
    name: str = Field(max_length=50)
    color: str | None = Field(default=None, max_length=7)


class CustomerTagCreate(CustomerTagBase):
    pass


class CustomerTagUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=50)
    color: str | None = Field(default=None, max_length=7)


class CustomerTagResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    freelancer_id: uuid.UUID
    name: str
    color: str | None
    created_at: datetime
    updated_at: datetime

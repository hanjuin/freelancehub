from __future__ import annotations

import sys
from datetime import date, datetime, time
from pathlib import Path
import uuid

# Ensure project root is on path for enum imports
_PROJECT_ROOT = str(Path(__file__).resolve().parents[4])
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from models import DayOfWeek  # noqa: E402

from pydantic import BaseModel, ConfigDict


class WorkingHoursBase(BaseModel):
    day_of_week: DayOfWeek
    is_open: bool = True
    open_time: time | None = None
    close_time: time | None = None
    break_start: time | None = None
    break_end: time | None = None


class WorkingHoursCreate(WorkingHoursBase):
    staff_member_id: uuid.UUID | None = None


class WorkingHoursUpdate(BaseModel):
    day_of_week: DayOfWeek | None = None
    is_open: bool | None = None
    open_time: time | None = None
    close_time: time | None = None
    break_start: time | None = None
    break_end: time | None = None


class WorkingHoursResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    freelancer_id: uuid.UUID
    staff_member_id: uuid.UUID | None
    day_of_week: DayOfWeek
    is_open: bool
    open_time: time | None
    close_time: time | None
    break_start: time | None
    break_end: time | None


class BlockedDateBase(BaseModel):
    start_date: date
    end_date: date
    reason: str | None = None
    all_day: bool = True
    block_start_time: time | None = None
    block_end_time: time | None = None


class BlockedDateCreate(BlockedDateBase):
    pass


class BlockedDateUpdate(BaseModel):
    start_date: date | None = None
    end_date: date | None = None
    reason: str | None = None
    all_day: bool | None = None
    block_start_time: time | None = None
    block_end_time: time | None = None


class BlockedDateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    freelancer_id: uuid.UUID
    staff_member_id: uuid.UUID | None
    start_date: date
    end_date: date
    reason: str | None
    all_day: bool
    block_start_time: time | None
    block_end_time: time | None
    created_at: datetime
    updated_at: datetime


class AvailableSlot(BaseModel):
    start_time: datetime
    end_time: datetime

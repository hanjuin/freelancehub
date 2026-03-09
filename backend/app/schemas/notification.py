from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
import uuid

_PROJECT_ROOT = str(Path(__file__).resolve().parents[4])
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from models import NotificationType  # noqa: E402

from pydantic import BaseModel, ConfigDict


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    type: NotificationType
    title: str
    body: str | None
    is_read: bool
    read_at: datetime | None
    entity_type: str | None
    entity_id: uuid.UUID | None
    created_at: datetime


class MarkReadRequest(BaseModel):
    notification_ids: list[uuid.UUID]

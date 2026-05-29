from __future__ import annotations
import uuid
from datetime import datetime
from pydantic import BaseModel
from app.models.audit import AuditStatus


class AuditCreate(BaseModel):
    title: str
    objective: str | None = None
    status: AuditStatus = AuditStatus.DRAFT


class AuditRead(BaseModel):
    id: uuid.UUID
    program_id: uuid.UUID
    title: str
    objective: str | None
    status: AuditStatus
    started_at: datetime | None
    ended_at: datetime | None
    created_at: datetime
    model_config = {"from_attributes": True}


class AuditUpdate(BaseModel):
    title: str | None = None
    objective: str | None = None
    status: AuditStatus | None = None
    started_at: datetime | None = None
    ended_at: datetime | None = None

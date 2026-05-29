from __future__ import annotations
import uuid
from datetime import datetime
from pydantic import BaseModel
from app.models.program import ProgramPlatform, ProgramStatus, ProgramType


class ProgramCreate(BaseModel):
    name: str
    program_type: ProgramType
    platform: ProgramPlatform = ProgramPlatform.OTHER
    program_url: str | None = None
    status: ProgramStatus = ProgramStatus.PLANNING


class ProgramRead(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    name: str
    program_type: ProgramType
    platform: ProgramPlatform
    program_url: str | None
    status: ProgramStatus
    scope_last_reviewed_at: datetime | None
    created_at: datetime
    model_config = {"from_attributes": True}


class ProgramUpdate(BaseModel):
    name: str | None = None
    program_type: ProgramType | None = None
    platform: ProgramPlatform | None = None
    program_url: str | None = None
    status: ProgramStatus | None = None

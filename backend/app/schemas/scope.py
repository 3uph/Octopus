from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel


class ScopeRawUpdate(BaseModel):
    scope_raw: str


class ScopeRawRead(BaseModel):
    program_id: uuid.UUID
    scope_raw: str | None
    scope_last_reviewed_at: datetime | None
    model_config = {"from_attributes": True}


class ScopeChangeLogRead(BaseModel):
    id: uuid.UUID
    program_id: uuid.UUID
    changed_by: uuid.UUID | None
    change_type: str
    before: dict | None
    after: dict | None
    created_at: datetime
    model_config = {"from_attributes": True}

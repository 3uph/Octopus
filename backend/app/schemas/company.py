from __future__ import annotations
import uuid
from datetime import datetime
from pydantic import BaseModel


class CompanyCreate(BaseModel):
    name_legal: str
    name_commercial: str | None = None
    description: str | None = None


class CompanyRead(BaseModel):
    id: uuid.UUID
    name_legal: str
    name_commercial: str | None
    description: str | None
    created_at: datetime
    model_config = {"from_attributes": True}


class CompanyUpdate(BaseModel):
    name_legal: str | None = None
    name_commercial: str | None = None
    description: str | None = None

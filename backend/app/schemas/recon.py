from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.asset import AssetType
from app.models.enums import Confidence, ReviewStatus, ScopeDecision


class ReconRequest(BaseModel):
    targets: list[str]


class AssetRead(BaseModel):
    id: uuid.UUID
    program_id: uuid.UUID
    value: str
    asset_type: AssetType
    discovered_via: str | None
    scope_decision: ScopeDecision
    score: int
    confidence: Confidence
    review_status: ReviewStatus
    first_seen: datetime
    last_seen: datetime
    model_config = {"from_attributes": True}


class ScanJobRead(BaseModel):
    id: uuid.UUID
    program_id: uuid.UUID
    mode: str
    status: str
    dry_run: bool
    targets: dict | None
    summary: dict | None
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime
    model_config = {"from_attributes": True}


class ToolRunRead(BaseModel):
    id: uuid.UUID
    scan_job_id: uuid.UUID
    tool_name: str
    mode: str
    status: str
    items_produced: int
    blocked_by_scope: bool
    started_at: datetime | None
    finished_at: datetime | None
    model_config = {"from_attributes": True}

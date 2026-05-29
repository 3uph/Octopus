from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.enums import Confidence, ReviewStatus, ScopeKind


class ScopeItemRead(BaseModel):
    id: uuid.UUID
    program_id: uuid.UUID
    raw_value: str
    normalized_value: str
    kind: ScopeKind
    is_wildcard: bool
    confidence: Confidence
    review_status: ReviewStatus
    source: str | None
    notes: str | None
    model_config = {"from_attributes": True}


class OutOfScopeItemRead(BaseModel):
    id: uuid.UUID
    program_id: uuid.UUID
    raw_value: str
    normalized_value: str
    kind: ScopeKind
    is_wildcard: bool
    reason: str | None
    source: str | None
    model_config = {"from_attributes": True}


class ScopeRuleRead(BaseModel):
    id: uuid.UUID
    program_id: uuid.UUID
    rule_type: str
    description_raw: str | None
    parsed_summary: str | None
    severity: str | None
    review_status: ReviewStatus
    model_config = {"from_attributes": True}


class RateLimitRuleRead(BaseModel):
    id: uuid.UUID
    program_id: uuid.UUID
    scope_pattern: str | None
    max_rps: float | None
    max_concurrency: int | None
    window: str | None
    model_config = {"from_attributes": True}


class ReviewItemAction(BaseModel):
    """Confirm or reject a scope item under manual review."""
    item_type: str  # "scope_item" | "out_of_scope_item" | "scope_rule"
    item_id: uuid.UUID
    action: str  # "confirm" | "reject"


class ScopeSummary(BaseModel):
    allowed: list[str]
    forbidden: list[str]
    ambiguous: list[str]
    requires_review: list[str]
    rules: list[str]
    counts: dict[str, int]

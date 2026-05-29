from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, field_validator


class AnalysisCreate(BaseModel):
    company_name: str
    root_domain: str | None = None
    country: str = "ES"
    nif: str | None = None
    aliases: list[str] = []
    depth: str = "standard"
    include_documents: bool = True
    include_github: bool = True
    include_public_records: bool = True
    include_social: bool = True
    include_news: bool = True
    include_leaks: bool = False

    @field_validator("company_name")
    @classmethod
    def name_required(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("company_name is required")
        return v.strip()

    @field_validator("depth")
    @classmethod
    def depth_valid(cls, v: str) -> str:
        if v not in ("light", "standard", "deep"):
            raise ValueError("depth must be light|standard|deep")
        return v

    @field_validator("root_domain")
    @classmethod
    def domain_basic(cls, v: str | None) -> str | None:
        if v is None or not v.strip():
            return None
        v = v.strip().lower()
        if " " in v or "." not in v:
            raise ValueError("invalid domain format")
        return v


class AnalysisRead(BaseModel):
    id: uuid.UUID
    target_company_name: str
    target_root_domain: str | None
    country: str
    nif: str | None
    aliases: list[str] | None
    depth: str
    flags: dict | None
    status: str
    started_at: datetime | None
    finished_at: datetime | None
    duration_seconds: float | None
    summary_json: dict | None
    exposure_score_json: dict | None
    created_at: datetime
    model_config = {"from_attributes": True}


class FindingRead(BaseModel):
    id: uuid.UUID
    type: str
    title: str
    value: str | None
    description: str | None
    source: str | None
    evidence_url: str | None
    confidence: str
    risk_level: str
    tags: list | None
    created_at: datetime
    model_config = {"from_attributes": True}


class EntityRead(BaseModel):
    id: uuid.UUID
    entity_type: str
    value: str
    normalized_value: str
    confidence: str
    source: str | None
    tags: list | None
    model_config = {"from_attributes": True}


class RelationshipRead(BaseModel):
    id: uuid.UUID
    source_value: str | None
    target_value: str | None
    relationship_type: str
    confidence: str
    evidence: str | None
    model_config = {"from_attributes": True}


class RiskRead(BaseModel):
    id: uuid.UUID
    key: str
    title: str
    description: str | None
    risk_level: str
    confidence: str
    evidence_summary: str | None
    why_it_matters: str | None
    recommended_validation: str | None
    recommended_remediation: str | None
    tags: list | None
    model_config = {"from_attributes": True}


class WarningRead(BaseModel):
    id: uuid.UUID
    collector: str | None
    level: str
    message: str
    model_config = {"from_attributes": True}


class CollectorStatusRead(BaseModel):
    id: uuid.UUID
    collector: str
    status: str
    items_produced: int
    duration_seconds: float | None
    message: str | None
    model_config = {"from_attributes": True}

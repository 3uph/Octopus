from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.enums import Confidence, ReviewStatus
from app.models.intelligence import Actionability, ProviderKind


class _ConfReview(BaseModel):
    confidence: Confidence = Confidence.MEDIUM
    review_status: ReviewStatus = ReviewStatus.REQUIRES_REVIEW


class BrandCreate(_ConfReview):
    name: str
    notes: str | None = None


class ProductCreate(_ConfReview):
    name: str
    category: str | None = None
    public_url: str | None = None


class PortalCreate(_ConfReview):
    url: str
    portal_type: str | None = None


class TechSignalCreate(_ConfReview):
    technology: str
    evidence_type: str | None = None


class ProviderCreate(_ConfReview):
    provider_name: str
    kind: ProviderKind = ProviderKind.OTHER
    exposes_surface: bool = False


class FindingCreate(_ConfReview):
    category: str
    title: str
    description: str | None = None
    actionability: Actionability = Actionability.CONTEXTUAL
    source_id: uuid.UUID | None = None


class IntelItemRead(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    created_at: datetime
    model_config = {"from_attributes": True, "extra": "allow"}


class ProfileUpsert(BaseModel):
    summary: str | None = None
    regions: list[str] | None = None
    operating_countries: list[str] | None = None

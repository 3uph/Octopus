"""Corporate intelligence models (OCT-033 base, NO AI).

Separated from technical recon. Every finding carries source + confidence +
review_status. Intelligence NEVER becomes an active target without Scope Gate.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum as PyEnum

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin
from app.models.enums import Confidence, ReviewStatus


class Actionability(str, PyEnum):
    TECHNICAL_ACTIONABLE = "technical_actionable"
    CONTEXTUAL = "contextual"
    LOW_CONFIDENCE = "low_confidence"
    REQUIRES_REVIEW = "requires_review"
    POSSIBLY_OUT_OF_SCOPE = "possibly_out_of_scope"
    SENSITIVE = "sensitive"


class ProviderKind(str, PyEnum):
    CLOUD = "cloud"
    SAAS = "saas"
    IDENTITY = "identity"
    OTHER = "other"


class CompanyIntelligenceProfile(TimestampMixin, Base):
    __tablename__ = "company_intelligence_profiles"
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False, unique=True, index=True,
    )
    summary: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    regions: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    operating_countries: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    last_refreshed_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True), nullable=True)


class _CompanyChild(TimestampMixin):
    """Mixin for company-scoped intelligence entities with confidence + review."""
    confidence: Mapped[Confidence] = mapped_column(
        sa.Enum(Confidence, name="confidence", create_type=False),
        nullable=False, default=Confidence.MEDIUM,
    )
    review_status: Mapped[ReviewStatus] = mapped_column(
        sa.Enum(ReviewStatus, name="review_status", create_type=False),
        nullable=False, default=ReviewStatus.REQUIRES_REVIEW,
    )


class Brand(_CompanyChild, Base):
    __tablename__ = "brands"
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(sa.String(256), nullable=False)
    notes: Mapped[str | None] = mapped_column(sa.Text, nullable=True)


class Product(_CompanyChild, Base):
    __tablename__ = "products"
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(sa.String(256), nullable=False)
    category: Mapped[str | None] = mapped_column(sa.String(128), nullable=True)
    public_url: Mapped[str | None] = mapped_column(sa.String(512), nullable=True)


class PublicPortal(_CompanyChild, Base):
    __tablename__ = "public_portals"
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    url: Mapped[str] = mapped_column(sa.String(512), nullable=False)
    portal_type: Mapped[str | None] = mapped_column(sa.String(64), nullable=True)


class TechnologySignal(_CompanyChild, Base):
    __tablename__ = "technology_signals"
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    technology: Mapped[str] = mapped_column(sa.String(128), nullable=False)
    evidence_type: Mapped[str | None] = mapped_column(sa.String(64), nullable=True)


class ThirdPartyProvider(_CompanyChild, Base):
    """Consolidates SaaS/cloud/identity providers via `kind` (modular, avoids table sprawl)."""
    __tablename__ = "third_party_providers"
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    provider_name: Mapped[str] = mapped_column(sa.String(256), nullable=False)
    kind: Mapped[ProviderKind] = mapped_column(
        sa.Enum(ProviderKind, name="provider_kind"), nullable=False, default=ProviderKind.OTHER)
    exposes_surface: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, default=False)


class IntelligenceSource(TimestampMixin, Base):
    __tablename__ = "intelligence_sources"
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    url: Mapped[str | None] = mapped_column(sa.String(1024), nullable=True)
    source_type: Mapped[str | None] = mapped_column(sa.String(64), nullable=True)
    reliability: Mapped[Confidence] = mapped_column(
        sa.Enum(Confidence, name="confidence", create_type=False),
        nullable=False, default=Confidence.MEDIUM)


class IntelligenceFinding(_CompanyChild, Base):
    __tablename__ = "intelligence_findings"
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    category: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    title: Mapped[str] = mapped_column(sa.String(256), nullable=False)
    description: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    actionability: Mapped[Actionability] = mapped_column(
        sa.Enum(Actionability, name="actionability"),
        nullable=False, default=Actionability.CONTEXTUAL)
    source_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("intelligence_sources.id", ondelete="SET NULL"), nullable=True)


class IntelligenceReviewItem(TimestampMixin, Base):
    __tablename__ = "intelligence_review_items"
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    finding_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("intelligence_findings.id", ondelete="CASCADE"), nullable=True)
    reason: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    status: Mapped[ReviewStatus] = mapped_column(
        sa.Enum(ReviewStatus, name="review_status", create_type=False),
        nullable=False, default=ReviewStatus.REQUIRES_REVIEW)

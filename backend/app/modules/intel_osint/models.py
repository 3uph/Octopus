"""Intel OSINT persistence models.

Enums stored as String (not PG ENUM) to avoid CREATE TYPE collisions with
existing migrations and to keep new value addition migration-free.
Flexible payloads use JSONB.
"""
from __future__ import annotations

import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin


class IntelligenceAnalysis(TimestampMixin, Base):
    __tablename__ = "intel_analyses"

    target_company_name: Mapped[str] = mapped_column(sa.String(512), nullable=False)
    target_root_domain: Mapped[str | None] = mapped_column(sa.String(512), nullable=True)
    country: Mapped[str] = mapped_column(sa.String(8), nullable=False, default="ES")
    nif: Mapped[str | None] = mapped_column(sa.String(32), nullable=True)
    aliases: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    depth: Mapped[str] = mapped_column(sa.String(16), nullable=False, default="standard")
    flags: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    status: Mapped[str] = mapped_column(sa.String(16), nullable=False, default="pending")
    started_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True), nullable=True)
    duration_seconds: Mapped[float | None] = mapped_column(sa.Float, nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    summary_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    exposure_score_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    findings: Mapped[list["IntelFinding"]] = relationship(
        back_populates="analysis", cascade="all, delete-orphan", lazy="select")
    entities: Mapped[list["IntelEntity"]] = relationship(
        back_populates="analysis", cascade="all, delete-orphan", lazy="select")
    relationships: Mapped[list["IntelRelationship"]] = relationship(
        back_populates="analysis", cascade="all, delete-orphan", lazy="select")
    risks: Mapped[list["IntelRiskHypothesis"]] = relationship(
        back_populates="analysis", cascade="all, delete-orphan", lazy="select")
    warnings: Mapped[list["IntelWarning"]] = relationship(
        back_populates="analysis", cascade="all, delete-orphan", lazy="select")
    collector_statuses: Mapped[list["IntelCollectorStatus"]] = relationship(
        back_populates="analysis", cascade="all, delete-orphan", lazy="select")


def _analysis_fk():
    return mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("intel_analyses.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )


class IntelFinding(TimestampMixin, Base):
    __tablename__ = "intel_findings"
    analysis_id: Mapped[uuid.UUID] = _analysis_fk()
    type: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    title: Mapped[str] = mapped_column(sa.String(512), nullable=False)
    value: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    description: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    source: Mapped[str | None] = mapped_column(sa.String(64), nullable=True)
    evidence_url: Mapped[str | None] = mapped_column(sa.String(1024), nullable=True)
    confidence: Mapped[str] = mapped_column(sa.String(16), nullable=False, default="medium")
    risk_level: Mapped[str] = mapped_column(sa.String(16), nullable=False, default="info")
    tags: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    raw_context_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    analysis: Mapped["IntelligenceAnalysis"] = relationship(back_populates="findings")


class IntelEntity(TimestampMixin, Base):
    __tablename__ = "intel_entities"
    analysis_id: Mapped[uuid.UUID] = _analysis_fk()
    entity_type: Mapped[str] = mapped_column(sa.String(32), nullable=False)
    value: Mapped[str] = mapped_column(sa.String(1024), nullable=False)
    normalized_value: Mapped[str] = mapped_column(sa.String(1024), nullable=False)
    confidence: Mapped[str] = mapped_column(sa.String(16), nullable=False, default="medium")
    source: Mapped[str | None] = mapped_column(sa.String(64), nullable=True)
    tags: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    analysis: Mapped["IntelligenceAnalysis"] = relationship(back_populates="entities")


class IntelRelationship(TimestampMixin, Base):
    __tablename__ = "intel_relationships"
    analysis_id: Mapped[uuid.UUID] = _analysis_fk()
    source_entity_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    target_entity_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    source_value: Mapped[str | None] = mapped_column(sa.String(1024), nullable=True)
    target_value: Mapped[str | None] = mapped_column(sa.String(1024), nullable=True)
    relationship_type: Mapped[str] = mapped_column(sa.String(48), nullable=False)
    confidence: Mapped[str] = mapped_column(sa.String(16), nullable=False, default="medium")
    evidence: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    analysis: Mapped["IntelligenceAnalysis"] = relationship(back_populates="relationships")


class IntelRiskHypothesis(TimestampMixin, Base):
    __tablename__ = "intel_risk_hypotheses"
    analysis_id: Mapped[uuid.UUID] = _analysis_fk()
    key: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    title: Mapped[str] = mapped_column(sa.String(512), nullable=False)
    description: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    risk_level: Mapped[str] = mapped_column(sa.String(16), nullable=False, default="info")
    confidence: Mapped[str] = mapped_column(sa.String(16), nullable=False, default="medium")
    evidence_summary: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    why_it_matters: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    recommended_validation: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    recommended_remediation: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    related_findings_json: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    related_entities_json: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    tags: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    analysis: Mapped["IntelligenceAnalysis"] = relationship(back_populates="risks")


class IntelEvidence(TimestampMixin, Base):
    __tablename__ = "intel_evidence"
    analysis_id: Mapped[uuid.UUID] = _analysis_fk()
    finding_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    source: Mapped[str | None] = mapped_column(sa.String(64), nullable=True)
    url: Mapped[str | None] = mapped_column(sa.String(1024), nullable=True)
    content_excerpt: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)


class IntelCollectorStatus(TimestampMixin, Base):
    __tablename__ = "intel_collector_status"
    analysis_id: Mapped[uuid.UUID] = _analysis_fk()
    collector: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    status: Mapped[str] = mapped_column(sa.String(16), nullable=False, default="pending")
    items_produced: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)
    duration_seconds: Mapped[float | None] = mapped_column(sa.Float, nullable=True)
    message: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    analysis: Mapped["IntelligenceAnalysis"] = relationship(back_populates="collector_statuses")


class IntelWarning(TimestampMixin, Base):
    __tablename__ = "intel_warnings"
    analysis_id: Mapped[uuid.UUID] = _analysis_fk()
    collector: Mapped[str | None] = mapped_column(sa.String(64), nullable=True)
    level: Mapped[str] = mapped_column(sa.String(16), nullable=False, default="warning")
    message: Mapped[str] = mapped_column(sa.Text, nullable=False)
    analysis: Mapped["IntelligenceAnalysis"] = relationship(back_populates="warnings")

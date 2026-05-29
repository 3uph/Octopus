"""Scan execution models — ScanProfile, ScanJob, ToolRun (OCT-028)."""
from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum as PyEnum

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin


class ReconMode(str, PyEnum):
    PASSIVE = "passive"
    MEDIUM = "medium"
    ACTIVE = "active"
    DRY_RUN = "dry_run"


class JobStatus(str, PyEnum):
    QUEUED = "queued"
    DRY_RUN = "dry_run"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ScanProfile(TimestampMixin, Base):
    __tablename__ = "scan_profiles"

    name: Mapped[str] = mapped_column(sa.String(128), nullable=False, unique=True)
    mode: Mapped[ReconMode] = mapped_column(
        sa.Enum(ReconMode, name="recon_mode"), nullable=False
    )
    tools_enabled: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    default_args: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    rate_limits: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    is_system: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, default=False)


class ScanJob(TimestampMixin, Base):
    __tablename__ = "scan_jobs"

    program_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("programs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    audit_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("audits.id", ondelete="SET NULL"), nullable=True
    )
    profile_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("scan_profiles.id", ondelete="SET NULL"), nullable=True
    )
    mode: Mapped[ReconMode] = mapped_column(
        sa.Enum(ReconMode, name="recon_mode", create_type=False), nullable=False
    )
    status: Mapped[JobStatus] = mapped_column(
        sa.Enum(JobStatus, name="job_status"), nullable=False, default=JobStatus.QUEUED
    )
    targets: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    requested_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    dry_run: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, default=False)
    started_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True), nullable=True)
    summary: Mapped[dict | None] = mapped_column(JSONB, nullable=True)


class ToolRun(TimestampMixin, Base):
    __tablename__ = "tool_runs"

    scan_job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("scan_jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tool_name: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    tool_version: Mapped[str | None] = mapped_column(sa.String(64), nullable=True)
    args_sanitized: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    target_scope: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    mode: Mapped[ReconMode] = mapped_column(
        sa.Enum(ReconMode, name="recon_mode", create_type=False), nullable=False
    )
    status: Mapped[JobStatus] = mapped_column(
        sa.Enum(JobStatus, name="job_status", create_type=False),
        nullable=False,
        default=JobStatus.QUEUED,
    )
    started_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True), nullable=True)
    exit_code: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)
    raw_output_path: Mapped[str | None] = mapped_column(sa.String(512), nullable=True)
    items_produced: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)
    blocked_by_scope: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, default=False)

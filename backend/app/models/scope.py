"""Scope models — normalized scope entities (OCT-022).

ScopeItem / OutOfScopeItem / ScopeRule / RateLimitRule.
No parsing logic here — that lives in modules/scope_parser.
"""
from __future__ import annotations

import uuid

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin
from app.models.enums import Confidence, ReviewStatus, ScopeKind


class ScopeItem(TimestampMixin, Base):
    __tablename__ = "scope_items"

    program_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("programs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    raw_value: Mapped[str] = mapped_column(sa.String(1024), nullable=False)
    normalized_value: Mapped[str] = mapped_column(sa.String(1024), nullable=False, index=True)
    kind: Mapped[ScopeKind] = mapped_column(
        sa.Enum(ScopeKind, name="scope_kind"), nullable=False, default=ScopeKind.OTHER
    )
    is_wildcard: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, default=False)
    confidence: Mapped[Confidence] = mapped_column(
        sa.Enum(Confidence, name="confidence"), nullable=False, default=Confidence.MEDIUM
    )
    review_status: Mapped[ReviewStatus] = mapped_column(
        sa.Enum(ReviewStatus, name="review_status"),
        nullable=False,
        default=ReviewStatus.AUTO,
    )
    source: Mapped[str | None] = mapped_column(sa.String(128), nullable=True)
    notes: Mapped[str | None] = mapped_column(sa.Text, nullable=True)


class OutOfScopeItem(TimestampMixin, Base):
    __tablename__ = "out_of_scope_items"

    program_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("programs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    raw_value: Mapped[str] = mapped_column(sa.String(1024), nullable=False)
    normalized_value: Mapped[str] = mapped_column(sa.String(1024), nullable=False, index=True)
    kind: Mapped[ScopeKind] = mapped_column(
        sa.Enum(ScopeKind, name="scope_kind", create_type=False),
        nullable=False,
        default=ScopeKind.OTHER,
    )
    is_wildcard: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, default=False)
    reason: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    source: Mapped[str | None] = mapped_column(sa.String(128), nullable=True)


class ScopeRule(TimestampMixin, Base):
    __tablename__ = "scope_rules"

    program_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("programs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    rule_type: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    description_raw: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    parsed_summary: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    severity: Mapped[str | None] = mapped_column(sa.String(32), nullable=True)
    review_status: Mapped[ReviewStatus] = mapped_column(
        sa.Enum(ReviewStatus, name="review_status", create_type=False),
        nullable=False,
        default=ReviewStatus.AUTO,
    )


class RateLimitRule(TimestampMixin, Base):
    __tablename__ = "rate_limit_rules"

    program_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("programs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    scope_pattern: Mapped[str | None] = mapped_column(sa.String(256), nullable=True)
    max_rps: Mapped[float | None] = mapped_column(sa.Float, nullable=True)
    max_concurrency: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)
    window: Mapped[str | None] = mapped_column(sa.String(32), nullable=True)
    notes: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    source: Mapped[str | None] = mapped_column(sa.String(128), nullable=True)

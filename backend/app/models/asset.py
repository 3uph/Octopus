"""Asset model — central surface node (OCT-027)."""
from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum as PyEnum

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin
from app.models.enums import Confidence, ReviewStatus, ScopeDecision


class AssetType(str, PyEnum):
    DOMAIN = "domain"
    SUBDOMAIN = "subdomain"
    IP = "ip"
    URL = "url"
    CLOUD = "cloud"
    MOBILE = "mobile"


class Asset(TimestampMixin, Base):
    __tablename__ = "assets"

    program_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("programs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    value: Mapped[str] = mapped_column(sa.String(1024), nullable=False, index=True)
    asset_type: Mapped[AssetType] = mapped_column(
        sa.Enum(AssetType, name="asset_type"), nullable=False
    )
    parent_asset_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("assets.id", ondelete="SET NULL"), nullable=True
    )
    discovered_via: Mapped[str | None] = mapped_column(sa.String(128), nullable=True)
    first_seen: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
    )
    last_seen: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
    )
    scope_decision: Mapped[ScopeDecision] = mapped_column(
        sa.Enum(ScopeDecision, name="scope_decision"),
        nullable=False,
        default=ScopeDecision.OUT,
    )
    score: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)
    score_breakdown: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    confidence: Mapped[Confidence] = mapped_column(
        sa.Enum(Confidence, name="confidence", create_type=False),
        nullable=False,
        default=Confidence.MEDIUM,
    )
    review_status: Mapped[ReviewStatus] = mapped_column(
        sa.Enum(ReviewStatus, name="review_status", create_type=False),
        nullable=False,
        default=ReviewStatus.AUTO,
    )
    tags: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    __table_args__ = (
        sa.UniqueConstraint("program_id", "value", name="uq_asset_program_value"),
    )

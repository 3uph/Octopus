"""Audit model — a work round/iteration within a Program."""
from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum as PyEnum

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin


class AuditStatus(str, PyEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class Audit(TimestampMixin, Base):
    __tablename__ = "audits"

    program_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("programs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(sa.String(256), nullable=False)
    objective: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    status: Mapped[AuditStatus] = mapped_column(
        sa.Enum(AuditStatus, name="audit_status"),
        nullable=False,
        default=AuditStatus.DRAFT,
    )
    started_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )
    ended_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )

    program: Mapped["Program"] = relationship("Program", back_populates="audits")

    def __repr__(self) -> str:
        return f"<Audit id={self.id} title={self.title!r} status={self.status}>"

"""Program model — bug bounty program or audit engagement."""
from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum as PyEnum

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin


class ProgramType(str, PyEnum):
    EXTERNAL_AUDIT = "external_audit"
    BUG_BOUNTY = "bug_bounty"
    OSINT = "osint"
    SURFACE_REVIEW = "surface_review"
    PRIVATE_PROGRAM = "private_program"
    OTHER = "other"


class ProgramPlatform(str, PyEnum):
    HACKERONE = "hackerone"
    BUGCROWD = "bugcrowd"
    INTIGRITI = "intigriti"
    PRIVATE = "private"
    CLIENT = "client"
    OTHER = "other"


class ProgramStatus(str, PyEnum):
    PLANNING = "planning"
    ACTIVE = "active"
    PAUSED = "paused"
    CLOSED = "closed"


class Program(TimestampMixin, Base):
    __tablename__ = "programs"

    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(sa.String(256), nullable=False)
    program_type: Mapped[ProgramType] = mapped_column(
        sa.Enum(ProgramType, name="program_type"), nullable=False
    )
    platform: Mapped[ProgramPlatform] = mapped_column(
        sa.Enum(ProgramPlatform, name="program_platform"),
        nullable=False,
        default=ProgramPlatform.OTHER,
    )
    program_url: Mapped[str | None] = mapped_column(sa.String(512), nullable=True)
    status: Mapped[ProgramStatus] = mapped_column(
        sa.Enum(ProgramStatus, name="program_status"),
        nullable=False,
        default=ProgramStatus.PLANNING,
    )
    scope_raw: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    scope_last_reviewed_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )

    company: Mapped["Company"] = relationship("Company", back_populates="programs")
    audits: Mapped[list["Audit"]] = relationship(
        "Audit", back_populates="program", cascade="all, delete-orphan", lazy="select"
    )

    def __repr__(self) -> str:
        return f"<Program id={self.id} name={self.name!r} type={self.program_type}>"

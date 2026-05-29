"""ScopeChangeLog model — history of raw scope changes per program.

Stores before/after snapshots. No parsing, no normalization (those come later).
"""
from __future__ import annotations

import uuid

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin


class ScopeChangeLog(TimestampMixin, Base):
    __tablename__ = "scope_change_logs"

    program_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("programs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    changed_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    change_type: Mapped[str] = mapped_column(sa.String(32), nullable=False)
    # Snapshots stored as JSONB: {"scope_raw": "..."}
    before: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    after: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    def __repr__(self) -> str:
        return f"<ScopeChangeLog program={self.program_id} type={self.change_type}>"

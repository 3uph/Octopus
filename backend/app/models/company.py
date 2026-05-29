"""Company model — top-level tenant entity."""
from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin


class Company(TimestampMixin, Base):
    __tablename__ = "companies"

    name_legal: Mapped[str] = mapped_column(sa.String(256), nullable=False)
    name_commercial: Mapped[str | None] = mapped_column(sa.String(256), nullable=True)
    description: Mapped[str | None] = mapped_column(sa.Text, nullable=True)

    # Relationships (lazy loading — avoid N+1 in async context)
    programs: Mapped[list["Program"]] = relationship(
        "Program", back_populates="company", cascade="all, delete-orphan", lazy="select"
    )

    def __repr__(self) -> str:
        return f"<Company id={self.id} name={self.name_legal!r}>"

"""Setting model — hierarchical config with encrypted secrets.

Hierarchy: program > company > global
is_secret=True values are encrypted at rest via Fernet (ENCRYPTION_KEY).
"""
from __future__ import annotations

import uuid
from enum import Enum as PyEnum

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin


class SettingScope(str, PyEnum):
    GLOBAL = "global"
    COMPANY = "company"
    PROGRAM = "program"


class Setting(TimestampMixin, Base):
    __tablename__ = "settings"

    scope: Mapped[SettingScope] = mapped_column(
        sa.Enum(SettingScope, name="setting_scope"), nullable=False
    )
    scope_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )
    key: Mapped[str] = mapped_column(sa.String(128), nullable=False)
    # Stored as JSONB. If is_secret=True, value is an encrypted string.
    value: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    is_secret: Mapped[bool] = mapped_column(
        sa.Boolean, nullable=False, default=False
    )

    __table_args__ = (
        sa.UniqueConstraint("scope", "scope_id", "key", name="uq_setting_scope_key"),
    )

    def get_value(self) -> object:
        """Return decrypted value if is_secret, else raw value."""
        if not self.is_secret or not self.value:
            return self.value
        from app.core.security.encryption import decrypt_value
        encrypted = self.value.get("_enc")
        if not encrypted:
            return self.value
        return decrypt_value(encrypted)

    @staticmethod
    def make_encrypted_value(plaintext: str) -> dict:
        """Return JSONB-compatible dict wrapping the encrypted value."""
        from app.core.security.encryption import encrypt_value
        return {"_enc": encrypt_value(plaintext)}

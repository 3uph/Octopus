"""AuditLog dependency — records mutating actions into audit_logs table."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import CurrentUser, get_current_user
from app.api.dependencies.db import get_db
from app.core.logging.redactor import redact
from app.models.audit_log import AuditLog

_SENSITIVE_KEYS = frozenset({
    "password", "passwd", "secret", "token", "api_key", "apikey",
    "auth", "credential", "private_key", "encryption_key", "access_key",
    "secret_key", "authorization",
})


async def audit_action(
    action: str,
    entity_type: str | None,
    entity_id: str | None,
    details: dict[str, Any] | None,
    db: AsyncSession,
    user: CurrentUser | None = None,
    request: Request | None = None,
    mode: str | None = None,
) -> None:
    """Write one audit log entry. Details are redacted before storage."""
    redacted: dict | None = None
    if details:
        redacted = {
            k: "[REDACTED]" if k.lower() in _SENSITIVE_KEYS else redact(str(v))
            for k, v in details.items()
        }

    ip: str | None = None
    if request:
        ip = request.client.host if request.client else None

    entry = AuditLog(
        id=uuid.uuid4(),
        user_id=user.id if user else None,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        mode=mode,
        details_redacted=redacted,
        ip=ip,
        created_at=datetime.now(timezone.utc),
    )
    db.add(entry)
    # Flush without commit — caller commits with the main transaction
    await db.flush()

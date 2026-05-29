"""FastAPI dependency — extract and validate current user from JWT."""
from __future__ import annotations

import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.logging import get_logger
from app.core.security.tokens import TokenError, decode_access_token
from app.models.user import UserRole

logger = get_logger(__name__)

_bearer = HTTPBearer(auto_error=True)


class CurrentUser:
    """Lightweight user context extracted from JWT (no DB query)."""

    def __init__(self, user_id: uuid.UUID, role: UserRole, username: str) -> None:
        self.id = user_id
        self.role = role
        self.username = username


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> CurrentUser:
    """Validate Bearer token and return current user context."""
    exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(credentials.credentials)
    except TokenError:
        raise exc

    user_id_str = payload.get("sub")
    role_str = payload.get("role", UserRole.VIEWER)
    username = payload.get("username", "")
    if not user_id_str:
        raise exc

    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        raise exc

    return CurrentUser(user_id=user_id, role=UserRole(role_str), username=username)

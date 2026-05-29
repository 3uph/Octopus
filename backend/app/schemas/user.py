"""User schemas — password_hash never exposed in read schemas."""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, field_validator

from app.models.user import UserRole


class UserCreate(BaseModel):
    username: str
    email: str
    password: str  # plain text; hashed in service layer
    role: UserRole = UserRole.VIEWER

    @field_validator("username")
    @classmethod
    def username_valid(cls, v: str) -> str:
        v = v.strip()
        if not v or len(v) < 3 or len(v) > 64:
            raise ValueError("username must be 3–64 chars")
        return v

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("password must be at least 8 chars")
        return v


class UserRead(BaseModel):
    """Read schema — never includes password_hash."""
    id: uuid.UUID
    username: str
    email: str
    role: UserRole
    is_active: bool
    last_login_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    role: UserRole | None = None
    is_active: bool | None = None

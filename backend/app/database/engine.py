"""Async engine factory — lazy initialization (not at import time)."""
from __future__ import annotations

from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from app.core.config import settings


@lru_cache(maxsize=1)
def get_engine() -> AsyncEngine:
    """Return the shared async engine (created once, cached)."""
    return create_async_engine(
        settings.database_url,
        echo=settings.log_level == "DEBUG",
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
    )

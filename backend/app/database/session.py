"""AsyncSession factory — lazy, depends on get_engine()."""
from __future__ import annotations

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from .engine import get_engine


def _make_session_factory() -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        bind=get_engine(),
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield an AsyncSession; for use as FastAPI dependency."""
    factory = _make_session_factory()
    async with factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise

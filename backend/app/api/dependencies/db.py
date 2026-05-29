"""FastAPI dependency for DB session injection."""
from typing import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db_session


async def get_db(
    session: AsyncSession = Depends(get_db_session),
) -> AsyncGenerator[AsyncSession, None]:
    """Dependency alias — inject AsyncSession into route handlers."""
    yield session

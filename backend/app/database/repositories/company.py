"""Company repository — DB access layer."""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import Company
from app.schemas.company import CompanyCreate, CompanyUpdate


class CompanyRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get(self, company_id: uuid.UUID) -> Company | None:
        result = await self._db.execute(select(Company).where(Company.id == company_id))
        return result.scalar_one_or_none()

    async def list(self, offset: int = 0, limit: int = 50) -> list[Company]:
        result = await self._db.execute(
            select(Company).order_by(Company.created_at.desc()).offset(offset).limit(limit)
        )
        return list(result.scalars().all())

    async def create(self, data: CompanyCreate) -> Company:
        company = Company(**data.model_dump())
        self._db.add(company)
        await self._db.flush()
        await self._db.refresh(company)
        return company

    async def update(self, company: Company, data: CompanyUpdate) -> Company:
        for field, value in data.model_dump(exclude_none=True).items():
            setattr(company, field, value)
        await self._db.flush()
        await self._db.refresh(company)
        return company

    async def delete(self, company: Company) -> None:
        await self._db.delete(company)
        await self._db.flush()

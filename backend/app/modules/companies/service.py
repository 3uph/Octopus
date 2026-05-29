"""Company service — business logic layer (thin for now)."""
from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.repositories.company import CompanyRepository
from app.models.company import Company
from app.schemas.company import CompanyCreate, CompanyUpdate


class CompanyService:
    def __init__(self, db: AsyncSession) -> None:
        self._repo = CompanyRepository(db)
        self._db = db

    async def get_or_404(self, company_id: uuid.UUID) -> Company:
        from fastapi import HTTPException
        company = await self._repo.get(company_id)
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        return company

    async def list(self, offset: int = 0, limit: int = 50) -> list[Company]:
        return await self._repo.list(offset=offset, limit=limit)

    async def create(self, data: CompanyCreate) -> Company:
        return await self._repo.create(data)

    async def update(self, company_id: uuid.UUID, data: CompanyUpdate) -> Company:
        company = await self.get_or_404(company_id)
        return await self._repo.update(company, data)

    async def delete(self, company_id: uuid.UUID) -> None:
        company = await self.get_or_404(company_id)
        await self._repo.delete(company)

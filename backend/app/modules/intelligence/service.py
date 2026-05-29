"""Corporate intelligence service (NO AI).

Manual CRUD for intelligence entities. Every finding keeps source/confidence/
review_status. Intelligence is NEVER auto-promoted to an active recon target —
promotion requires explicit Scope Gate + human review (not implemented here).
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.intelligence import (
    Brand, CompanyIntelligenceProfile, IntelligenceFinding, Product,
    PublicPortal, TechnologySignal, ThirdPartyProvider,
)
from app.modules.companies.service import CompanyService

# Map entity keys to model classes for generic listing
ENTITY_MODELS = {
    "brands": Brand,
    "products": Product,
    "portals": PublicPortal,
    "tech_signals": TechnologySignal,
    "providers": ThirdPartyProvider,
    "findings": IntelligenceFinding,
}


class IntelligenceService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._companies = CompanyService(db)

    async def _company_or_404(self, company_id: uuid.UUID):
        return await self._companies.get_or_404(company_id)

    async def add_entity(self, company_id: uuid.UUID, model_cls, data: dict):
        await self._company_or_404(company_id)
        obj = model_cls(company_id=company_id, **data)
        self._db.add(obj)
        await self._db.flush()
        await self._db.refresh(obj)
        return obj

    async def list_entity(self, company_id: uuid.UUID, entity_key: str):
        await self._company_or_404(company_id)
        model_cls = ENTITY_MODELS.get(entity_key)
        if model_cls is None:
            raise HTTPException(status_code=404, detail="Unknown intelligence entity")
        rows = (await self._db.execute(
            select(model_cls).where(model_cls.company_id == company_id)
            .order_by(model_cls.created_at.desc())
        )).scalars().all()
        return list(rows)

    async def upsert_profile(self, company_id: uuid.UUID, data: dict):
        await self._company_or_404(company_id)
        existing = (await self._db.execute(
            select(CompanyIntelligenceProfile).where(
                CompanyIntelligenceProfile.company_id == company_id)
        )).scalar_one_or_none()
        if existing:
            for k, v in data.items():
                if v is not None:
                    setattr(existing, k, v)
            existing.last_refreshed_at = datetime.now(timezone.utc)
            await self._db.flush()
            return existing
        profile = CompanyIntelligenceProfile(
            company_id=company_id, last_refreshed_at=datetime.now(timezone.utc), **data,
        )
        self._db.add(profile)
        await self._db.flush()
        await self._db.refresh(profile)
        return profile

    async def get_profile(self, company_id: uuid.UUID):
        await self._company_or_404(company_id)
        return (await self._db.execute(
            select(CompanyIntelligenceProfile).where(
                CompanyIntelligenceProfile.company_id == company_id)
        )).scalar_one_or_none()

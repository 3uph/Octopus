"""Corporate intelligence routes (manual, NO AI).

CRUD for brands/products/portals/tech-signals/providers/findings + profile.
Intelligence is contextual; it never becomes an active recon target here.
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.audit import audit_action
from app.api.dependencies.auth import CurrentUser, get_current_user
from app.api.dependencies.db import get_db
from app.core.permissions.rbac import require_operator
from app.models.intelligence import (
    Brand, IntelligenceFinding, Product, PublicPortal, TechnologySignal,
    ThirdPartyProvider,
)
from app.modules.intelligence.service import IntelligenceService
from app.schemas.intelligence import (
    BrandCreate, FindingCreate, IntelItemRead, PortalCreate, ProductCreate,
    ProfileUpsert, ProviderCreate, TechSignalCreate,
)

router = APIRouter(prefix="/companies/{company_id}/intelligence", tags=["intelligence"])

_CREATE_MAP = [
    ("brands", Brand, BrandCreate),
    ("products", Product, ProductCreate),
    ("portals", PublicPortal, PortalCreate),
    ("tech_signals", TechnologySignal, TechSignalCreate),
    ("providers", ThirdPartyProvider, ProviderCreate),
    ("findings", IntelligenceFinding, FindingCreate),
]


def _make_create_route(entity_key: str, model_cls, schema_cls):
    async def _create(
        company_id: uuid.UUID,
        data: schema_cls,  # type: ignore[valid-type]
        db: AsyncSession = Depends(get_db),
        user: CurrentUser = Depends(require_operator),
    ) -> dict:
        obj = await IntelligenceService(db).add_entity(company_id, model_cls, data.model_dump())
        await audit_action(
            f"create_intel_{entity_key}", entity_key, str(obj.id),
            {"company_id": str(company_id)}, db, user,
        )
        await db.commit()
        return {"id": str(obj.id), "entity": entity_key}
    return _create


def _make_list_route(entity_key: str):
    async def _list(
        company_id: uuid.UUID,
        db: AsyncSession = Depends(get_db),
        user: CurrentUser = Depends(get_current_user),
    ) -> list[IntelItemRead]:
        return await IntelligenceService(db).list_entity(company_id, entity_key)
    return _list


for _key, _model, _schema in _CREATE_MAP:
    router.add_api_route(f"/{_key}", _make_create_route(_key, _model, _schema),
                         methods=["POST"], name=f"create_{_key}")
    router.add_api_route(f"/{_key}", _make_list_route(_key),
                         methods=["GET"], name=f"list_{_key}",
                         response_model=list[IntelItemRead])


@router.put("/profile")
async def upsert_profile(
    company_id: uuid.UUID,
    data: ProfileUpsert,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_operator),
) -> dict:
    profile = await IntelligenceService(db).upsert_profile(company_id, data.model_dump())
    await audit_action("upsert_intel_profile", "company", str(company_id), {}, db, user)
    await db.commit()
    return {"id": str(profile.id), "company_id": str(company_id)}


@router.get("/profile")
async def get_profile(
    company_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> dict:
    profile = await IntelligenceService(db).get_profile(company_id)
    if not profile:
        return {}
    return {
        "id": str(profile.id),
        "company_id": str(profile.company_id),
        "summary": profile.summary,
        "regions": profile.regions,
        "operating_countries": profile.operating_countries,
    }

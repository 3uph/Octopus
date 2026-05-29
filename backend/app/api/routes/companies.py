"""Company routes — CRUD. Requires operator role for mutations."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import CurrentUser
from app.api.dependencies.audit import audit_action
from app.api.dependencies.db import get_db
from app.core.permissions.rbac import require_operator, get_current_user
from app.modules.companies.service import CompanyService
from app.schemas.company import CompanyCreate, CompanyRead, CompanyUpdate

router = APIRouter(prefix="/companies", tags=["companies"])


@router.get("/", response_model=list[CompanyRead])
async def list_companies(
    offset: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),  # any authenticated user
) -> list[CompanyRead]:
    svc = CompanyService(db)
    return await svc.list(offset=offset, limit=limit)


@router.post("/", response_model=CompanyRead, status_code=status.HTTP_201_CREATED)
async def create_company(
    data: CompanyCreate,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_operator),
) -> CompanyRead:
    svc = CompanyService(db)
    company = await svc.create(data)
    await audit_action("create_company", "company", str(company.id), {"name": data.name_legal}, db, user)
    await db.commit()
    return company


@router.get("/{company_id}", response_model=CompanyRead)
async def get_company(
    company_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> CompanyRead:
    svc = CompanyService(db)
    return await svc.get_or_404(company_id)


@router.patch("/{company_id}", response_model=CompanyRead)
async def update_company(
    company_id: uuid.UUID,
    data: CompanyUpdate,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_operator),
) -> CompanyRead:
    svc = CompanyService(db)
    company = await svc.update(company_id, data)
    await audit_action("update_company", "company", str(company_id), {}, db, user)
    await db.commit()
    return company


@router.delete("/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_company(
    company_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_operator),
) -> None:
    svc = CompanyService(db)
    await svc.delete(company_id)
    await audit_action("delete_company", "company", str(company_id), {}, db, user)
    await db.commit()

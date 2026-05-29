"""Program routes — nested under company for tenant isolation."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.audit import audit_action
from app.api.dependencies.auth import CurrentUser, get_current_user
from app.api.dependencies.db import get_db
from app.core.permissions.rbac import require_operator
from app.modules.companies.service import CompanyService
from app.modules.programs.service import ProgramService
from app.schemas.program import ProgramCreate, ProgramRead, ProgramUpdate

router = APIRouter(prefix="/companies/{company_id}/programs", tags=["programs"])


@router.get("/", response_model=list[ProgramRead])
async def list_programs(
    company_id: uuid.UUID,
    offset: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> list[ProgramRead]:
    await CompanyService(db).get_or_404(company_id)
    return await ProgramService(db).list(company_id, offset=offset, limit=limit)


@router.post("/", response_model=ProgramRead, status_code=status.HTTP_201_CREATED)
async def create_program(
    company_id: uuid.UUID,
    data: ProgramCreate,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_operator),
) -> ProgramRead:
    await CompanyService(db).get_or_404(company_id)
    program = await ProgramService(db).create(company_id, data)
    await audit_action(
        "create_program", "program", str(program.id),
        {"name": data.name, "company_id": str(company_id)}, db, user,
    )
    await db.commit()
    return program


@router.get("/{program_id}", response_model=ProgramRead)
async def get_program(
    company_id: uuid.UUID,
    program_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> ProgramRead:
    return await ProgramService(db).get_in_company_or_404(company_id, program_id)


@router.patch("/{program_id}", response_model=ProgramRead)
async def update_program(
    company_id: uuid.UUID,
    program_id: uuid.UUID,
    data: ProgramUpdate,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_operator),
) -> ProgramRead:
    program = await ProgramService(db).update(company_id, program_id, data)
    await audit_action(
        "update_program", "program", str(program_id),
        {"company_id": str(company_id)}, db, user,
    )
    await db.commit()
    return program


@router.delete("/{program_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_program(
    company_id: uuid.UUID,
    program_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_operator),
) -> None:
    await ProgramService(db).delete(company_id, program_id)
    await audit_action(
        "delete_program", "program", str(program_id),
        {"company_id": str(company_id)}, db, user,
    )
    await db.commit()

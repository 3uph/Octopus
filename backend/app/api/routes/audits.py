"""Audit routes — nested under program for tenant isolation."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.audit import audit_action
from app.api.dependencies.auth import CurrentUser, get_current_user
from app.api.dependencies.db import get_db
from app.core.permissions.rbac import require_operator
from app.modules.programs.service import AuditService
from app.schemas.audit import AuditCreate, AuditRead, AuditUpdate

router = APIRouter(prefix="/programs/{program_id}/audits", tags=["audits"])


@router.get("/", response_model=list[AuditRead])
async def list_audits(
    program_id: uuid.UUID,
    offset: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> list[AuditRead]:
    return await AuditService(db).list(program_id, offset=offset, limit=limit)


@router.post("/", response_model=AuditRead, status_code=status.HTTP_201_CREATED)
async def create_audit(
    program_id: uuid.UUID,
    data: AuditCreate,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_operator),
) -> AuditRead:
    audit = await AuditService(db).create(program_id, data)
    await audit_action(
        "create_audit", "audit", str(audit.id),
        {"title": data.title, "program_id": str(program_id)}, db, user,
    )
    await db.commit()
    return audit


@router.get("/{audit_id}", response_model=AuditRead)
async def get_audit(
    program_id: uuid.UUID,
    audit_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> AuditRead:
    return await AuditService(db).get_in_program_or_404(program_id, audit_id)


@router.patch("/{audit_id}", response_model=AuditRead)
async def update_audit(
    program_id: uuid.UUID,
    audit_id: uuid.UUID,
    data: AuditUpdate,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_operator),
) -> AuditRead:
    audit = await AuditService(db).update(program_id, audit_id, data)
    await audit_action(
        "update_audit", "audit", str(audit_id),
        {"program_id": str(program_id)}, db, user,
    )
    await db.commit()
    return audit


@router.delete("/{audit_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_audit(
    program_id: uuid.UUID,
    audit_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_operator),
) -> None:
    await AuditService(db).delete(program_id, audit_id)
    await audit_action(
        "delete_audit", "audit", str(audit_id),
        {"program_id": str(program_id)}, db, user,
    )
    await db.commit()

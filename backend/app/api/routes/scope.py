"""Scope raw routes — persist raw scope text + view change history.

NO parsing, NO Scope Gate. Raw persistence only (OCT-018).
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.audit import audit_action
from app.api.dependencies.auth import CurrentUser, get_current_user
from app.api.dependencies.db import get_db
from app.core.permissions.rbac import require_operator
from app.modules.programs.scope_service import ScopeService
from app.modules.scope_parser.service import ScopeParserService
from app.schemas.scope import ScopeChangeLogRead, ScopeRawRead, ScopeRawUpdate
from app.schemas.scope_entities import ReviewItemAction, ScopeSummary

router = APIRouter(prefix="/companies/{company_id}/programs/{program_id}/scope", tags=["scope"])


@router.get("/", response_model=ScopeRawRead)
async def get_scope(
    company_id: uuid.UUID,
    program_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> ScopeRawRead:
    program = await ScopeService(db).get_scope(company_id, program_id)
    return ScopeRawRead(
        program_id=program.id,
        scope_raw=program.scope_raw,
        scope_last_reviewed_at=program.scope_last_reviewed_at,
    )


@router.put("/", response_model=ScopeRawRead)
async def update_scope_raw(
    company_id: uuid.UUID,
    program_id: uuid.UUID,
    data: ScopeRawUpdate,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_operator),
) -> ScopeRawRead:
    program = await ScopeService(db).update_scope_raw(company_id, program_id, data, user.id)
    await audit_action(
        "update_scope_raw", "program", str(program_id),
        {"company_id": str(company_id)}, db, user,
    )
    await db.commit()
    return ScopeRawRead(
        program_id=program.id,
        scope_raw=program.scope_raw,
        scope_last_reviewed_at=program.scope_last_reviewed_at,
    )


@router.get("/history", response_model=list[ScopeChangeLogRead])
async def list_scope_history(
    company_id: uuid.UUID,
    program_id: uuid.UUID,
    offset: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> list[ScopeChangeLogRead]:
    # Tenant check via scope service
    await ScopeService(db).get_scope(company_id, program_id)
    return await ScopeService(db).list_change_logs(program_id, offset=offset, limit=limit)


@router.post("/parse")
async def parse_scope_endpoint(
    company_id: uuid.UUID,
    program_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_operator),
) -> dict:
    """Parse raw scope into normalized ScopeItems (OCT-023). Idempotent."""
    counts = await ScopeParserService(db).parse_and_store(company_id, program_id)
    await audit_action(
        "parse_scope", "program", str(program_id),
        {"company_id": str(company_id), **counts}, db, user,
    )
    await db.commit()
    return counts


@router.get("/summary", response_model=ScopeSummary)
async def scope_summary(
    company_id: uuid.UUID,
    program_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> ScopeSummary:
    """Deterministic allowed/forbidden/ambiguous summary (OCT-024)."""
    await ScopeService(db).get_scope(company_id, program_id)  # tenant check
    return await ScopeParserService(db).get_summary(program_id)


@router.post("/review")
async def review_scope_item(
    company_id: uuid.UUID,
    program_id: uuid.UUID,
    action: ReviewItemAction,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_operator),
) -> dict:
    """Confirm/reject a scope item under manual review (OCT-025)."""
    await ScopeService(db).get_scope(company_id, program_id)  # tenant check
    await ScopeParserService(db).review_item(
        program_id, action.item_type, action.item_id, action.action
    )
    await audit_action(
        "review_scope_item", action.item_type, str(action.item_id),
        {"company_id": str(company_id), "action": action.action}, db, user,
    )
    await db.commit()
    return {"status": "ok", "action": action.action}

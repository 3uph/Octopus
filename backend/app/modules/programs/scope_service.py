"""Scope raw persistence service — stores raw scope + change history.

NO parsing, NO normalization, NO Scope Gate. Those are later issues (Sprint 2).
This only persists the raw text and records a ScopeChangeLog on each change.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.program import Program
from app.models.scope_change_log import ScopeChangeLog
from app.modules.programs.service import ProgramService
from app.schemas.scope import ScopeRawUpdate


class ScopeService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._programs = ProgramService(db)

    async def get_scope(self, company_id: uuid.UUID, program_id: uuid.UUID) -> Program:
        return await self._programs.get_in_company_or_404(company_id, program_id)

    async def update_scope_raw(
        self,
        company_id: uuid.UUID,
        program_id: uuid.UUID,
        data: ScopeRawUpdate,
        changed_by: uuid.UUID | None,
    ) -> Program:
        program = await self._programs.get_in_company_or_404(company_id, program_id)

        before_value = program.scope_raw
        change_type = "create" if before_value is None else "update"

        # Record change log
        log = ScopeChangeLog(
            id=uuid.uuid4(),
            program_id=program_id,
            changed_by=changed_by,
            change_type=change_type,
            before={"scope_raw": before_value},
            after={"scope_raw": data.scope_raw},
        )
        self._db.add(log)

        # Update program
        program.scope_raw = data.scope_raw
        program.scope_last_reviewed_at = datetime.now(timezone.utc)

        await self._db.flush()
        await self._db.refresh(program)
        return program

    async def list_change_logs(
        self, program_id: uuid.UUID, offset: int = 0, limit: int = 50
    ) -> list[ScopeChangeLog]:
        result = await self._db.execute(
            select(ScopeChangeLog)
            .where(ScopeChangeLog.program_id == program_id)
            .order_by(ScopeChangeLog.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

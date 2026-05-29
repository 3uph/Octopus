"""Program & Audit services — business logic with tenant checks + transitions."""
from __future__ import annotations

import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.repositories.program import AuditRepository, ProgramRepository
from app.models.audit import Audit
from app.models.program import Program
from app.modules.programs.transitions import is_valid_transition
from app.schemas.audit import AuditCreate, AuditUpdate
from app.schemas.program import ProgramCreate, ProgramUpdate


class ProgramService:
    def __init__(self, db: AsyncSession) -> None:
        self._repo = ProgramRepository(db)
        self._db = db

    async def get_or_404(self, program_id: uuid.UUID) -> Program:
        program = await self._repo.get(program_id)
        if not program:
            raise HTTPException(status_code=404, detail="Program not found")
        return program

    async def get_in_company_or_404(
        self, company_id: uuid.UUID, program_id: uuid.UUID
    ) -> Program:
        """Tenant-checked fetch: program must belong to company."""
        program = await self.get_or_404(program_id)
        if program.company_id != company_id:
            raise HTTPException(status_code=404, detail="Program not found in company")
        return program

    async def list(self, company_id: uuid.UUID, offset: int = 0, limit: int = 50) -> list[Program]:
        return await self._repo.list_by_company(company_id, offset=offset, limit=limit)

    async def create(self, company_id: uuid.UUID, data: ProgramCreate) -> Program:
        return await self._repo.create(company_id, data)

    async def update(
        self, company_id: uuid.UUID, program_id: uuid.UUID, data: ProgramUpdate
    ) -> Program:
        program = await self.get_in_company_or_404(company_id, program_id)
        # Validate state transition if status is changing
        if data.status is not None and not is_valid_transition(program.status, data.status):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Invalid status transition: {program.status.value} -> {data.status.value}",
            )
        return await self._repo.update(program, data)

    async def delete(self, company_id: uuid.UUID, program_id: uuid.UUID) -> None:
        program = await self.get_in_company_or_404(company_id, program_id)
        await self._repo.delete(program)


class AuditService:
    def __init__(self, db: AsyncSession) -> None:
        self._repo = AuditRepository(db)
        self._program_repo = ProgramRepository(db)
        self._db = db

    async def _program_or_404(self, program_id: uuid.UUID) -> Program:
        program = await self._program_repo.get(program_id)
        if not program:
            raise HTTPException(status_code=404, detail="Program not found")
        return program

    async def get_in_program_or_404(
        self, program_id: uuid.UUID, audit_id: uuid.UUID
    ) -> Audit:
        audit = await self._repo.get(audit_id)
        if not audit or audit.program_id != program_id:
            raise HTTPException(status_code=404, detail="Audit not found in program")
        return audit

    async def list(self, program_id: uuid.UUID, offset: int = 0, limit: int = 50) -> list[Audit]:
        await self._program_or_404(program_id)
        return await self._repo.list_by_program(program_id, offset=offset, limit=limit)

    async def create(self, program_id: uuid.UUID, data: AuditCreate) -> Audit:
        await self._program_or_404(program_id)
        return await self._repo.create(program_id, data)

    async def update(
        self, program_id: uuid.UUID, audit_id: uuid.UUID, data: AuditUpdate
    ) -> Audit:
        audit = await self.get_in_program_or_404(program_id, audit_id)
        return await self._repo.update(audit, data)

    async def delete(self, program_id: uuid.UUID, audit_id: uuid.UUID) -> None:
        audit = await self.get_in_program_or_404(program_id, audit_id)
        await self._repo.delete(audit)

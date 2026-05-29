"""Program & Audit repositories — DB access with tenant isolation."""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import Audit
from app.models.program import Program
from app.schemas.audit import AuditCreate, AuditUpdate
from app.schemas.program import ProgramCreate, ProgramUpdate


class ProgramRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get(self, program_id: uuid.UUID) -> Program | None:
        result = await self._db.execute(select(Program).where(Program.id == program_id))
        return result.scalar_one_or_none()

    async def list_by_company(
        self, company_id: uuid.UUID, offset: int = 0, limit: int = 50
    ) -> list[Program]:
        # Tenant isolation: always filter by company_id
        result = await self._db.execute(
            select(Program)
            .where(Program.company_id == company_id)
            .order_by(Program.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def create(self, company_id: uuid.UUID, data: ProgramCreate) -> Program:
        program = Program(company_id=company_id, **data.model_dump())
        self._db.add(program)
        await self._db.flush()
        await self._db.refresh(program)
        return program

    async def update(self, program: Program, data: ProgramUpdate) -> Program:
        for field, value in data.model_dump(exclude_none=True).items():
            setattr(program, field, value)
        await self._db.flush()
        await self._db.refresh(program)
        return program

    async def delete(self, program: Program) -> None:
        await self._db.delete(program)
        await self._db.flush()


class AuditRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get(self, audit_id: uuid.UUID) -> Audit | None:
        result = await self._db.execute(select(Audit).where(Audit.id == audit_id))
        return result.scalar_one_or_none()

    async def list_by_program(
        self, program_id: uuid.UUID, offset: int = 0, limit: int = 50
    ) -> list[Audit]:
        # Tenant isolation: always filter by program_id
        result = await self._db.execute(
            select(Audit)
            .where(Audit.program_id == program_id)
            .order_by(Audit.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def create(self, program_id: uuid.UUID, data: AuditCreate) -> Audit:
        audit = Audit(program_id=program_id, **data.model_dump())
        self._db.add(audit)
        await self._db.flush()
        await self._db.refresh(audit)
        return audit

    async def update(self, audit: Audit, data: AuditUpdate) -> Audit:
        for field, value in data.model_dump(exclude_none=True).items():
            setattr(audit, field, value)
        await self._db.flush()
        await self._db.refresh(audit)
        return audit

    async def delete(self, audit: Audit) -> None:
        await self._db.delete(audit)
        await self._db.flush()

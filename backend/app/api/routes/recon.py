"""Recon routes — passive discovery with mandatory Scope Gate + dry-run.

Active/manual recon is NOT available yet (placeholder only).
Every target passes through the Scope Gate. Out-of-scope = hard block.
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.audit import audit_action
from app.api.dependencies.auth import CurrentUser, get_current_user
from app.api.dependencies.db import get_db
from app.core.permissions.rbac import require_operator
from app.database.repositories.asset import AssetRepository
from app.models.scan import ScanJob, ToolRun
from app.modules.discovery.service import DiscoveryService
from app.modules.programs.service import ProgramService
from app.schemas.recon import AssetRead, ReconRequest, ScanJobRead, ToolRunRead

router = APIRouter(prefix="/companies/{company_id}/programs/{program_id}", tags=["recon"])


@router.post("/recon/passive/dry-run")
async def passive_dry_run(
    company_id: uuid.UUID,
    program_id: uuid.UUID,
    body: ReconRequest,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> dict:
    """Dry-run: show eligible vs blocked targets. Executes nothing."""
    plan = await DiscoveryService(db).plan(company_id, program_id, body.targets)
    return {
        "mode": plan.mode,
        "eligible_targets": plan.eligible_targets,
        "blocked_targets": plan.blocked_targets,
        "sources": plan.sources,
        "note": plan.note,
    }


@router.post("/recon/passive/run")
async def passive_run(
    company_id: uuid.UUID,
    program_id: uuid.UUID,
    body: ReconRequest,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_operator),
) -> dict:
    """Execute passive discovery for Scope-Gate-approved targets."""
    result = await DiscoveryService(db).run_passive(
        company_id, program_id, body.targets, user.id
    )
    await audit_action(
        "recon_passive_run", "program", str(program_id),
        {"company_id": str(company_id), "eligible": result.eligible_targets,
         "assets_created": result.assets_created}, db, user, mode="passive",
    )
    await db.commit()
    return {
        "scan_job_id": result.scan_job_id,
        "eligible_targets": result.eligible_targets,
        "blocked_targets": result.blocked_targets,
        "assets_created": result.assets_created,
        "assets_seen": result.assets_seen,
        "subdomains_out_of_scope": result.subdomains_out_of_scope,
    }


@router.post("/recon/active/run", status_code=status.HTTP_501_NOT_IMPLEMENTED)
async def active_run_placeholder(
    company_id: uuid.UUID,
    program_id: uuid.UUID,
    user: CurrentUser = Depends(require_operator),
) -> dict:
    """Active/manual recon is not available yet (placeholder)."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Active recon not implemented yet. Passive + dry-run only.",
    )


@router.get("/assets", response_model=list[AssetRead])
async def list_assets(
    company_id: uuid.UUID,
    program_id: uuid.UUID,
    offset: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> list[AssetRead]:
    await ProgramService(db).get_in_company_or_404(company_id, program_id)
    return await AssetRepository(db).list(program_id, offset=offset, limit=limit)


@router.get("/scan-jobs", response_model=list[ScanJobRead])
async def list_scan_jobs(
    company_id: uuid.UUID,
    program_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> list[ScanJobRead]:
    await ProgramService(db).get_in_company_or_404(company_id, program_id)
    rows = (await db.execute(
        select(ScanJob).where(ScanJob.program_id == program_id).order_by(ScanJob.created_at.desc())
    )).scalars().all()
    return list(rows)


@router.get("/scan-jobs/{job_id}/tool-runs", response_model=list[ToolRunRead])
async def list_tool_runs(
    company_id: uuid.UUID,
    program_id: uuid.UUID,
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> list[ToolRunRead]:
    await ProgramService(db).get_in_company_or_404(company_id, program_id)
    rows = (await db.execute(
        select(ToolRun).where(ToolRun.scan_job_id == job_id).order_by(ToolRun.created_at.desc())
    )).scalars().all()
    return list(rows)

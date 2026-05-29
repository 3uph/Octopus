"""Passive discovery orchestration (OCT-029 dry-run + passive execute).

Flow:
  1. Resolve target domains for a program.
  2. Scope Gate each target. Only IN targets are eligible; others are blocked.
  3. dry_run  -> return the plan (eligible vs blocked), execute nothing.
  4. passive  -> run passive sources for eligible targets, dedup subdomains,
                 Scope-Gate each discovered subdomain, persist Assets,
                 record ScanJob + ToolRun.

NEVER touches targets actively. NO subprocess. NO offensive tools.
Discovered subdomains out of scope are recorded with scope_decision=out (not IN).
"""
from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.database.repositories.asset import AssetRepository
from app.models.asset import AssetType
from app.models.enums import Confidence, ScopeDecision
from app.models.scan import JobStatus, ReconMode, ScanJob, ToolRun
from app.modules.discovery.sources.base import PassiveSource
from app.modules.discovery.sources.crtsh import CrtShSource
from app.modules.programs.service import ProgramService
from app.modules.scope_gate.gate import ScopeGate

logger = get_logger(__name__)


@dataclass
class DiscoveryPlan:
    mode: str
    eligible_targets: list[str] = field(default_factory=list)
    blocked_targets: list[dict] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)
    note: str = ""


@dataclass
class DiscoveryResult:
    scan_job_id: str
    mode: str
    eligible_targets: list[str]
    blocked_targets: list[dict]
    assets_created: int
    assets_seen: int
    subdomains_out_of_scope: int


class DiscoveryService:
    def __init__(self, db: AsyncSession, sources: list[PassiveSource] | None = None) -> None:
        self._db = db
        self._programs = ProgramService(db)
        self._gate = ScopeGate(db)
        self._assets = AssetRepository(db)
        # Passive sources only. Injected for tests (offline).
        self._sources = sources if sources is not None else [CrtShSource()]

    async def _eligible_and_blocked(
        self, program_id: uuid.UUID, targets: list[str]
    ) -> tuple[list[str], list[dict]]:
        eligible: list[str] = []
        blocked: list[dict] = []
        for t in targets:
            result = await self._gate.check(program_id, t, "domain")
            if result.allowed:
                eligible.append(t)
            else:
                blocked.append({"target": t, "decision": result.decision.value})
        return eligible, blocked

    async def plan(
        self, company_id: uuid.UUID, program_id: uuid.UUID, targets: list[str]
    ) -> DiscoveryPlan:
        """Dry-run: show what would run, what is blocked. Executes nothing."""
        await self._programs.get_in_company_or_404(company_id, program_id)
        eligible, blocked = await self._eligible_and_blocked(program_id, targets)
        return DiscoveryPlan(
            mode=ReconMode.DRY_RUN.value,
            eligible_targets=eligible,
            blocked_targets=blocked,
            sources=[s.name for s in self._sources],
            note="Dry-run only. No execution performed.",
        )

    async def run_passive(
        self,
        company_id: uuid.UUID,
        program_id: uuid.UUID,
        targets: list[str],
        requested_by: uuid.UUID | None,
    ) -> DiscoveryResult:
        """Execute passive discovery for in-scope targets. Records ScanJob/ToolRun."""
        await self._programs.get_in_company_or_404(company_id, program_id)
        eligible, blocked = await self._eligible_and_blocked(program_id, targets)

        job = ScanJob(
            id=uuid.uuid4(),
            program_id=program_id,
            mode=ReconMode.PASSIVE,
            status=JobStatus.RUNNING,
            targets={"requested": targets, "eligible": eligible, "blocked": blocked},
            requested_by=requested_by,
            dry_run=False,
            started_at=datetime.now(timezone.utc),
        )
        self._db.add(job)
        await self._db.flush()

        if not eligible:
            job.status = JobStatus.DONE
            job.finished_at = datetime.now(timezone.utc)
            job.summary = {"note": "no eligible targets (all blocked by Scope Gate)"}
            await self._db.flush()
            raise HTTPException(
                status_code=403,
                detail="No targets approved by Scope Gate. All blocked or out of scope.",
            )

        created = seen = oos = 0
        for source in self._sources:
            tr = ToolRun(
                id=uuid.uuid4(),
                scan_job_id=job.id,
                tool_name=source.name,
                mode=ReconMode.PASSIVE,
                status=JobStatus.RUNNING,
                started_at=datetime.now(timezone.utc),
                target_scope={"eligible": eligible},
            )
            self._db.add(tr)
            await self._db.flush()

            produced = 0
            for domain in eligible:
                res = await source.discover(domain)
                for sub in res.subdomains:
                    # Scope-gate every discovered subdomain
                    gate_res = await self._gate.check(program_id, sub, "domain")
                    decision = gate_res.decision
                    if decision != ScopeDecision.IN:
                        oos += 1
                    asset_type = AssetType.SUBDOMAIN if sub != domain else AssetType.DOMAIN
                    _, was_created = await self._assets.upsert(
                        program_id=program_id,
                        value=sub,
                        asset_type=asset_type,
                        scope_decision=decision,
                        discovered_via=source.name,
                        confidence=Confidence.MEDIUM,
                    )
                    produced += 1
                    if was_created:
                        created += 1
                    else:
                        seen += 1

            tr.status = JobStatus.DONE
            tr.finished_at = datetime.now(timezone.utc)
            tr.items_produced = produced
            await self._db.flush()

        job.status = JobStatus.DONE
        job.finished_at = datetime.now(timezone.utc)
        job.summary = {"assets_created": created, "assets_seen": seen, "out_of_scope": oos}
        await self._db.flush()

        return DiscoveryResult(
            scan_job_id=str(job.id),
            mode=ReconMode.PASSIVE.value,
            eligible_targets=eligible,
            blocked_targets=blocked,
            assets_created=created,
            assets_seen=seen,
            subdomains_out_of_scope=oos,
        )

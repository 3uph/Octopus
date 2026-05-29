"""Intel OSINT service — create + run + persist + query analyses.

Run is synchronous-controlled (the project has Dramatiq, but discovery already
runs sync; intel runs are depth-bounded). Status lifecycle:
pending -> running -> completed | partial | failed.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.modules.intel_osint.config import get_intel_config
from app.modules.intel_osint.models import (
    IntelCollectorStatus, IntelEntity, IntelFinding, IntelRelationship,
    IntelRiskHypothesis, IntelWarning, IntelligenceAnalysis,
)
from app.modules.intel_osint.orchestrator import IntelOrchestrator, default_collectors
from app.modules.intel_osint.schemas import AnalysisCreate

logger = get_logger(__name__)


class IntelService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create_and_run(
        self, data: AnalysisCreate, user_id: uuid.UUID | None,
        orchestrator: IntelOrchestrator | None = None,
    ) -> IntelligenceAnalysis:
        flags = {
            "include_documents": data.include_documents,
            "include_github": data.include_github,
            "include_public_records": data.include_public_records,
            "include_social": data.include_social,
            "include_news": data.include_news,
            "include_leaks": data.include_leaks,
        }
        analysis = IntelligenceAnalysis(
            id=uuid.uuid4(), target_company_name=data.company_name,
            target_root_domain=data.root_domain, country=data.country, nif=data.nif,
            aliases=data.aliases, depth=data.depth, flags=flags, status="running",
            created_by=user_id, started_at=datetime.now(timezone.utc),
        )
        self._db.add(analysis)
        await self._db.flush()

        orch = orchestrator or IntelOrchestrator(default_collectors())
        t0 = datetime.now(timezone.utc)
        try:
            out = await orch.run(
                company_name=data.company_name, root_domain=data.root_domain,
                country=data.country, nif=data.nif, aliases=data.aliases,
                depth=data.depth, flags=flags)
        except Exception as exc:  # orchestrator itself failing → mark failed, persist
            logger.warning("intel orchestrator failed: %s", type(exc).__name__)
            analysis.status = "failed"
            analysis.finished_at = datetime.now(timezone.utc)
            analysis.metadata_json = {"error": type(exc).__name__}
            await self._db.flush()
            return analysis

        # Persist children
        for f in out.findings:
            self._db.add(IntelFinding(id=uuid.uuid4(), analysis_id=analysis.id,
                type=f["type"], title=f["title"][:512], value=f.get("value"),
                description=f.get("description"), source=f.get("source"),
                evidence_url=(f.get("evidence_url") or None), confidence=f["confidence"],
                risk_level=f["risk_level"], tags=f.get("tags"),
                raw_context_json=f.get("raw_context")))
        for e in out.entities:
            self._db.add(IntelEntity(id=uuid.uuid4(), analysis_id=analysis.id,
                entity_type=e["entity_type"], value=e["value"][:1024],
                normalized_value=e["normalized_value"][:1024], confidence=e["confidence"],
                source=e.get("source"), tags=e.get("tags"), metadata_json=e.get("metadata")))
        for r in out.relationships:
            self._db.add(IntelRelationship(id=uuid.uuid4(), analysis_id=analysis.id,
                source_value=r.get("source_value"), target_value=r.get("target_value"),
                relationship_type=r["relationship_type"], confidence=r["confidence"],
                evidence=r.get("evidence")))
        for rk in out.risks:
            self._db.add(IntelRiskHypothesis(id=uuid.uuid4(), analysis_id=analysis.id,
                key=rk["key"], title=rk["title"][:512], description=rk.get("description"),
                risk_level=rk["risk_level"], confidence=rk["confidence"],
                evidence_summary=rk.get("evidence_summary"), why_it_matters=rk.get("why_it_matters"),
                recommended_validation=rk.get("recommended_validation"),
                recommended_remediation=rk.get("recommended_remediation"),
                related_findings_json=rk.get("related_findings_json"), tags=rk.get("tags")))
        for w in out.warnings:
            self._db.add(IntelWarning(id=uuid.uuid4(), analysis_id=analysis.id,
                collector=w.get("collector"), level=w.get("level", "warning"),
                message=w["message"][:2000]))
        for c in out.collectors:
            self._db.add(IntelCollectorStatus(id=uuid.uuid4(), analysis_id=analysis.id,
                collector=c["collector"], status=c["status"],
                items_produced=c.get("items_produced", 0),
                duration_seconds=c.get("duration_seconds"), message=c.get("message")))

        finished = datetime.now(timezone.utc)
        analysis.status = out.status
        analysis.finished_at = finished
        analysis.duration_seconds = (finished - t0).total_seconds()
        analysis.summary_json = out.summary
        analysis.exposure_score_json = out.exposure
        analysis.metadata_json = {"graph": out.graph}
        await self._db.flush()
        return analysis

    async def get_or_404(self, analysis_id: uuid.UUID) -> IntelligenceAnalysis:
        a = (await self._db.execute(
            select(IntelligenceAnalysis).where(IntelligenceAnalysis.id == analysis_id)
        )).scalar_one_or_none()
        if not a:
            raise HTTPException(status_code=404, detail="Analysis not found")
        return a

    async def list(self, offset: int = 0, limit: int = 50) -> list[IntelligenceAnalysis]:
        rows = (await self._db.execute(
            select(IntelligenceAnalysis).order_by(IntelligenceAnalysis.created_at.desc())
            .offset(offset).limit(limit))).scalars().all()
        return list(rows)

    async def _children(self, model, analysis_id: uuid.UUID):
        return list((await self._db.execute(
            select(model).where(model.analysis_id == analysis_id))).scalars().all())

    async def findings(self, analysis_id, risk_level=None, type_=None):
        rows = await self._children(IntelFinding, analysis_id)
        if risk_level:
            rows = [r for r in rows if r.risk_level == risk_level]
        if type_:
            rows = [r for r in rows if r.type == type_]
        return rows

    async def entities(self, analysis_id, entity_type=None):
        rows = await self._children(IntelEntity, analysis_id)
        if entity_type:
            rows = [r for r in rows if r.entity_type == entity_type]
        return rows

    async def relationships(self, analysis_id):
        return await self._children(IntelRelationship, analysis_id)

    async def risks(self, analysis_id):
        return await self._children(IntelRiskHypothesis, analysis_id)

    async def warnings(self, analysis_id):
        return await self._children(IntelWarning, analysis_id)

    async def collectors(self, analysis_id):
        return await self._children(IntelCollectorStatus, analysis_id)

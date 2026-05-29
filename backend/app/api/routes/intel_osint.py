"""Intel OSINT API — create/list/detail analyses + findings/entities/risks/export.

Auth required. Mutations (create) require operator. Reads require any user.
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.audit import audit_action
from app.api.dependencies.auth import CurrentUser, get_current_user
from app.api.dependencies.db import get_db
from app.core.permissions.rbac import require_operator
from app.modules.intel_osint.outputs.json_exporter import export_json
from app.modules.intel_osint.outputs.markdown_exporter import export_markdown
from app.modules.intel_osint.schemas import (
    AnalysisCreate, AnalysisRead, CollectorStatusRead, EntityRead, FindingRead,
    RelationshipRead, RiskRead, WarningRead,
)
from app.modules.intel_osint.service import IntelService

router = APIRouter(prefix="/intelligence/analyses", tags=["intel-osint"])


@router.post("", response_model=AnalysisRead, status_code=201)
async def create_analysis(
    data: AnalysisCreate,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_operator),
) -> AnalysisRead:
    svc = IntelService(db)
    analysis = await svc.create_and_run(data, user.id)
    await audit_action("create_intel_analysis", "intel_analysis", str(analysis.id),
                       {"company": data.company_name, "domain": data.root_domain or ""},
                       db, user, mode="passive")
    await db.commit()
    return analysis


@router.get("", response_model=list[AnalysisRead])
async def list_analyses(
    offset: int = 0, limit: int = 50,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> list[AnalysisRead]:
    return await IntelService(db).list(offset=offset, limit=limit)


@router.get("/{analysis_id}", response_model=AnalysisRead)
async def get_analysis(
    analysis_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> AnalysisRead:
    return await IntelService(db).get_or_404(analysis_id)


@router.get("/{analysis_id}/findings", response_model=list[FindingRead])
async def get_findings(
    analysis_id: uuid.UUID, risk_level: str | None = None, type: str | None = None,
    db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user),
) -> list[FindingRead]:
    svc = IntelService(db)
    await svc.get_or_404(analysis_id)
    return await svc.findings(analysis_id, risk_level=risk_level, type_=type)


@router.get("/{analysis_id}/entities", response_model=list[EntityRead])
async def get_entities(
    analysis_id: uuid.UUID, entity_type: str | None = None,
    db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user),
) -> list[EntityRead]:
    svc = IntelService(db)
    await svc.get_or_404(analysis_id)
    return await svc.entities(analysis_id, entity_type=entity_type)


@router.get("/{analysis_id}/relationships", response_model=list[RelationshipRead])
async def get_relationships(
    analysis_id: uuid.UUID,
    db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user),
) -> list[RelationshipRead]:
    svc = IntelService(db)
    await svc.get_or_404(analysis_id)
    return await svc.relationships(analysis_id)


@router.get("/{analysis_id}/risks", response_model=list[RiskRead])
async def get_risks(
    analysis_id: uuid.UUID,
    db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user),
) -> list[RiskRead]:
    svc = IntelService(db)
    await svc.get_or_404(analysis_id)
    return await svc.risks(analysis_id)


@router.get("/{analysis_id}/warnings", response_model=list[WarningRead])
async def get_warnings(
    analysis_id: uuid.UUID,
    db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user),
) -> list[WarningRead]:
    svc = IntelService(db)
    await svc.get_or_404(analysis_id)
    return await svc.warnings(analysis_id)


@router.get("/{analysis_id}/collectors", response_model=list[CollectorStatusRead])
async def get_collectors(
    analysis_id: uuid.UUID,
    db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user),
) -> list[CollectorStatusRead]:
    svc = IntelService(db)
    await svc.get_or_404(analysis_id)
    return await svc.collectors(analysis_id)


async def _full_export(db: AsyncSession, analysis_id: uuid.UUID) -> dict:
    svc = IntelService(db)
    a = await svc.get_or_404(analysis_id)
    analysis = {
        "id": str(a.id), "target_company_name": a.target_company_name,
        "target_root_domain": a.target_root_domain, "country": a.country, "nif": a.nif,
        "aliases": a.aliases, "depth": a.depth, "status": a.status,
        "duration_seconds": a.duration_seconds, "summary_json": a.summary_json,
        "exposure_score_json": a.exposure_score_json,
    }
    def dump(rows, fields):
        return [{f: getattr(r, f) if not isinstance(getattr(r, f, None), uuid.UUID)
                 else str(getattr(r, f)) for f in fields} for r in rows]
    findings = dump(await svc.findings(analysis_id),
                    ["type", "title", "value", "description", "source", "evidence_url",
                     "confidence", "risk_level", "tags"])
    entities = dump(await svc.entities(analysis_id),
                    ["entity_type", "value", "normalized_value", "confidence", "source", "tags"])
    rels = dump(await svc.relationships(analysis_id),
                ["source_value", "target_value", "relationship_type", "confidence", "evidence"])
    risks = dump(await svc.risks(analysis_id),
                 ["key", "title", "description", "risk_level", "confidence", "evidence_summary",
                  "why_it_matters", "recommended_validation", "recommended_remediation", "tags"])
    warnings = dump(await svc.warnings(analysis_id), ["collector", "level", "message"])
    collectors = dump(await svc.collectors(analysis_id),
                      ["collector", "status", "items_produced", "duration_seconds", "message"])
    return {"analysis": analysis, "findings": findings, "entities": entities,
            "relationships": rels, "risks": risks, "warnings": warnings, "collectors": collectors}


@router.get("/{analysis_id}/export/json")
async def export_analysis_json(
    analysis_id: uuid.UUID,
    db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user),
) -> dict:
    d = await _full_export(db, analysis_id)
    return export_json(d["analysis"], d["findings"], d["entities"], d["relationships"],
                       d["risks"], d["warnings"], d["collectors"])


@router.get("/{analysis_id}/export/markdown")
async def export_analysis_markdown(
    analysis_id: uuid.UUID,
    db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user),
) -> Response:
    d = await _full_export(db, analysis_id)
    md = export_markdown(d["analysis"], d["findings"], d["entities"], d["risks"], d["warnings"])
    return Response(content=md, media_type="text/markdown")

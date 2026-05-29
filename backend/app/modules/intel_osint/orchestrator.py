"""Orchestrator — runs collectors, normalizes/dedups, scores, builds output.

Resilience contract: a failing collector becomes status=partial + a warning,
never a crashed analysis. Overall status:
  - failed    : every collector failed
  - partial   : at least one collector failed/partial OR some skipped+some ok
  - completed : all ran without failure (skipped allowed if degraded)
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from app.core.logging import get_logger
from app.modules.intel_osint.analyzers.exposure_score import compute_exposure
from app.modules.intel_osint.analyzers.risk_hypothesis_engine import generate_hypotheses
from app.modules.intel_osint.collectors.base import (
    Collector, CollectorContext, RawEntity, RawFinding, RawRelationship,
)
from app.modules.intel_osint.config import IntelConfig, get_intel_config
from app.modules.intel_osint.graph.graph_builder import build_graph
from app.modules.intel_osint.outputs.summary_builder import build_summary

logger = get_logger(__name__)


def _normalize(entity_type: str, value: str) -> str:
    v = (value or "").strip().lower()
    if entity_type in ("domain", "subdomain", "email"):
        v = v.rstrip(".")
    return v


@dataclass
class OrchestratorOutput:
    status: str
    findings: list[dict] = field(default_factory=list)
    entities: list[dict] = field(default_factory=list)
    relationships: list[dict] = field(default_factory=list)
    risks: list[dict] = field(default_factory=list)
    warnings: list[dict] = field(default_factory=list)
    collectors: list[dict] = field(default_factory=list)
    summary: dict[str, Any] = field(default_factory=dict)
    exposure: dict[str, Any] = field(default_factory=dict)
    graph: dict[str, Any] = field(default_factory=dict)


def _rf(f: RawFinding) -> dict:
    return {"type": f.type, "title": f.title, "value": f.value, "description": f.description,
            "source": f.source, "evidence_url": f.evidence_url, "confidence": f.confidence,
            "risk_level": f.risk_level, "tags": f.tags, "raw_context": f.raw_context}


def _re(e: RawEntity) -> dict:
    return {"entity_type": e.entity_type, "value": e.value,
            "normalized_value": e.normalized_value or _normalize(e.entity_type, e.value),
            "confidence": e.confidence, "source": e.source, "tags": e.tags, "metadata": e.metadata}


def _rr(r: RawRelationship) -> dict:
    return {"source_value": r.source_value, "target_value": r.target_value,
            "relationship_type": r.relationship_type, "confidence": r.confidence,
            "evidence": r.evidence}


class IntelOrchestrator:
    def __init__(self, collectors: list[Collector], config: IntelConfig | None = None) -> None:
        self._collectors = collectors
        self._config = config or get_intel_config()

    async def run(
        self, company_name: str, root_domain: str | None, country: str,
        nif: str | None, aliases: list[str], depth: str, flags: dict[str, bool],
    ) -> OrchestratorOutput:
        ctx = CollectorContext(
            company_name=company_name, root_domain=root_domain, country=country,
            nif=nif, aliases=aliases or [], depth=depth, flags=flags or {}, config=self._config)

        findings: list[dict] = []
        ent_index: dict[tuple[str, str], dict] = {}
        relationships: list[dict] = []
        warnings: list[dict] = []
        collector_statuses: list[dict] = []
        any_ok = False
        any_fail = False

        for collector in self._collectors:
            t0 = time.monotonic()
            try:
                result = await collector.collect(ctx)
            except Exception as exc:  # defensive: collector must not crash analysis
                logger.warning("collector %s crashed: %s", collector.name, type(exc).__name__)
                any_fail = True
                collector_statuses.append({"collector": collector.name, "status": "failed",
                                           "items_produced": 0,
                                           "duration_seconds": round(time.monotonic() - t0, 3),
                                           "message": f"crashed: {type(exc).__name__}"})
                warnings.append({"collector": collector.name, "level": "error",
                                 "message": f"collector crashed: {type(exc).__name__}"})
                continue

            produced = len(result.findings) + len(result.entities)
            collector_statuses.append({
                "collector": collector.name, "status": result.status,
                "items_produced": produced,
                "duration_seconds": round(time.monotonic() - t0, 3),
                "message": result.message})
            for w in result.warnings:
                warnings.append({"collector": collector.name, "level": "warning", "message": w})

            if result.status in ("completed", "partial"):
                any_ok = any_ok or produced > 0 or result.status == "completed"
            if result.status in ("failed",):
                any_fail = True
            if result.status == "partial":
                any_fail = True

            for f in result.findings:
                findings.append(_rf(f))
            for e in result.entities:
                d = _re(e)
                key = (d["entity_type"], d["normalized_value"])
                if key in ent_index:
                    # merge: keep highest confidence, union tags
                    prev = ent_index[key]
                    order = {"high": 3, "medium": 2, "low": 1, "unknown": 0}
                    if order.get(d["confidence"], 0) > order.get(prev["confidence"], 0):
                        prev["confidence"] = d["confidence"]
                    prev["tags"] = sorted(set((prev.get("tags") or []) + (d.get("tags") or [])))
                else:
                    ent_index[key] = d
            for r in result.relationships:
                relationships.append(_rr(r))

        entities = list(ent_index.values())

        # Analyzers
        exposure = compute_exposure(findings, entities)
        hyps = generate_hypotheses(findings, entities)
        risks = [{
            "key": h.key, "title": h.title, "description": h.description,
            "risk_level": h.risk_level, "confidence": h.confidence,
            "evidence_summary": h.evidence_summary, "why_it_matters": h.why_it_matters,
            "recommended_validation": h.recommended_validation,
            "recommended_remediation": h.recommended_remediation,
            "tags": h.tags, "related_findings_json": h.related_findings,
        } for h in hyps]

        summary = build_summary(company_name, root_domain, findings, entities, risks, warnings, exposure)
        graph = build_graph(entities, relationships)

        # Overall status
        if collector_statuses and all(c["status"] == "failed" for c in collector_statuses):
            status = "failed"
        elif any_fail or any(c["status"] in ("partial", "skipped") for c in collector_statuses):
            status = "partial" if any_ok else "partial"
        else:
            status = "completed"

        return OrchestratorOutput(
            status=status, findings=findings, entities=entities, relationships=relationships,
            risks=risks, warnings=warnings, collectors=collector_statuses,
            summary=summary, exposure=exposure, graph=graph)


def default_collectors(document_urls: list[str] | None = None) -> list[Collector]:
    """Construct the default collector pipeline (real + degraded)."""
    from app.modules.intel_osint.collectors.dns_collector import DNSCollector
    from app.modules.intel_osint.collectors.certificate_collector import CertificateCollector
    from app.modules.intel_osint.collectors.web_crawler_collector import WebCrawlerCollector
    from app.modules.intel_osint.collectors.document_collector import DocumentCollector
    from app.modules.intel_osint.collectors.github_collector import GitHubCollector
    from app.modules.intel_osint.collectors.degraded import (
        LeakCollector, NewsCollector, SearchEngineCollector,
        SocialCollector, SpanishPublicRecordsCollector,
    )
    return [
        DNSCollector(),
        CertificateCollector(),
        WebCrawlerCollector(),
        DocumentCollector(document_urls=document_urls or []),
        GitHubCollector(),
        SpanishPublicRecordsCollector(),
        NewsCollector(),
        SocialCollector(),
        SearchEngineCollector(),
        LeakCollector(),
    ]

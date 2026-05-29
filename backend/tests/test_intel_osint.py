"""Intel OSINT tests — fully offline (no Internet, no DB).

Covers extractors, secret masking, exposure scoring, risk hypotheses,
graph building, exporters, and the orchestrator with mocked collectors
(including collector failure isolation).
"""
from __future__ import annotations

import pytest

from app.modules.intel_osint.extractors.emails import (
    extract_emails, infer_email_pattern,
)
from app.modules.intel_osint.extractors.domains import extract_domains, related_domains
from app.modules.intel_osint.extractors.urls import extract_links, is_document, is_internal
from app.modules.intel_osint.extractors.nif import extract_nifs, validate_nif
from app.modules.intel_osint.extractors.secrets import detect_secrets, mask_secret
from app.modules.intel_osint.extractors.technologies import detect_technologies
from app.modules.intel_osint.analyzers.exposure_score import compute_exposure, CATEGORIES
from app.modules.intel_osint.analyzers.risk_hypothesis_engine import generate_hypotheses
from app.modules.intel_osint.graph.graph_builder import build_graph
from app.modules.intel_osint.outputs.markdown_exporter import export_markdown
from app.modules.intel_osint.outputs.json_exporter import export_json


# ---------------------------------------------------------------------------
# Extractors
# ---------------------------------------------------------------------------

class TestEmailExtractor:
    def test_extract(self):
        text = "contact john.doe@acme.com or sales@acme.com, noise@example.com"
        out = extract_emails(text)
        assert "john.doe@acme.com" in out
        assert "sales@acme.com" in out
        assert "noise@example.com" not in out  # example.com filtered

    def test_infer_pattern_dotted(self):
        emails = ["john.doe@acme.com", "jane.roe@acme.com"]
        assert infer_email_pattern(emails, "acme.com") == "{first}.{last}@acme.com"


class TestDomainExtractor:
    def test_extract(self):
        out = extract_domains("visit acme.com and mail.acme.com or logo.png")
        assert "acme.com" in out
        assert "mail.acme.com" in out
        assert "logo.png" not in out

    def test_related(self):
        out = related_domains(["mail.acme.com", "evil.com", "acme.com"], "acme.com")
        assert set(out) == {"mail.acme.com", "acme.com"}


class TestUrlExtractor:
    def test_links_resolved(self):
        html = '<a href="/about">x</a><a href="https://ext.com/p">y</a>'
        links = extract_links(html, "https://acme.com/")
        assert "https://acme.com/about" in links
        assert "https://ext.com/p" in links

    def test_internal_and_document(self):
        assert is_internal("https://mail.acme.com/x", "acme.com")
        assert not is_internal("https://evil.com", "acme.com")
        assert is_document("https://acme.com/report.pdf")
        assert not is_document("https://acme.com/page")


class TestNif:
    def test_valid_dni(self):
        # 12345678Z is a well-known valid test DNI
        assert validate_nif("12345678Z")

    def test_invalid_dni(self):
        assert not validate_nif("12345678A")

    def test_extract(self):
        out = extract_nifs("DNI 12345678Z aparece aqui")
        assert "12345678Z" in out


class TestSecrets:
    def test_mask_never_full(self):
        masked = mask_secret("supersecretvalue123")
        assert "supersecretvalue123" not in masked
        assert "*" in masked

    def test_detect_aws_masked(self):
        hits = detect_secrets("key AKIAIOSFODNN7EXAMPLE here")
        assert any(h.kind == "aws_access_key" for h in hits)
        # full value never present
        assert all("AKIAIOSFODNN7EXAMPLE" not in h.masked for h in hits)

    def test_detect_assignment(self):
        hits = detect_secrets('password = "hunter2supersecret"')
        assert hits
        assert all("hunter2supersecret" not in h.masked for h in hits)


class TestTechnologies:
    def test_detect(self):
        out = dict(detect_technologies("Server: nginx ... cloudflare ... wp-content"))
        assert out.get("nginx") == "web"
        assert out.get("Cloudflare") == "cloud"
        assert out.get("WordPress") == "web"


# ---------------------------------------------------------------------------
# Analyzers
# ---------------------------------------------------------------------------

class TestExposureScore:
    def test_all_categories_present(self):
        out = compute_exposure([], [])
        assert set(out["categories"].keys()) == set(CATEGORIES)
        assert out["overall"] == 0

    def test_score_rises_with_findings(self):
        findings = [{"type": "login_portal"}, {"type": "api_surface"},
                    {"type": "email_security"}]
        entities = [{"entity_type": "email"}, {"entity_type": "email"},
                    {"entity_type": "domain"}]
        out = compute_exposure(findings, entities)
        assert out["overall"] > 0
        assert out["categories"]["technical_surface_exposure"]["score"] > 0
        # explanation present
        assert "raised_by" in out["categories"]["email_exposure"]

    def test_score_clamped(self):
        entities = [{"entity_type": "email"}] * 1000
        out = compute_exposure([], entities)
        assert out["categories"]["email_exposure"]["score"] <= 100


class TestRiskEngine:
    def test_login_hypothesis(self):
        findings = [{"type": "login_portal", "value": "https://acme.com/login"}]
        hyps = generate_hypotheses(findings, [])
        keys = {h.key for h in hyps}
        assert "exposed_login_portals" in keys

    def test_email_pattern_hypothesis(self):
        entities = [{"entity_type": "email", "value": f"u{i}@acme.com"} for i in range(4)]
        hyps = generate_hypotheses([], entities)
        assert "email_pattern_exposure" in {h.key for h in hyps}

    def test_no_hypotheses_when_empty(self):
        assert generate_hypotheses([], []) == []


class TestGraph:
    def test_build(self):
        entities = [{"entity_type": "domain", "value": "acme.com", "normalized_value": "acme.com"}]
        rels = [{"source_value": "acme.com", "target_value": "mail.acme.com",
                 "relationship_type": "related_to_domain", "confidence": "high"}]
        g = build_graph(entities, rels)
        assert g["counts"]["edges"] == 1
        assert any(n["id"] == "acme.com" for n in g["nodes"])


# ---------------------------------------------------------------------------
# Exporters
# ---------------------------------------------------------------------------

class TestExporters:
    def _analysis(self):
        return {"target_company_name": "ACME", "target_root_domain": "acme.com",
                "status": "completed", "depth": "standard",
                "summary_json": {"executive_summary": "test", "kpis": {"total_findings": 1}},
                "exposure_score_json": {"overall": 42, "categories": {}}}

    def test_markdown(self):
        md = export_markdown(self._analysis(), [{"title": "F", "type": "t", "risk_level": "low",
                             "confidence": "high", "source": "dns"}], [], [], [])
        assert "# Intelligence Report — ACME" in md
        assert "42/100" in md

    def test_json(self):
        out = export_json(self._analysis(), [], [], [], [], [], [])
        assert out["analysis"]["target_company_name"] == "ACME"
        assert "exposure_score" in out


# ---------------------------------------------------------------------------
# Orchestrator — mocked collectors, failure isolation
# ---------------------------------------------------------------------------

from app.modules.intel_osint.collectors.base import (
    Collector, CollectorContext, CollectorResult, RawEntity, RawFinding, RawRelationship,
)
from app.modules.intel_osint.orchestrator import IntelOrchestrator


class _GoodCollector(Collector):
    name = "good"

    async def collect(self, ctx: CollectorContext) -> CollectorResult:
        return CollectorResult(
            collector=self.name, status="completed",
            findings=[RawFinding(type="login_portal", title="login",
                                 value="https://acme.com/login", risk_level="medium")],
            entities=[RawEntity(entity_type="domain", value="acme.com",
                                normalized_value="acme.com", confidence="high"),
                      RawEntity(entity_type="domain", value="ACME.com",  # dup → dedup
                                normalized_value="acme.com", confidence="medium")],
            relationships=[RawRelationship(source_value="acme.com", target_value="mail.acme.com",
                                           relationship_type="related_to_domain")])


class _CrashingCollector(Collector):
    name = "boom"

    async def collect(self, ctx: CollectorContext) -> CollectorResult:
        raise RuntimeError("kaboom")


class _SkippedCollector(Collector):
    name = "skip"

    async def collect(self, ctx: CollectorContext) -> CollectorResult:
        return self.skipped("no api key")


@pytest.mark.asyncio
class TestOrchestrator:
    async def _run(self, collectors):
        orch = IntelOrchestrator(collectors)
        return await orch.run(company_name="ACME", root_domain="acme.com", country="ES",
                              nif=None, aliases=[], depth="standard", flags={})

    async def test_dedup_entities(self):
        out = await self._run([_GoodCollector()])
        domains = [e for e in out.entities if e["entity_type"] == "domain"]
        assert len(domains) == 1  # deduped
        assert domains[0]["confidence"] == "high"  # merged keeps highest

    async def test_crash_does_not_break_analysis(self):
        out = await self._run([_GoodCollector(), _CrashingCollector()])
        # analysis still produced results
        assert any(e["entity_type"] == "domain" for e in out.entities)
        # crash recorded as warning + failed collector status
        assert any(w["level"] == "error" for w in out.warnings)
        assert any(c["collector"] == "boom" and c["status"] == "failed" for c in out.collectors)

    async def test_skipped_collector_is_warning_not_fatal(self):
        out = await self._run([_GoodCollector(), _SkippedCollector()])
        assert any(c["status"] == "skipped" for c in out.collectors)
        assert out.status in ("partial", "completed")

    async def test_produces_risks_and_exposure(self):
        out = await self._run([_GoodCollector()])
        assert out.exposure["overall"] >= 0
        assert any(r["key"] == "exposed_login_portals" for r in out.risks)
        assert out.summary["kpis"]["total_findings"] >= 1

    async def test_all_failed_is_failed_status(self):
        out = await self._run([_CrashingCollector()])
        assert out.status == "failed"

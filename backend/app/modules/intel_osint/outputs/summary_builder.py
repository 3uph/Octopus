"""Build executive summary + KPI metrics from analysis data. Pure."""
from __future__ import annotations

from collections import Counter
from typing import Any


def build_summary(
    company: str, domain: str | None,
    findings: list[dict], entities: list[dict],
    risks: list[dict], warnings: list[dict], exposure: dict,
) -> dict[str, Any]:
    by_etype = Counter(e.get("entity_type") for e in entities)
    by_risk = Counter(f.get("risk_level") for f in findings)
    risk_by_level = Counter(r.get("risk_level") for r in risks)

    kpis = {
        "total_findings": len(findings),
        "domains": by_etype.get("domain", 0) + by_etype.get("subdomain", 0),
        "emails": by_etype.get("email", 0),
        "people": by_etype.get("person", 0) + by_etype.get("role", 0),
        "documents": by_etype.get("document", 0),
        "repositories": by_etype.get("repository", 0),
        "technologies": by_etype.get("technology", 0),
        "login_portals": by_etype.get("login_portal", 0),
        "public_records": by_etype.get("public_record", 0),
        "third_parties": by_etype.get("third_party", 0),
        "risk_hypotheses": len(risks),
        "warnings": len(warnings),
    }

    high = risk_by_level.get("high", 0) + by_risk.get("high", 0)
    overall = exposure.get("overall", 0)
    posture = ("high exposure" if overall >= 66 else
               "moderate exposure" if overall >= 33 else "low exposure")
    executive = (
        f"Public intelligence analysis of {company}"
        + (f" ({domain})" if domain else "")
        + f". Overall exposure score {overall}/100 — {posture}. "
        f"{kpis['total_findings']} findings, {kpis['domains']} domains/subdomains, "
        f"{kpis['emails']} emails, {kpis['technologies']} technologies, "
        f"{len(risks)} risk hypotheses ({high} high-severity signals). "
        f"{len(warnings)} collector warning(s)."
    )

    return {
        "executive_summary": executive,
        "kpis": kpis,
        "findings_by_risk": dict(by_risk),
        "risk_by_level": dict(risk_by_level),
        "entities_by_type": dict(by_etype),
    }

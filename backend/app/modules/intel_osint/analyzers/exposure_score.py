"""Exposure scoring — deterministic, category-based, explainable.

Each category 0-100 (higher = more public exposure / attack surface).
Every score carries an explanation: what raised it, what's missing, confidence.
Pure function over normalized findings/entities.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

CATEGORIES = [
    "corporate_identity_exposure",
    "legal_public_records_exposure",
    "technical_surface_exposure",
    "email_exposure",
    "employee_exposure",
    "document_exposure",
    "repository_exposure",
    "cloud_exposure",
    "third_party_exposure",
    "credential_exposure",
    "phishing_risk",
]


@dataclass
class CategoryScore:
    score: int
    confidence: str
    raised_by: list[str] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)


def _count(items: list[dict], **match) -> int:
    n = 0
    for it in items:
        if all(it.get(k) == v for k, v in match.items()):
            n += 1
    return n


def _clamp(v: int) -> int:
    return max(0, min(100, v))


def compute_exposure(findings: list[dict], entities: list[dict]) -> dict[str, Any]:
    """Return {overall, categories:{cat: {...}}}. Inputs are dict rows."""
    def etypes(t: str) -> int:
        return _count(entities, entity_type=t)

    def ftype(t: str) -> int:
        return _count(findings, type=t)

    cats: dict[str, CategoryScore] = {}

    # corporate identity
    brands = etypes("brand") + etypes("organization") + etypes("legal_entity")
    domains = etypes("domain") + etypes("subdomain")
    cats["corporate_identity_exposure"] = CategoryScore(
        _clamp(min(60, domains * 3) + min(40, brands * 10)),
        "high" if domains else "low",
        raised_by=[f"{domains} domains/subdomains", f"{brands} brand/legal entities"],
        missing=[] if brands else ["legal entity / brand mapping"])

    # legal/public records
    pr = ftype("public_record") + etypes("public_record") + etypes("contract") + etypes("subsidy")
    cats["legal_public_records_exposure"] = CategoryScore(
        _clamp(min(100, pr * 12)), "medium" if pr else "low",
        raised_by=[f"{pr} public records"], missing=["Spanish public records integration"] if not pr else [])

    # technical surface
    apis = ftype("api_surface")
    logins = ftype("login_portal")
    techs = etypes("technology")
    sech = ftype("security_header")
    cats["technical_surface_exposure"] = CategoryScore(
        _clamp(min(40, apis * 15) + min(30, logins * 10) + min(20, techs * 2) + min(20, sech * 3)),
        "high" if (apis or logins or techs) else "low",
        raised_by=[f"{apis} API surfaces", f"{logins} login portals", f"{techs} technologies",
                   f"{sech} missing security headers"],
        missing=[])

    # email
    emails = etypes("email")
    email_sec = ftype("email_security")
    cats["email_exposure"] = CategoryScore(
        _clamp(min(70, emails * 6) + min(30, email_sec * 15)),
        "high" if emails else "medium",
        raised_by=[f"{emails} public emails", f"{email_sec} email-security weaknesses"],
        missing=[])

    # employee
    people = etypes("person") + etypes("role")
    cats["employee_exposure"] = CategoryScore(
        _clamp(min(100, people * 8)), "medium" if people else "low",
        raised_by=[f"{people} people/roles"],
        missing=["people enumeration source (search/social)"] if not people else [])

    # document
    docs = etypes("document") + ftype("document_metadata")
    cats["document_exposure"] = CategoryScore(
        _clamp(min(100, docs * 8)), "high" if docs else "low",
        raised_by=[f"{docs} public documents"], missing=[])

    # repository
    repos = etypes("repository")
    secrets = ftype("potential_secret")
    cats["repository_exposure"] = CategoryScore(
        _clamp(min(60, repos * 12) + min(40, secrets * 20)),
        "medium" if repos else "low",
        raised_by=[f"{repos} repos", f"{secrets} potential secrets"],
        missing=["GITHUB_TOKEN for deep repo search"] if not repos else [])

    # cloud
    cloud = etypes("cloud_asset") + _count(entities, entity_type="technology")
    cloud_tags = sum(1 for e in entities if e.get("entity_type") == "technology"
                     and any(t in (e.get("tags") or []) for t in ("cloud", "saas")))
    cats["cloud_exposure"] = CategoryScore(
        _clamp(min(100, cloud_tags * 12)), "medium" if cloud_tags else "low",
        raised_by=[f"{cloud_tags} cloud/SaaS signals"], missing=[])

    # third party
    tp = etypes("third_party")
    cats["third_party_exposure"] = CategoryScore(
        _clamp(min(100, tp * 6)), "low" if tp else "low",
        raised_by=[f"{tp} third parties linked"], missing=[])

    # credential
    cred = ftype("potential_secret") + ftype("credential_exposure")
    cats["credential_exposure"] = CategoryScore(
        _clamp(min(100, cred * 25)), "low" if not cred else "medium",
        raised_by=[f"{cred} credential candidates"],
        missing=["authorized leak API"] )

    # phishing risk (composite)
    phish = min(40, emails * 4) + (20 if email_sec else 0) + min(20, logins * 10) + min(20, people * 4)
    cats["phishing_risk"] = CategoryScore(
        _clamp(phish), "medium",
        raised_by=["email + login + people exposure feed phishing pretext"],
        missing=[])

    overall = _clamp(int(sum(c.score for c in cats.values()) / len(cats)))
    return {
        "overall": overall,
        "categories": {
            k: {"score": v.score, "confidence": v.confidence,
                "raised_by": v.raised_by, "missing": v.missing}
            for k, v in cats.items()
        },
    }

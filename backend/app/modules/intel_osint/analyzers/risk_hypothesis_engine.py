"""Risk hypothesis engine — deterministic rules over findings/entities.

Generates explainable hypotheses (why it matters, how to validate, how to
remediate). Pure function. No network, no AI.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Hypothesis:
    key: str
    title: str
    description: str
    risk_level: str
    confidence: str
    evidence_summary: str
    why_it_matters: str
    recommended_validation: str
    recommended_remediation: str
    tags: list[str] = field(default_factory=list)
    related_findings: list[str] = field(default_factory=list)


def _f(findings: list[dict], **m) -> list[dict]:
    return [x for x in findings if all(x.get(k) == v for k, v in m.items())]


def _e(entities: list[dict], etype: str) -> list[dict]:
    return [x for x in entities if x.get("entity_type") == etype]


def generate_hypotheses(findings: list[dict], entities: list[dict]) -> list[Hypothesis]:
    out: list[Hypothesis] = []

    logins = _f(findings, type="login_portal")
    if logins:
        out.append(Hypothesis(
            key="exposed_login_portals",
            title=f"{len(logins)} login portal(s) exposed on public surface",
            description="Public authentication endpoints were discovered.",
            risk_level="medium", confidence="medium",
            evidence_summary=", ".join(f.get("value") or "" for f in logins[:5]),
            why_it_matters="Login portals are primary targets for credential stuffing and phishing.",
            recommended_validation="Confirm MFA and rate limiting on each portal.",
            recommended_remediation="Enforce MFA, geo/IP restrictions, and lockout policies.",
            tags=["auth", "phishing"], related_findings=[f.get("value") or "" for f in logins]))

    apis = _f(findings, type="api_surface")
    if apis:
        swagger = [a for a in apis if "swagger" in (a.get("value") or "").lower()
                   or "openapi" in (a.get("value") or "").lower()]
        graphql = [a for a in apis if "graphql" in (a.get("value") or "").lower()]
        out.append(Hypothesis(
            key="exposed_api_surface",
            title=f"{len(apis)} API surface endpoint(s) discovered",
            description="Public API endpoints/specs discovered via safe well-known paths.",
            risk_level="medium", confidence="medium",
            evidence_summary=", ".join(a.get("value") or "" for a in apis[:5]),
            why_it_matters="Exposed API specs reveal attack surface and data models.",
            recommended_validation="Review auth on each endpoint; check if specs should be public.",
            recommended_remediation="Restrict spec exposure; require auth; apply rate limits.",
            tags=["api"] + (["swagger"] if swagger else []) + (["graphql"] if graphql else [])))
        if swagger:
            out.append(Hypothesis(
                key="swagger_or_openapi_exposure", title="Swagger/OpenAPI spec exposed",
                description="An API specification document is publicly reachable.",
                risk_level="medium", confidence="high",
                evidence_summary=swagger[0].get("value") or "",
                why_it_matters="Full API contract disclosure aids targeted attacks.",
                recommended_validation="Confirm whether public spec exposure is intended.",
                recommended_remediation="Gate spec behind auth or remove from production.",
                tags=["api", "swagger"]))
        if graphql:
            out.append(Hypothesis(
                key="graphql_exposure", title="GraphQL endpoint exposed",
                description="A GraphQL endpoint is publicly reachable.",
                risk_level="medium", confidence="high",
                evidence_summary=graphql[0].get("value") or "",
                why_it_matters="Introspection can disclose the full schema.",
                recommended_validation="Test if introspection is enabled.",
                recommended_remediation="Disable introspection in production; require auth.",
                tags=["api", "graphql"]))

    email_sec = _f(findings, type="email_security")
    dmarc_missing = [f for f in email_sec if "dmarc" in (f.get("title") or "").lower()]
    if email_sec:
        out.append(Hypothesis(
            key="weak_email_security_posture",
            title="Weak email security posture (SPF/DMARC)",
            description="SPF/DMARC issues detected via DNS.",
            risk_level="medium", confidence="high",
            evidence_summary="; ".join(f.get("title") or "" for f in email_sec),
            why_it_matters="Weak SPF/DMARC enables email spoofing and phishing of the brand.",
            recommended_validation="Review SPF/DMARC/DKIM alignment.",
            recommended_remediation="Publish strict DMARC (p=reject) after monitoring.",
            tags=["email", "phishing"]))
        if dmarc_missing:
            out.append(Hypothesis(
                key="missing_or_weak_dmarc", title="Missing or weak DMARC",
                description="No enforcing DMARC record found.",
                risk_level="medium", confidence="high",
                evidence_summary="; ".join(f.get("title") or "" for f in dmarc_missing),
                why_it_matters="Without DMARC enforcement, brand impersonation is easier.",
                recommended_validation="Confirm DMARC at _dmarc.<domain>.",
                recommended_remediation="Deploy DMARC p=quarantine→reject.",
                tags=["email", "dmarc"]))

    docs = _f(findings, type="document_metadata") + _e(entities, "document")
    if docs:
        out.append(Hypothesis(
            key="public_documents_metadata",
            title=f"{len(docs)} public document(s) — possible metadata leakage",
            description="Public documents discovered; metadata may reveal authors/software/paths.",
            risk_level="low", confidence="medium",
            evidence_summary=", ".join((d.get("value") or "").split("/")[-1] for d in docs[:5]),
            why_it_matters="Document metadata leaks usernames, software versions and internal paths.",
            recommended_validation="Inspect metadata of each document.",
            recommended_remediation="Strip metadata before publishing documents.",
            tags=["document"]))

    emails = _e(entities, "email")
    if len(emails) >= 3:
        out.append(Hypothesis(
            key="email_pattern_exposure",
            title="Corporate email pattern inferable",
            description=f"{len(emails)} corporate emails exposed; address pattern can be inferred.",
            risk_level="medium", confidence="medium",
            evidence_summary=", ".join(e.get("value") or "" for e in emails[:5]),
            why_it_matters="Known email pattern enables targeted phishing of any employee.",
            recommended_validation="Confirm pattern; assess phishing awareness.",
            recommended_remediation="Phishing training; external email banners; MFA.",
            tags=["email", "phishing", "social_engineering"]))

    techs = _e(entities, "technology")
    cloud = [t for t in techs if any(x in (t.get("tags") or []) for x in ("cloud", "saas"))]
    if cloud:
        out.append(Hypothesis(
            key="cloud_provider_exposure",
            title="Cloud/SaaS providers inferable from public signals",
            description="Cloud/SaaS usage inferred from DNS/headers/HTML.",
            risk_level="low", confidence="medium",
            evidence_summary=", ".join(t.get("value") or "" for t in cloud[:8]),
            why_it_matters="Provider knowledge enables targeted supply-chain and tenant attacks.",
            recommended_validation="Confirm cloud tenancy and exposed admin surfaces.",
            recommended_remediation="Harden cloud tenant config; restrict admin endpoints.",
            tags=["cloud"]))

    repos = _e(entities, "repository")
    if repos:
        out.append(Hypothesis(
            key="repository_exposure",
            title=f"{len(repos)} public repository(ies) related to org",
            description="Public repos possibly related to the organization.",
            risk_level="low", confidence="low",
            evidence_summary=", ".join(r.get("value") or "" for r in repos[:5]),
            why_it_matters="Repos can leak secrets, internal hostnames and architecture.",
            recommended_validation="Review repos for secrets and internal references.",
            recommended_remediation="Secret scanning, branch protection, repo hygiene.",
            tags=["repository"]))

    secrets = _f(findings, type="potential_secret")
    if secrets:
        out.append(Hypothesis(
            key="potential_secret_exposure",
            title=f"{len(secrets)} potential secret(s) detected (masked)",
            description="Possible secrets detected in public sources (values masked).",
            risk_level="high", confidence="low",
            evidence_summary=f"{len(secrets)} masked candidates",
            why_it_matters="Leaked credentials can grant direct unauthorized access.",
            recommended_validation="Manually verify candidates; rotate if confirmed.",
            recommended_remediation="Rotate exposed secrets; enable secret scanning.",
            tags=["secret", "credential"]))

    tp = _e(entities, "third_party")
    if len(tp) >= 3:
        out.append(Hypothesis(
            key="third_party_exposure",
            title=f"{len(tp)} third parties linked from public surface",
            description="External parties linked from the org's public web.",
            risk_level="low", confidence="low",
            evidence_summary=", ".join(t.get("value") or "" for t in tp[:8]),
            why_it_matters="Third parties widen the supply-chain attack surface.",
            recommended_validation="Map data flows to each third party.",
            recommended_remediation="Vendor risk assessment; least-privilege integrations.",
            tags=["third_party", "supply_chain"]))

    domains = _e(entities, "domain") + _e(entities, "subdomain")
    if len(domains) >= 10:
        out.append(Hypothesis(
            key="domain_sprawl",
            title=f"Domain sprawl: {len(domains)} domains/subdomains",
            description="Large number of domains/subdomains observed.",
            risk_level="low", confidence="medium",
            evidence_summary=f"{len(domains)} domains/subdomains",
            why_it_matters="Sprawl increases unmanaged/forgotten asset risk (shadow IT).",
            recommended_validation="Inventory all assets; identify owners.",
            recommended_remediation="Decommission stale assets; central asset management.",
            tags=["asset_management", "possible_shadow_it"]))

    return out

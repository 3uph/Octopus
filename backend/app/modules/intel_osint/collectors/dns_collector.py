"""DNS + email-security posture collector (REAL via dnspython).

Resolves A/AAAA/MX/TXT/NS/CNAME, derives SPF/DMARC posture, infers providers.
Degrades gracefully if dnspython is unavailable.
"""
from __future__ import annotations

import asyncio

from app.modules.intel_osint.collectors.base import (
    Collector, CollectorContext, CollectorResult, RawEntity, RawFinding, RawRelationship,
)
from app.modules.intel_osint.extractors.technologies import detect_from_dns


class DNSCollector(Collector):
    name = "dns"

    def _resolve(self, domain: str) -> tuple[dict[str, list[str]], list[str]]:
        warnings: list[str] = []
        records: dict[str, list[str]] = {}
        try:
            import dns.resolver  # type: ignore
        except ImportError:
            warnings.append("dnspython not installed — DNS collection skipped")
            return records, warnings

        resolver = dns.resolver.Resolver()
        resolver.lifetime = 8.0
        resolver.timeout = 4.0

        def q(name: str, rtype: str) -> list[str]:
            try:
                ans = resolver.resolve(name, rtype)
                return [r.to_text().strip('"') for r in ans]
            except Exception:
                return []

        for rtype in ("A", "AAAA", "MX", "TXT", "NS", "CNAME"):
            vals = q(domain, rtype)
            if vals:
                records[rtype] = vals
        # DMARC at _dmarc.<domain>
        dmarc = q(f"_dmarc.{domain}", "TXT")
        if dmarc:
            records["DMARC"] = dmarc
        return records, warnings

    async def collect(self, ctx: CollectorContext) -> CollectorResult:
        res = CollectorResult(collector=self.name)
        if not ctx.root_domain:
            return self.skipped("no root domain provided")

        records, warnings = await asyncio.to_thread(self._resolve, ctx.root_domain)
        res.warnings.extend(warnings)
        if not records and warnings:
            res.status = "skipped"
            return res

        for rtype, vals in records.items():
            for v in vals:
                res.findings.append(RawFinding(
                    type="dns_record", title=f"{rtype} record",
                    value=v, source="dns", confidence="high", risk_level="info",
                    tags=[rtype], raw_context={"record_type": rtype, "domain": ctx.root_domain},
                ))

        # Email-security posture
        txt_blob = " ".join(records.get("TXT", []))
        has_spf = "v=spf1" in txt_blob.lower()
        has_dmarc = any("v=dmarc1" in d.lower() for d in records.get("DMARC", []))
        if not has_spf:
            res.findings.append(RawFinding(
                type="email_security", title="No SPF record found",
                source="dns", confidence="high", risk_level="medium",
                description="No v=spf1 TXT record — sender spoofing easier.", tags=["email", "spf"]))
        if not has_dmarc:
            res.findings.append(RawFinding(
                type="email_security", title="No DMARC record found",
                source="dns", confidence="high", risk_level="medium",
                description="No _dmarc TXT record — weak anti-spoofing posture.", tags=["email", "dmarc"]))
        elif any("p=none" in d.lower() for d in records.get("DMARC", [])):
            res.findings.append(RawFinding(
                type="email_security", title="DMARC policy is p=none",
                source="dns", confidence="high", risk_level="low",
                description="DMARC present but monitoring-only (p=none).", tags=["email", "dmarc"]))

        # Provider inference
        for tech, cat in detect_from_dns(records):
            res.findings.append(RawFinding(
                type="technology", title=f"Provider inferred: {tech}",
                value=tech, source="dns", confidence="medium", risk_level="info",
                tags=[cat, "inference"]))
            res.entities.append(RawEntity(entity_type="technology", value=tech,
                                          source="dns", confidence="medium", tags=[cat]))
            res.relationships.append(RawRelationship(
                source_value=ctx.root_domain, target_value=tech,
                relationship_type="uses_provider", confidence="medium", evidence="DNS records"))

        res.entities.append(RawEntity(entity_type="domain", value=ctx.root_domain,
                                      source="dns", confidence="high"))
        return res

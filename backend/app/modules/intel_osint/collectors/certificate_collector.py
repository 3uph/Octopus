"""Certificate Transparency collector (REAL via crt.sh).

Passive: queries the public CT log aggregator. Never touches the target.
Network fetcher is injectable for offline tests.
"""
from __future__ import annotations

from typing import Any, Awaitable, Callable

from app.modules.intel_osint.collectors.base import (
    Collector, CollectorContext, CollectorResult, RawEntity, RawRelationship,
)

FetchJson = Callable[[str, float, str], Awaitable[list[dict[str, Any]]]]


async def _default_fetch(url: str, timeout: float, ua: str) -> list[dict[str, Any]]:
    import httpx
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.get(url, headers={"User-Agent": ua})
        resp.raise_for_status()
        return resp.json()


class CertificateCollector(Collector):
    name = "certificate"

    def __init__(self, fetch_json: FetchJson | None = None) -> None:
        self._fetch = fetch_json or _default_fetch

    async def collect(self, ctx: CollectorContext) -> CollectorResult:
        res = CollectorResult(collector=self.name)
        if not ctx.root_domain:
            return self.skipped("no root domain provided")

        url = f"https://crt.sh/?q=%25.{ctx.root_domain}&output=json"
        try:
            rows = await self._fetch(url, float(ctx.config.http_timeout), ctx.config.user_agent)
        except Exception as exc:
            res.status = "partial"
            res.warnings.append(f"crt.sh unavailable: {type(exc).__name__}")
            return res

        subs: set[str] = set()
        for row in rows[: ctx.config.max_results_per_collector * 5]:
            for line in str(row.get("name_value", "")).splitlines():
                s = line.strip().lstrip("*.").lower()
                if s.endswith(ctx.root_domain.lower()):
                    subs.add(s)

        for sub in sorted(subs)[: ctx.config.max_results_per_collector]:
            etype = "domain" if sub == ctx.root_domain else "subdomain"
            res.entities.append(RawEntity(entity_type=etype, value=sub,
                                          source="certificate", confidence="high",
                                          tags=["certificate_transparency"]))
            if sub != ctx.root_domain:
                res.relationships.append(RawRelationship(
                    source_value=ctx.root_domain, target_value=sub,
                    relationship_type="related_to_domain", confidence="high",
                    evidence="Certificate Transparency"))
        res.message = f"{len(subs)} names from CT"
        return res

"""Degraded-mode collectors.

These have real interfaces and real adapter points, but require external
APIs/integrations not yet wired. They return status=skipped with a clear
warning instead of mock data. The orchestrator treats skipped as non-fatal.

This keeps the full collector surface present and the flow functional, while
being honest that the data source needs configuration/integration.
"""
from __future__ import annotations

from app.modules.intel_osint.collectors.base import Collector, CollectorContext, CollectorResult


class _DegradedBase(Collector):
    flag_key: str = ""
    reason: str = "collector requires external integration not yet configured"

    async def collect(self, ctx: CollectorContext) -> CollectorResult:
        if self.flag_key and not ctx.flags.get(self.flag_key, True):
            return self.skipped(f"{self.name} disabled by flag")
        return self.skipped(f"{self.name}: {self.reason}")


class SpanishPublicRecordsCollector(_DegradedBase):
    name = "spanish_public_records"
    flag_key = "include_public_records"
    reason = ("BORME/BOE/PLACSP/BDNS/OEPM adapters require integration; "
              "no public no-auth bulk API wired yet — skipped with warning")


class NewsCollector(_DegradedBase):
    name = "news"
    flag_key = "include_news"
    reason = "news/press collector requires a search/news API key (INTEL_SEARCH_PROVIDER=disabled)"


class SocialCollector(_DegradedBase):
    name = "social"
    flag_key = "include_social"
    reason = "social profile collector requires platform APIs/keys — skipped"


class LeakCollector(_DegradedBase):
    name = "leak"
    flag_key = "include_leaks"
    reason = ("authorized leak collector requires an authorized breach API key; "
              "never validates credentials or stores passwords")

    async def collect(self, ctx: CollectorContext) -> CollectorResult:
        # Hard gate: only ever runs when explicitly enabled.
        if not ctx.flags.get("include_leaks", False):
            return self.skipped("leaks disabled (include_leaks=false)")
        if not ctx.config.enable_leaks:
            return self.skipped("leaks disabled by config (INTEL_ENABLE_LEAKS=false)")
        return self.skipped("no authorized leak API configured — skipped (no credentials accessed)")


class SearchEngineCollector(_DegradedBase):
    name = "search_engine"
    reason = "search provider disabled (INTEL_SEARCH_PROVIDER=disabled)"

    async def collect(self, ctx: CollectorContext) -> CollectorResult:
        if ctx.config.search_provider == "disabled" or not ctx.config.search_api_key:
            return self.skipped("search engine disabled or no API key — skipped")
        return self.skipped("configured search provider adapter not implemented yet")

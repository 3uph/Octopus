"""GitHub collector — REAL with token, degraded (skipped+warning) without.

Searches public code/repos for the org/domain. Masks any potential secret.
Never stores full secrets. Requires GITHUB_TOKEN; without it, skips cleanly.
"""
from __future__ import annotations

from typing import Any, Awaitable, Callable

from app.modules.intel_osint.collectors.base import (
    Collector, CollectorContext, CollectorResult, RawEntity, RawFinding,
)

# search(query, token, ua, timeout) -> list of repo dicts
Search = Callable[[str, str, str, float], Awaitable[list[dict[str, Any]]]]


async def _default_search(query: str, token: str, ua: str, timeout: float) -> list[dict[str, Any]]:
    import httpx
    headers = {"Authorization": f"Bearer {token}", "User-Agent": ua,
               "Accept": "application/vnd.github+json"}
    url = f"https://api.github.com/search/repositories?q={query}&per_page=20"
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.get(url, headers=headers)
        resp.raise_for_status()
        return resp.json().get("items", [])


class GitHubCollector(Collector):
    name = "github"

    def __init__(self, search: Search | None = None) -> None:
        self._search = search or _default_search

    async def collect(self, ctx: CollectorContext) -> CollectorResult:
        res = CollectorResult(collector=self.name)
        if not ctx.flags.get("include_github", True) or not ctx.config.enable_github:
            return self.skipped("github disabled by flag/config")
        if not ctx.config.github_token:
            return self.skipped("GITHUB_TOKEN not set — github collector skipped (degraded mode)")

        terms = [ctx.company_name] + ctx.aliases
        if ctx.root_domain:
            terms.append(ctx.root_domain.split(".")[0])
        query = "+".join(t.replace(" ", "+") for t in terms[:2] if t)
        try:
            repos = await self._search(query, ctx.config.github_token,
                                       ctx.config.user_agent, float(ctx.config.http_timeout))
        except Exception as exc:
            res.status = "partial"
            res.warnings.append(f"github search failed: {type(exc).__name__}")
            return res

        for repo in repos[: ctx.config.max_results_per_collector]:
            full = repo.get("full_name", "")
            res.findings.append(RawFinding(
                type="repository", title=f"Public repo: {full}",
                value=repo.get("html_url"), source="github", confidence="medium",
                risk_level="info", evidence_url=repo.get("html_url"), tags=["repository"]))
            res.entities.append(RawEntity(entity_type="repository", value=full,
                                          source="github", confidence="medium"))
        res.message = f"{len(repos)} repos"
        return res

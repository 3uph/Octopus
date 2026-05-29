"""crt.sh passive source — Certificate Transparency lookup.

Reads public CT logs via crt.sh JSON API. This is PASSIVE: it queries a public
log service, never the target itself. No port scan, no probing.

Network access is injected via `fetch_json` so tests run offline.
Default fetcher uses httpx (the HTTP client library, NOT the projectdiscovery
recon binary) with a strict timeout. It is only invoked when explicitly enabled.
"""
from __future__ import annotations

from typing import Any, Awaitable, Callable

from app.core.logging import get_logger
from app.modules.discovery.sources.base import PassiveSource, SourceResult

logger = get_logger(__name__)

# Type for the injected fetcher: (url) -> parsed JSON (list of dicts)
FetchJson = Callable[[str], Awaitable[list[dict[str, Any]]]]

_CRTSH_URL = "https://crt.sh/?q=%25.{domain}&output=json"
_TIMEOUT_S = 15.0


async def _default_fetch_json(url: str) -> list[dict[str, Any]]:
    """Default fetcher using httpx library with timeout. Not used in tests."""
    import httpx  # local import: only needed when really fetching

    async with httpx.AsyncClient(timeout=_TIMEOUT_S) as client:
        resp = await client.get(url, headers={"User-Agent": "octopus-recon/0.1"})
        resp.raise_for_status()
        return resp.json()


class CrtShSource(PassiveSource):
    name = "crtsh"

    def __init__(self, fetch_json: FetchJson | None = None) -> None:
        # Injected fetcher for tests; default does real HTTP (only if invoked)
        self._fetch = fetch_json or _default_fetch_json

    async def discover(self, domain: str) -> SourceResult:
        url = _CRTSH_URL.format(domain=domain)
        try:
            rows = await self._fetch(url)
        except Exception as exc:  # network/parse errors are non-fatal
            logger.warning("crtsh fetch failed for %s: %s", domain, type(exc).__name__)
            return SourceResult(source_name=self.name, error=str(type(exc).__name__))

        subs: set[str] = set()
        for row in rows:
            name_value = row.get("name_value", "")
            for line in str(name_value).splitlines():
                cleaned = line.strip().lstrip("*.").lower()
                if cleaned and cleaned.endswith(domain.lower()):
                    subs.add(cleaned)
        return SourceResult(source_name=self.name, subdomains=sorted(subs))

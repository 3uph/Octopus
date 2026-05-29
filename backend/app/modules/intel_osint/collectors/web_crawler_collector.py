"""Safe web crawler collector (REAL via httpx).

Bounded, polite crawl of the root domain: robots/sitemap, safe well-known
paths, link extraction, tech/login/API detection, document discovery.
NO fuzzing, NO brute force. Page + depth limits + per-request timeout.
HTTP fetcher injectable for offline tests.
"""
from __future__ import annotations

from collections import deque
from typing import Awaitable, Callable
from urllib.parse import urljoin, urlparse

from app.modules.intel_osint.collectors.base import (
    Collector, CollectorContext, CollectorResult, RawEntity, RawFinding, RawRelationship,
)
from app.modules.intel_osint.extractors.emails import extract_emails
from app.modules.intel_osint.extractors.login_portals import (
    SAFE_PROBE_PATHS, is_api_surface, looks_like_login,
)
from app.modules.intel_osint.extractors.technologies import detect_technologies
from app.modules.intel_osint.extractors.urls import extract_links, is_document, is_internal

# fetch(url) -> (status_code, headers_dict, text_body)
Fetch = Callable[[str], Awaitable[tuple[int, dict[str, str], str]]]


def _make_default_fetch(timeout: float, ua: str) -> Fetch:
    async def _fetch(url: str) -> tuple[int, dict[str, str], str]:
        import httpx
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            resp = await client.get(url, headers={"User-Agent": ua})
            body = resp.text[:500_000]
            return resp.status_code, {k.lower(): v for k, v in resp.headers.items()}, body
    return _fetch


class WebCrawlerCollector(Collector):
    name = "web_crawler"

    def __init__(self, fetch: Fetch | None = None) -> None:
        self._fetch = fetch

    async def collect(self, ctx: CollectorContext) -> CollectorResult:
        res = CollectorResult(collector=self.name)
        if not ctx.root_domain:
            return self.skipped("no root domain provided")

        fetch = self._fetch or _make_default_fetch(float(ctx.config.http_timeout), ctx.config.user_agent)
        root = ctx.root_domain
        base = f"https://{root}"
        max_pages = ctx.config.max_crawl_pages
        max_depth = ctx.config.max_crawl_depth

        seen: set[str] = set()
        queue: deque[tuple[str, int]] = deque()
        queue.append((base, 0))
        for p in SAFE_PROBE_PATHS:
            queue.append((urljoin(base + "/", p.lstrip("/")), 1))

        alive = False
        techs: dict[str, str] = {}
        emails: set[str] = set()
        external_hosts: set[str] = set()
        documents: set[str] = set()
        pages_fetched = 0

        while queue and pages_fetched < max_pages:
            url, depth = queue.popleft()
            if url in seen or depth > max_depth:
                continue
            seen.add(url)
            try:
                status, headers, body = await fetch(url)
            except Exception:
                continue
            pages_fetched += 1
            path = urlparse(url).path or "/"

            if status < 500:
                alive = True
            if status >= 400:
                # record only meaningful well-known probes
                continue

            header_blob = " ".join(f"{k}: {v}" for k, v in headers.items())
            for tech, cat in detect_technologies(header_blob + " " + body[:20000]):
                techs[tech] = cat

            for e in extract_emails(body):
                emails.add(e)

            # security headers (report missing important ones on root)
            if path in ("/", ""):
                for h in ("strict-transport-security", "content-security-policy",
                          "x-frame-options", "x-content-type-options"):
                    if h not in headers:
                        res.findings.append(RawFinding(
                            type="security_header", title=f"Missing header: {h}",
                            source="web_crawler", confidence="high", risk_level="low",
                            evidence_url=url, tags=["headers"]))

            # login / api surface
            if looks_like_login(url, body):
                res.findings.append(RawFinding(
                    type="login_portal", title=f"Login portal: {path}",
                    value=url, source="web_crawler", confidence="medium",
                    risk_level="medium", evidence_url=url, tags=["login", "auth"]))
                res.entities.append(RawEntity(entity_type="login_portal", value=url,
                                              source="web_crawler", confidence="medium"))
                res.relationships.append(RawRelationship(
                    source_value=root, target_value=url,
                    relationship_type="exposes_login_portal", confidence="medium",
                    evidence="HTML form / login hints"))
            if is_api_surface(path) and status < 400:
                res.findings.append(RawFinding(
                    type="api_surface", title=f"API surface: {path}",
                    value=url, source="web_crawler", confidence="medium",
                    risk_level="medium", evidence_url=url, tags=["api"]))

            # links
            for link in extract_links(body, url):
                if is_document(link):
                    documents.add(link)
                    continue
                if is_internal(link, root):
                    if link not in seen and depth + 1 <= max_depth:
                        queue.append((link, depth + 1))
                else:
                    h = urlparse(link).hostname or ""
                    if h:
                        external_hosts.add(h.lower())

        if not alive:
            res.status = "partial"
            res.warnings.append(f"{root} did not respond over HTTP/HTTPS")

        for tech, cat in techs.items():
            res.findings.append(RawFinding(type="technology", title=f"Technology: {tech}",
                                           value=tech, source="web_crawler", confidence="medium",
                                           risk_level="info", tags=[cat]))
            res.entities.append(RawEntity(entity_type="technology", value=tech,
                                          source="web_crawler", confidence="medium", tags=[cat]))
        for e in sorted(emails)[: ctx.config.max_results_per_collector]:
            res.entities.append(RawEntity(entity_type="email", value=e,
                                          source="web_crawler", confidence="high"))
        for d in sorted(documents)[: ctx.config.max_results_per_collector]:
            res.findings.append(RawFinding(type="document", title=f"Public document: {d.split('/')[-1]}",
                                           value=d, source="web_crawler", confidence="high",
                                           risk_level="info", evidence_url=d, tags=["document"]))
            res.entities.append(RawEntity(entity_type="document", value=d,
                                          source="web_crawler", confidence="high"))
        for h in sorted(external_hosts)[: ctx.config.max_results_per_collector]:
            res.entities.append(RawEntity(entity_type="third_party", value=h,
                                          source="web_crawler", confidence="low", tags=["external_link"]))
            res.relationships.append(RawRelationship(
                source_value=root, target_value=h, relationship_type="linked_from",
                confidence="low", evidence="external link"))

        res.message = f"{pages_fetched} pages crawled"
        return res

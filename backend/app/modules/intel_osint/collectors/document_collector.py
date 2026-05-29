"""Document metadata collector (REAL where libs available, degraded otherwise).

Takes document URLs discovered by the crawler, downloads within size/timeout
limits, and extracts metadata (author/creator/software/dates) + emails +
internal paths. PDF metadata uses pypdf if installed; otherwise degrades to
header-only metadata with a warning. Never executes document content.
"""
from __future__ import annotations

from typing import Awaitable, Callable

from app.modules.intel_osint.collectors.base import (
    Collector, CollectorContext, CollectorResult, RawEntity, RawFinding, RawRelationship,
)
from app.modules.intel_osint.extractors.emails import extract_emails

# fetch(url) -> (status, headers, content_bytes)
FetchBytes = Callable[[str], Awaitable[tuple[int, dict[str, str], bytes]]]


def _make_default_fetch(timeout: float, ua: str, max_bytes: int) -> FetchBytes:
    async def _fetch(url: str) -> tuple[int, dict[str, str], bytes]:
        import httpx
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            resp = await client.get(url, headers={"User-Agent": ua})
            return resp.status_code, {k.lower(): v for k, v in resp.headers.items()}, resp.content[:max_bytes]
    return _fetch


def _pdf_metadata(content: bytes) -> dict[str, str]:
    try:
        import io
        from pypdf import PdfReader  # type: ignore
        reader = PdfReader(io.BytesIO(content))
        meta = reader.metadata or {}
        out = {}
        for k, v in meta.items():
            if v:
                out[str(k).lstrip("/")] = str(v)
        return out
    except Exception:
        return {}


class DocumentCollector(Collector):
    name = "document"

    def __init__(self, document_urls: list[str] | None = None, fetch: FetchBytes | None = None) -> None:
        self._docs = document_urls or []
        self._fetch = fetch

    async def collect(self, ctx: CollectorContext) -> CollectorResult:
        res = CollectorResult(collector=self.name)
        if not ctx.flags.get("include_documents", True):
            return self.skipped("documents disabled by flag")
        if not ctx.config.enable_document_download:
            return self.skipped("document download disabled by config")
        if not self._docs:
            res.message = "no document URLs supplied by crawler"
            return res

        fetch = self._fetch or _make_default_fetch(
            float(ctx.config.http_timeout), ctx.config.user_agent, ctx.config.max_document_size_bytes)

        pypdf_ok = True
        try:
            import pypdf  # noqa: F401
        except ImportError:
            pypdf_ok = False
            res.warnings.append("pypdf not installed — PDF metadata extraction degraded")

        for url in self._docs[: ctx.config.max_results_per_collector]:
            try:
                status, headers, content = await fetch(url)
            except Exception as exc:
                res.warnings.append(f"document fetch failed ({type(exc).__name__}): {url}")
                res.status = "partial"
                continue
            if status >= 400:
                continue

            meta: dict[str, str] = {}
            if url.lower().endswith(".pdf") and pypdf_ok:
                meta = _pdf_metadata(content)

            text = content[:200_000].decode("latin-1", errors="ignore")
            emails = extract_emails(text)

            risk = "low"
            tags = ["document"]
            interesting = {k: meta[k] for k in ("Author", "Creator", "Producer") if k in meta}
            if interesting or emails:
                risk = "medium"
                tags.append("metadata_exposure")

            res.findings.append(RawFinding(
                type="document_metadata",
                title=f"Document metadata: {url.split('/')[-1]}",
                value=url, source="document", confidence="high", risk_level=risk,
                evidence_url=url, tags=tags,
                raw_context={"metadata": interesting, "emails": emails,
                             "content_type": headers.get("content-type"),
                             "size": headers.get("content-length")}))
            for e in emails:
                res.entities.append(RawEntity(entity_type="email", value=e,
                                              source="document", confidence="high"))
                res.relationships.append(RawRelationship(
                    source_value=url, target_value=e,
                    relationship_type="document_mentions", confidence="high",
                    evidence="email in document"))
        return res

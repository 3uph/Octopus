"""URL extraction + classification (internal/external, document). Pure."""
from __future__ import annotations

import re
from urllib.parse import urljoin, urlparse

_URL_RE = re.compile(r"https?://[^\s\"'<>)\]]+", re.IGNORECASE)
_HREF_RE = re.compile(r"""(?:href|src)\s*=\s*["']([^"']+)["']""", re.IGNORECASE)

DOC_EXTS = (".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".csv", ".txt")


def extract_urls(text: str) -> list[str]:
    return sorted(set(_URL_RE.findall(text or "")))


def extract_links(html: str, base_url: str) -> list[str]:
    """Resolve href/src links against base_url. Returns absolute http(s) URLs."""
    out = set()
    for ref in _HREF_RE.findall(html or ""):
        if ref.startswith(("mailto:", "tel:", "javascript:", "#", "data:")):
            continue
        absu = urljoin(base_url, ref)
        if absu.startswith(("http://", "https://")):
            out.add(absu.split("#")[0])
    return sorted(out)


def host_of(url: str) -> str:
    return (urlparse(url).hostname or "").lower()


def is_internal(url: str, root: str) -> bool:
    h = host_of(url)
    r = root.lower().lstrip("*.")
    return h == r or h.endswith("." + r)


def is_document(url: str) -> bool:
    path = urlparse(url).path.lower()
    return path.endswith(DOC_EXTS)

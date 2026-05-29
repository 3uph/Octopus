"""Domain extraction + relation to a root domain. Pure, no I/O."""
from __future__ import annotations

import re

_DOMAIN_RE = re.compile(
    r"\b(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}\b"
)
_TLD_OK = re.compile(r"[a-zA-Z]{2,}$")


def extract_domains(text: str) -> list[str]:
    out = set()
    for m in _DOMAIN_RE.findall(text or ""):
        d = m.lower().strip(".")
        # filter file-like matches (e.g. image.png) by rejecting known file ext last labels
        last = d.rsplit(".", 1)[-1]
        if last in ("png", "jpg", "jpeg", "gif", "svg", "css", "js", "ico", "woff", "ttf", "map"):
            continue
        out.add(d)
    return sorted(out)


def is_subdomain_of(candidate: str, root: str) -> bool:
    c, r = candidate.lower().rstrip("."), root.lower().lstrip("*.").rstrip(".")
    return c == r or c.endswith("." + r)


def related_domains(domains: list[str], root: str) -> list[str]:
    return sorted({d for d in domains if is_subdomain_of(d, root)})

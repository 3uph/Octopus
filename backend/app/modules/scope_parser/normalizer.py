"""Scope value normalization + classification (deterministic, no AI).

Classifies a raw token into a ScopeKind and produces a normalized form.
Anything unclear is marked OTHER and flagged for manual review by the caller.
"""
from __future__ import annotations

import ipaddress
import re
from urllib.parse import urlparse

from app.models.enums import ScopeKind

_DOMAIN_RE = re.compile(
    r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)"
    r"(?:\.(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?))+$"
)
_ASN_RE = re.compile(r"^AS\d+$", re.IGNORECASE)


def classify_and_normalize(raw: str) -> tuple[ScopeKind, str, bool]:
    """Return (kind, normalized_value, is_wildcard) for a raw scope token.

    Pure function: no I/O, no network. Unknown → (OTHER, stripped, False).
    """
    token = raw.strip()
    is_wildcard = False

    if not token:
        return ScopeKind.OTHER, "", False

    # URL?
    if token.lower().startswith(("http://", "https://")):
        parsed = urlparse(token)
        if parsed.netloc:
            return ScopeKind.URL, token.rstrip("/").lower(), False
        return ScopeKind.OTHER, token, False

    # ASN?
    if _ASN_RE.match(token):
        return ScopeKind.ASN, token.upper(), False

    # Wildcard domain?
    if token.startswith("*."):
        is_wildcard = True
        bare = token[2:].lower()
        if _DOMAIN_RE.match(bare):
            return ScopeKind.WILDCARD, "*." + bare, True
        return ScopeKind.OTHER, token, True

    # Mobile app hints
    low = token.lower()
    if low.endswith(".apk") or "play.google.com" in low or "apps.apple.com" in low:
        return ScopeKind.MOBILE_APP, token, False

    # CIDR?
    if "/" in token:
        try:
            net = ipaddress.ip_network(token, strict=False)
            return ScopeKind.CIDR, str(net), False
        except ValueError:
            pass

    # IP?
    try:
        ip = ipaddress.ip_address(token)
        return ScopeKind.IP, str(ip), False
    except ValueError:
        pass

    # Domain?
    if _DOMAIN_RE.match(low):
        return ScopeKind.DOMAIN, low, False

    return ScopeKind.OTHER, token, False

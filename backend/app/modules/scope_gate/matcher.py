"""Pure scope-matching logic (no DB, no I/O) — the heart of the Scope Gate.

Decision precedence (security-critical):
  1. Explicit out-of-scope match  -> OUT (hard block, never executable)
  2. Confirmed/auto in-scope match -> IN
  3. In-scope match needing review -> AMBIGUOUS
  4. No match                      -> OUT (default deny)

Subdomain/wildcard handling, case-folding, and IDN are handled here.
"""
from __future__ import annotations

import ipaddress
from dataclasses import dataclass

from app.models.enums import ScopeDecision


@dataclass(frozen=True)
class ScopeEntry:
    """A normalized scope entry used for matching."""
    normalized_value: str
    kind: str            # ScopeKind value
    is_wildcard: bool
    requires_review: bool = False


def _norm(value: str) -> str:
    return value.strip().lower().rstrip(".")


def _domain_matches(target: str, entry: ScopeEntry) -> bool:
    t = _norm(target)
    v = _norm(entry.normalized_value)
    if entry.is_wildcard or v.startswith("*."):
        base = v[2:] if v.startswith("*.") else v
        # wildcard covers any subdomain and the apex
        return t == base or t.endswith("." + base)
    return t == v


def _ip_matches(target: str, entry: ScopeEntry) -> bool:
    try:
        ip = ipaddress.ip_address(target.strip())
    except ValueError:
        return False
    v = entry.normalized_value.strip()
    if entry.kind == "cidr" or "/" in v:
        try:
            return ip in ipaddress.ip_network(v, strict=False)
        except ValueError:
            return False
    try:
        return ip == ipaddress.ip_address(v)
    except ValueError:
        return False


def _entry_matches(target: str, target_kind: str, entry: ScopeEntry) -> bool:
    if target_kind in ("domain", "wildcard", "url"):
        return _domain_matches(_host_of(target), entry)
    if target_kind in ("ip", "cidr"):
        return _ip_matches(target, entry)
    return False


def _host_of(target: str) -> str:
    """Extract host from a URL or return the domain as-is."""
    t = target.strip()
    if t.lower().startswith(("http://", "https://")):
        from urllib.parse import urlparse
        return urlparse(t).hostname or t
    return t


def decide(
    target: str,
    target_kind: str,
    in_scope: list[ScopeEntry],
    out_of_scope: list[ScopeEntry],
) -> ScopeDecision:
    """Return the scope decision for a target. Pure function."""
    # 1. Explicit out-of-scope wins — hard block
    for entry in out_of_scope:
        if _entry_matches(target, target_kind, entry):
            return ScopeDecision.OUT

    # 2/3. In-scope matches
    matched_review = False
    for entry in in_scope:
        if _entry_matches(target, target_kind, entry):
            if entry.requires_review:
                matched_review = True
            else:
                return ScopeDecision.IN

    if matched_review:
        return ScopeDecision.AMBIGUOUS

    # 4. Default deny
    return ScopeDecision.OUT

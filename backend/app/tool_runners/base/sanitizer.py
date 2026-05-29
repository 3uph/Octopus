"""Input sanitizer for ToolRunner targets.

Validates that target values match strict patterns for their type.
Any value that doesn't match is rejected — never passed to a subprocess.

No shell=True. No string concatenation. Args always as lists.
"""
from __future__ import annotations

import ipaddress
import re
from urllib.parse import urlparse

from .types import Target, TargetKind


class TargetSanitizationError(ValueError):
    """Raised when a target value fails sanitization."""


# Strict domain pattern: labels [a-zA-Z0-9-], no leading/trailing hyphens,
# no consecutive dots, no control chars, no shell metacharacters.
_DOMAIN_RE = re.compile(
    r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)"
    r"(?:\.(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?))*$"
)

# Characters that must never appear in any target (shell metacharacters)
_FORBIDDEN_CHARS_RE = re.compile(
    r"[;&|`$\(\)<>\\\n\r\t\x00-\x1f\x7f]"
)

# URL scheme allowlist
_ALLOWED_SCHEMES = {"http", "https"}


def _check_forbidden(value: str, context: str) -> None:
    """Reject any value containing shell metacharacters."""
    if _FORBIDDEN_CHARS_RE.search(value):
        raise TargetSanitizationError(
            f"Forbidden characters detected in {context}: {value!r}"
        )
    if len(value) > 2048:
        raise TargetSanitizationError(
            f"{context} exceeds maximum length (2048): len={len(value)}"
        )


def sanitize_domain(value: str) -> str:
    """Validate and return a clean domain name."""
    _check_forbidden(value, "domain")
    value = value.strip().lower()
    # Strip leading wildcard if present (wildcards are handled at scope level)
    bare = value.lstrip("*.")
    if not bare or not _DOMAIN_RE.fullmatch(bare):
        raise TargetSanitizationError(f"Invalid domain: {value!r}")
    return value


def sanitize_ip(value: str) -> str:
    """Validate and return a clean IP address (v4 or v6)."""
    _check_forbidden(value, "ip")
    value = value.strip()
    try:
        ipaddress.ip_address(value)
    except ValueError:
        raise TargetSanitizationError(f"Invalid IP address: {value!r}")
    return value


def sanitize_cidr(value: str) -> str:
    """Validate and return a clean CIDR range."""
    _check_forbidden(value, "cidr")
    value = value.strip()
    try:
        ipaddress.ip_network(value, strict=False)
    except ValueError:
        raise TargetSanitizationError(f"Invalid CIDR: {value!r}")
    return value


def sanitize_url(value: str) -> str:
    """Validate and return a clean URL (http/https only)."""
    _check_forbidden(value, "url")
    value = value.strip()
    try:
        parsed = urlparse(value)
    except Exception:
        raise TargetSanitizationError(f"Unparseable URL: {value!r}")
    if parsed.scheme not in _ALLOWED_SCHEMES:
        raise TargetSanitizationError(
            f"URL scheme not allowed: {parsed.scheme!r} (only http/https)"
        )
    if not parsed.netloc:
        raise TargetSanitizationError(f"URL has no host: {value!r}")
    return value


def sanitize_target(target: Target) -> Target:
    """Sanitize a target according to its kind. Returns cleaned Target."""
    dispatchers = {
        TargetKind.DOMAIN: sanitize_domain,
        TargetKind.IP: sanitize_ip,
        TargetKind.CIDR: sanitize_cidr,
        TargetKind.URL: sanitize_url,
    }
    fn = dispatchers[target.kind]
    clean_value = fn(target.value)
    return Target(value=clean_value, kind=target.kind)


def sanitize_targets(targets: list[Target]) -> list[Target]:
    """Sanitize a list of targets, raising on first failure."""
    return [sanitize_target(t) for t in targets]

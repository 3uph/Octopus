"""Redact sensitive values from strings before logging or external transmission."""
import re

# Patterns that indicate a sensitive key=value or bearer token
_PATTERNS: list[re.Pattern] = [
    # Authorization header value
    re.compile(r"(Authorization:\s*)(Bearer\s+\S+)", re.IGNORECASE),
    # Key=value pairs for common secret fields
    re.compile(
        r"((?:password|passwd|secret|token|api[_-]?key|auth|credential|private[_-]?key"
        r"|encryption[_-]?key|access[_-]?key|secret[_-]?key)\s*[=:]\s*)(\S+)",
        re.IGNORECASE,
    ),
    # Bearer tokens standalone
    re.compile(r"(Bearer\s+)([A-Za-z0-9\-._~+/]+=*)", re.IGNORECASE),
    # JWT-shaped strings (3 base64 segments separated by dots)
    re.compile(r"([A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,})"),
]

_REPLACEMENT = "[REDACTED]"


def redact(text: str) -> str:
    """Return text with sensitive values replaced by [REDACTED]."""
    for pattern in _PATTERNS:
        if pattern.groups == 1:
            # Full match replacement (e.g. JWT)
            text = pattern.sub(_REPLACEMENT, text)
        else:
            # Keep group 1 (key/label), replace group 2 (value)
            text = pattern.sub(lambda m: m.group(1) + _REPLACEMENT, text)
    return text

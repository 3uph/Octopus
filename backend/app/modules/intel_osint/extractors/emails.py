"""Email extraction + corporate email-pattern inference. Pure, no I/O."""
from __future__ import annotations

import re

_EMAIL_RE = re.compile(
    r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"
)
# Obvious noise to drop
_NOISE = ("example.com", "domain.com", "email.com", "sentry.io", "wixpress.com")


def extract_emails(text: str) -> list[str]:
    """Return unique, lowercased emails found in text (noise filtered)."""
    found = set()
    for m in _EMAIL_RE.findall(text or ""):
        e = m.lower()
        if any(e.endswith(n) for n in _NOISE):
            continue
        found.add(e)
    return sorted(found)


def emails_for_domain(emails: list[str], domain: str) -> list[str]:
    d = domain.lower().lstrip("*.")
    return [e for e in emails if e.split("@")[-1] == d or e.split("@")[-1].endswith("." + d)]


def infer_email_pattern(emails: list[str], domain: str) -> str | None:
    """Infer corporate email pattern (e.g. {first}.{last}@domain).

    Heuristic and conservative — returns None if no confident pattern.
    """
    locals_ = [e.split("@")[0] for e in emails_for_domain(emails, domain)]
    if not locals_:
        return None
    dotted = sum(1 for l in locals_ if "." in l)
    if dotted >= max(1, len(locals_) // 2):
        return f"{{first}}.{{last}}@{domain}"
    # single-token locals
    return f"{{first}}@{domain}"

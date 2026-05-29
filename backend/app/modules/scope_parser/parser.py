"""Deterministic scope parser (OCT-023).

Parses raw scope text (pasted from HackerOne/Bugcrowd/Intigriti or client docs)
into in-scope / out-of-scope candidates + rule hints.

NO AI. NO network. Conservative: anything unclear → review.
Nothing is assumed in-scope unless it cleanly classifies.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.models.enums import Confidence, ReviewStatus, ScopeKind
from app.modules.scope_parser.normalizer import classify_and_normalize

# Lines hinting out-of-scope context
_OOS_HINTS = re.compile(
    r"\b(out[\s\-]?of[\s\-]?scope|oos|excluded|do not test|not in scope|forbidden)\b",
    re.IGNORECASE,
)
# Lines hinting in-scope context
_IS_HINTS = re.compile(r"\b(in[\s\-]?scope|scope|targets?|assets?|domains?)\b", re.IGNORECASE)
# Rule hints
_RULE_HINTS = re.compile(
    r"\b(rate[\s\-]?limit|no automated|no automation|do not|prohibited|"
    r"social engineering|dos|ddos|denial of service|spam|brute[\s\-]?force)\b",
    re.IGNORECASE,
)


@dataclass
class ParsedScopeItem:
    raw_value: str
    normalized_value: str
    kind: ScopeKind
    is_wildcard: bool
    confidence: Confidence
    review_status: ReviewStatus
    source: str = "parser"


@dataclass
class ParsedRule:
    rule_type: str
    description_raw: str
    review_status: ReviewStatus = ReviewStatus.REQUIRES_REVIEW


@dataclass
class ParseResult:
    in_scope: list[ParsedScopeItem] = field(default_factory=list)
    out_of_scope: list[ParsedScopeItem] = field(default_factory=list)
    rules: list[ParsedRule] = field(default_factory=list)
    ambiguous: list[ParsedScopeItem] = field(default_factory=list)


def _make_item(token: str) -> ParsedScopeItem:
    kind, normalized, is_wildcard = classify_and_normalize(token)
    if kind == ScopeKind.OTHER:
        confidence = Confidence.LOW
        review = ReviewStatus.REQUIRES_REVIEW
    elif kind in (ScopeKind.DOMAIN, ScopeKind.WILDCARD, ScopeKind.URL):
        confidence = Confidence.HIGH
        review = ReviewStatus.AUTO
    else:
        confidence = Confidence.MEDIUM
        review = ReviewStatus.REQUIRES_REVIEW
    return ParsedScopeItem(
        raw_value=token.strip(),
        normalized_value=normalized,
        kind=kind,
        is_wildcard=is_wildcard,
        confidence=confidence,
        review_status=review,
    )


_TOKEN_SPLIT = re.compile(r"[\s,;]+")


def _extract_tokens(line: str) -> list[str]:
    # Strip common list markers (bullets/numbers) WITHOUT eating wildcard "*."
    # Markers: leading whitespace, "- ", "* " (bullet+space), "• ", "1. ", "1) "
    line = re.sub(r"^\s*(?:[-•]\s+|\*\s+|\d+[.)]\s+)", "", line)
    line = line.replace("`", "").strip()
    if not line:
        return []
    candidates = _TOKEN_SPLIT.split(line)
    # Keep only token-ish things (contain a dot or look like a host/asn)
    return [c for c in candidates if c and ("." in c or c.lower().startswith("as"))]


def parse_scope(raw_text: str) -> ParseResult:
    """Parse raw scope text into structured result. Deterministic."""
    result = ParseResult()
    current_section = "unknown"  # "in" | "out" | "unknown"

    for line in raw_text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue

        # Section detection
        if _OOS_HINTS.search(stripped):
            current_section = "out"
            # A header-only line still may carry a token; fall through to extract
        elif _IS_HINTS.search(stripped) and len(stripped) < 40:
            current_section = "in"

        # Rule detection (independent of tokens)
        if _RULE_HINTS.search(stripped):
            result.rules.append(
                ParsedRule(rule_type="restriction", description_raw=stripped)
            )

        tokens = _extract_tokens(stripped)
        for tok in tokens:
            item = _make_item(tok)
            if current_section == "out" or _OOS_HINTS.search(stripped):
                result.out_of_scope.append(item)
            elif item.kind == ScopeKind.OTHER:
                result.ambiguous.append(item)
            else:
                result.in_scope.append(item)

    return result

"""Shared enums reused across scope, assets, and intelligence."""
from __future__ import annotations

from enum import Enum as PyEnum


class Confidence(str, PyEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ReviewStatus(str, PyEnum):
    AUTO = "auto"
    REQUIRES_REVIEW = "requires_review"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"


class ScopeKind(str, PyEnum):
    DOMAIN = "domain"
    WILDCARD = "wildcard"
    URL = "url"
    IP = "ip"
    CIDR = "cidr"
    ASN = "asn"
    MOBILE_APP = "mobile_app"
    OTHER = "other"


class ScopeDecision(str, PyEnum):
    IN = "in"
    OUT = "out"
    AMBIGUOUS = "ambiguous"
    BLOCKED = "blocked"

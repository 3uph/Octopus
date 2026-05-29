"""Base collector contract + shared result container.

Collectors are PASSIVE: they read public data, never attack the target.
A collector must never raise out — it returns CollectorResult with status
and warnings. The orchestrator turns failures into partial+warning, never
a crashed analysis.
"""
from __future__ import annotations

import abc
from dataclasses import dataclass, field
from typing import Any

from app.modules.intel_osint.config import IntelConfig


@dataclass
class RawFinding:
    type: str
    title: str
    value: str | None = None
    description: str | None = None
    source: str | None = None
    evidence_url: str | None = None
    confidence: str = "medium"
    risk_level: str = "info"
    tags: list[str] = field(default_factory=list)
    raw_context: dict[str, Any] = field(default_factory=dict)


@dataclass
class RawEntity:
    entity_type: str
    value: str
    normalized_value: str | None = None
    confidence: str = "medium"
    source: str | None = None
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class RawRelationship:
    source_value: str
    target_value: str
    relationship_type: str
    confidence: str = "medium"
    evidence: str | None = None


@dataclass
class CollectorResult:
    collector: str
    status: str = "completed"  # completed | partial | skipped | failed
    findings: list[RawFinding] = field(default_factory=list)
    entities: list[RawEntity] = field(default_factory=list)
    relationships: list[RawRelationship] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    message: str | None = None


@dataclass
class CollectorContext:
    company_name: str
    root_domain: str | None
    country: str
    nif: str | None
    aliases: list[str]
    depth: str
    flags: dict[str, bool]
    config: IntelConfig


class Collector(abc.ABC):
    name: str

    @abc.abstractmethod
    async def collect(self, ctx: CollectorContext) -> CollectorResult:
        """Run the collector. Must not raise; return result with status."""

    def skipped(self, reason: str) -> CollectorResult:
        return CollectorResult(collector=self.name, status="skipped",
                               warnings=[reason], message=reason)

"""Passive source interface.

Passive sources read PUBLIC data about a domain (e.g. Certificate Transparency).
They never touch the target directly: no port scan, no fuzzing, no active probing.
Network access is injected (a fetch callable) so tests run fully offline.
"""
from __future__ import annotations

import abc
from dataclasses import dataclass, field


@dataclass
class SourceResult:
    source_name: str
    subdomains: list[str] = field(default_factory=list)
    error: str | None = None


class PassiveSource(abc.ABC):
    """Abstract passive discovery source."""

    name: str

    @abc.abstractmethod
    async def discover(self, domain: str) -> SourceResult:
        """Return subdomains discovered for the given domain. No active probing."""

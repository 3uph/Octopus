"""Shared types for the ToolRunner system."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class ReconMode(str, Enum):
    PASSIVE = "passive"
    MEDIUM = "medium"
    ACTIVE = "active"
    DRY_RUN = "dry_run"


class TargetKind(str, Enum):
    DOMAIN = "domain"
    IP = "ip"
    CIDR = "cidr"
    URL = "url"


@dataclass(frozen=True)
class Target:
    value: str
    kind: TargetKind


@dataclass
class ToolRunPlan:
    """Result of plan() — describes what would be executed without doing it."""
    tool_name: str
    targets: list[Target]
    args: list[str]          # Final argument list (no shell expansion ever)
    mode: ReconMode
    blocked_targets: list[Target] = field(default_factory=list)
    estimated_duration_s: int = 0
    dry_run_description: str = ""


@dataclass
class RawOutput:
    path: Path
    tool_name: str
    exit_code: int
    stdout_lines: int
    stderr_path: Path | None = None

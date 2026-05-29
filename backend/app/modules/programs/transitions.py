"""Program status transition rules.

Allowed transitions:
  planning -> active, closed
  active   -> paused, closed
  paused   -> active, closed
  closed   -> (terminal)
"""
from __future__ import annotations

from app.models.program import ProgramStatus

_ALLOWED: dict[ProgramStatus, set[ProgramStatus]] = {
    ProgramStatus.PLANNING: {ProgramStatus.ACTIVE, ProgramStatus.CLOSED},
    ProgramStatus.ACTIVE: {ProgramStatus.PAUSED, ProgramStatus.CLOSED},
    ProgramStatus.PAUSED: {ProgramStatus.ACTIVE, ProgramStatus.CLOSED},
    ProgramStatus.CLOSED: set(),
}


def is_valid_transition(current: ProgramStatus, target: ProgramStatus) -> bool:
    """Return True if moving current -> target is allowed (same-state is a no-op)."""
    if current == target:
        return True
    return target in _ALLOWED.get(current, set())

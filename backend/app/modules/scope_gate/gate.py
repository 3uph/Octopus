"""Scope Gate — DB-backed wrapper around the pure matcher.

Every recon target MUST pass through ScopeGate before any execution.
Out-of-scope = hard block. Unmatched = default deny. Ambiguous = manual review.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import ReviewStatus, ScopeDecision
from app.models.scope import OutOfScopeItem, ScopeItem
from app.modules.scope_gate.matcher import ScopeEntry, decide


@dataclass
class ScopeGateResult:
    target: str
    target_kind: str
    decision: ScopeDecision
    allowed: bool  # True only when decision == IN


class ScopeGate:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def _load_entries(
        self, program_id: uuid.UUID
    ) -> tuple[list[ScopeEntry], list[ScopeEntry]]:
        in_rows = (
            await self._db.execute(
                select(ScopeItem).where(ScopeItem.program_id == program_id)
            )
        ).scalars().all()
        out_rows = (
            await self._db.execute(
                select(OutOfScopeItem).where(OutOfScopeItem.program_id == program_id)
            )
        ).scalars().all()

        in_scope = [
            ScopeEntry(
                normalized_value=r.normalized_value,
                kind=r.kind.value,
                is_wildcard=r.is_wildcard,
                # Items still under review are not auto-allowed
                requires_review=r.review_status
                in (ReviewStatus.REQUIRES_REVIEW, ReviewStatus.REJECTED),
            )
            for r in in_rows
            # rejected items never grant access
            if r.review_status != ReviewStatus.REJECTED
        ]
        out_scope = [
            ScopeEntry(
                normalized_value=r.normalized_value,
                kind=r.kind.value,
                is_wildcard=r.is_wildcard,
            )
            for r in out_rows
        ]
        return in_scope, out_scope

    async def check(
        self, program_id: uuid.UUID, target: str, target_kind: str
    ) -> ScopeGateResult:
        in_scope, out_scope = await self._load_entries(program_id)
        decision = decide(target, target_kind, in_scope, out_scope)
        return ScopeGateResult(
            target=target,
            target_kind=target_kind,
            decision=decision,
            allowed=(decision == ScopeDecision.IN),
        )

    async def filter_allowed(
        self, program_id: uuid.UUID, targets: list[tuple[str, str]]
    ) -> tuple[list[ScopeGateResult], list[ScopeGateResult]]:
        """Split targets into (allowed, blocked) based on gate decisions."""
        in_scope, out_scope = await self._load_entries(program_id)
        allowed: list[ScopeGateResult] = []
        blocked: list[ScopeGateResult] = []
        for target, kind in targets:
            decision = decide(target, kind, in_scope, out_scope)
            res = ScopeGateResult(target, kind, decision, decision == ScopeDecision.IN)
            (allowed if res.allowed else blocked).append(res)
        return allowed, blocked

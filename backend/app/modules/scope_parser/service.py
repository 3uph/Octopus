"""Scope parsing service — persists parsed scope, builds summary, handles review.

OCT-023 (parse), OCT-024 (summary, deterministic), OCT-025 (manual review).
NO AI. NO Scope Gate execution here.
"""
from __future__ import annotations

import uuid

from fastapi import HTTPException
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import ReviewStatus
from app.models.scope import OutOfScopeItem, RateLimitRule, ScopeItem, ScopeRule
from app.modules.programs.service import ProgramService
from app.modules.scope_parser.parser import parse_scope
from app.schemas.scope_entities import ScopeSummary


class ScopeParserService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._programs = ProgramService(db)

    async def parse_and_store(
        self, company_id: uuid.UUID, program_id: uuid.UUID
    ) -> dict[str, int]:
        """Parse the program's raw scope into ScopeItems/OutOfScopeItems/Rules.

        Replaces previously parsed items (idempotent re-parse).
        """
        program = await self._programs.get_in_company_or_404(company_id, program_id)
        if not program.scope_raw:
            raise HTTPException(status_code=400, detail="Program has no raw scope to parse")

        # Clear prior parsed items for this program (re-parse is idempotent)
        for model in (ScopeItem, OutOfScopeItem, ScopeRule):
            await self._db.execute(delete(model).where(model.program_id == program_id))

        result = parse_scope(program.scope_raw)

        for item in result.in_scope + result.ambiguous:
            self._db.add(ScopeItem(
                program_id=program_id,
                raw_value=item.raw_value,
                normalized_value=item.normalized_value,
                kind=item.kind,
                is_wildcard=item.is_wildcard,
                confidence=item.confidence,
                review_status=item.review_status,
                source=item.source,
            ))
        for item in result.out_of_scope:
            self._db.add(OutOfScopeItem(
                program_id=program_id,
                raw_value=item.raw_value,
                normalized_value=item.normalized_value,
                kind=item.kind,
                is_wildcard=item.is_wildcard,
                source=item.source,
            ))
        for rule in result.rules:
            self._db.add(ScopeRule(
                program_id=program_id,
                rule_type=rule.rule_type,
                description_raw=rule.description_raw,
                review_status=rule.review_status,
            ))

        await self._db.flush()
        return {
            "in_scope": len(result.in_scope),
            "ambiguous": len(result.ambiguous),
            "out_of_scope": len(result.out_of_scope),
            "rules": len(result.rules),
        }

    async def get_summary(self, program_id: uuid.UUID) -> ScopeSummary:
        """Build a deterministic allowed/forbidden/ambiguous summary (OCT-024)."""
        items = (await self._db.execute(
            select(ScopeItem).where(ScopeItem.program_id == program_id)
        )).scalars().all()
        oos = (await self._db.execute(
            select(OutOfScopeItem).where(OutOfScopeItem.program_id == program_id)
        )).scalars().all()
        rules = (await self._db.execute(
            select(ScopeRule).where(ScopeRule.program_id == program_id)
        )).scalars().all()

        allowed, ambiguous, requires_review = [], [], []
        for it in items:
            if it.review_status == ReviewStatus.CONFIRMED or (
                it.review_status == ReviewStatus.AUTO and it.confidence.value == "high"
            ):
                allowed.append(it.normalized_value)
            elif it.review_status == ReviewStatus.REQUIRES_REVIEW:
                requires_review.append(it.normalized_value)
            elif it.review_status == ReviewStatus.REJECTED:
                continue
            else:
                ambiguous.append(it.normalized_value)

        forbidden = [o.normalized_value for o in oos]
        rule_summaries = [r.description_raw or r.rule_type for r in rules]

        return ScopeSummary(
            allowed=allowed,
            forbidden=forbidden,
            ambiguous=ambiguous,
            requires_review=requires_review,
            rules=rule_summaries,
            counts={
                "allowed": len(allowed),
                "forbidden": len(forbidden),
                "ambiguous": len(ambiguous),
                "requires_review": len(requires_review),
                "rules": len(rule_summaries),
            },
        )

    async def review_item(
        self, program_id: uuid.UUID, item_type: str, item_id: uuid.UUID, action: str
    ) -> None:
        """Confirm or reject a scope item under manual review (OCT-025)."""
        if action not in ("confirm", "reject"):
            raise HTTPException(status_code=400, detail="action must be confirm or reject")
        new_status = ReviewStatus.CONFIRMED if action == "confirm" else ReviewStatus.REJECTED

        model_map = {"scope_item": ScopeItem, "scope_rule": ScopeRule}
        model = model_map.get(item_type)
        if model is None:
            raise HTTPException(status_code=400, detail="invalid item_type")

        row = (await self._db.execute(
            select(model).where(model.id == item_id, model.program_id == program_id)
        )).scalar_one_or_none()
        if not row:
            raise HTTPException(status_code=404, detail="scope item not found")

        row.review_status = new_status
        await self._db.flush()

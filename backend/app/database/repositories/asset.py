"""Asset repository — create/dedup assets per program (tenant-scoped)."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.asset import Asset, AssetType
from app.models.enums import Confidence, ScopeDecision


class AssetRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_by_value(self, program_id: uuid.UUID, value: str) -> Asset | None:
        result = await self._db.execute(
            select(Asset).where(Asset.program_id == program_id, Asset.value == value)
        )
        return result.scalar_one_or_none()

    async def list(self, program_id: uuid.UUID, offset: int = 0, limit: int = 100) -> list[Asset]:
        result = await self._db.execute(
            select(Asset)
            .where(Asset.program_id == program_id)
            .order_by(Asset.score.desc(), Asset.last_seen.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def upsert(
        self,
        program_id: uuid.UUID,
        value: str,
        asset_type: AssetType,
        scope_decision: ScopeDecision,
        discovered_via: str,
        confidence: Confidence = Confidence.MEDIUM,
    ) -> tuple[Asset, bool]:
        """Insert or update asset by (program_id, value). Returns (asset, created)."""
        existing = await self.get_by_value(program_id, value)
        now = datetime.now(timezone.utc)
        if existing:
            existing.last_seen = now
            # Upgrade scope decision only if newly resolved to IN
            if scope_decision == ScopeDecision.IN:
                existing.scope_decision = ScopeDecision.IN
            await self._db.flush()
            return existing, False

        asset = Asset(
            program_id=program_id,
            value=value,
            asset_type=asset_type,
            scope_decision=scope_decision,
            discovered_via=discovered_via,
            confidence=confidence,
            first_seen=now,
            last_seen=now,
        )
        self._db.add(asset)
        await self._db.flush()
        return asset, True

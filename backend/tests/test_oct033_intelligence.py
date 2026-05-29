"""BLOCK C: corporate intelligence models + CRUD + RBAC (NO AI)."""
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest


class TestIntelModels:
    def test_models_importable(self):
        from app.models.intelligence import (
            CompanyIntelligenceProfile, Brand, Product, PublicPortal,
            TechnologySignal, ThirdPartyProvider, IntelligenceSource,
            IntelligenceFinding, IntelligenceReviewItem, Actionability, ProviderKind,
        )
        assert Brand.__tablename__ == "brands"
        assert IntelligenceFinding.__tablename__ == "intelligence_findings"

    def test_actionability_values(self):
        from app.models.intelligence import Actionability
        vals = {a.value for a in Actionability}
        assert "sensitive" in vals
        assert "possibly_out_of_scope" in vals
        assert "technical_actionable" in vals

    def test_finding_has_confidence_review_source(self):
        from app.models.intelligence import IntelligenceFinding
        cols = {c.name for c in IntelligenceFinding.__table__.columns}
        assert {"confidence", "review_status", "source_id", "actionability"} <= cols

    def test_finding_default_review_requires_review(self):
        from app.models.intelligence import IntelligenceFinding
        # default review_status should be requires_review (conservative)
        col = IntelligenceFinding.__table__.c["review_status"]
        assert col.default.arg.value == "requires_review"

    def test_migration_exists(self):
        from pathlib import Path
        p = Path(__file__).parent.parent / "app/database/migrations/versions/0008_intelligence.py"
        assert p.exists()


class TestIntelServiceLogic:
    @pytest.mark.asyncio
    async def test_add_entity_sets_company_id(self):
        from app.modules.intelligence.service import IntelligenceService
        from app.models.intelligence import Brand
        db = AsyncMock()
        added = []
        db.add = MagicMock(side_effect=lambda x: added.append(x))
        svc = IntelligenceService(db)
        svc._companies.get_or_404 = AsyncMock(return_value=MagicMock())
        cid = uuid.uuid4()
        await svc.add_entity(cid, Brand, {"name": "ACME Brand"})
        assert len(added) == 1
        assert added[0].company_id == cid
        assert added[0].name == "ACME Brand"

    @pytest.mark.asyncio
    async def test_list_unknown_entity_404(self):
        from fastapi import HTTPException
        from app.modules.intelligence.service import IntelligenceService
        svc = IntelligenceService(AsyncMock())
        svc._companies.get_or_404 = AsyncMock(return_value=MagicMock())
        with pytest.raises(HTTPException) as exc:
            await svc.list_entity(uuid.uuid4(), "nonexistent")
        assert exc.value.status_code == 404


class TestIntelRBAC:
    def setup_method(self):
        from fastapi.testclient import TestClient
        from app.main import app
        from app.database.session import get_db_session
        self.app = app
        async def fake_db():
            yield AsyncMock()
        app.dependency_overrides[get_db_session] = fake_db
        self.client = TestClient(app, raise_server_exceptions=False)

    def teardown_method(self):
        self.app.dependency_overrides.clear()

    def _token(self, role):
        from app.core.security.tokens import create_access_token
        return create_access_token(str(uuid.uuid4()), extra_claims={"role": role, "username": "u"})

    def test_create_brand_viewer_blocked(self):
        cid = uuid.uuid4()
        r = self.client.post(
            f"/companies/{cid}/intelligence/brands",
            json={"name": "Test"},
            headers={"Authorization": f"Bearer {self._token('viewer')}"},
        )
        assert r.status_code == 403

    def test_create_finding_unauthenticated_blocked(self):
        cid = uuid.uuid4()
        r = self.client.post(
            f"/companies/{cid}/intelligence/findings",
            json={"category": "tech", "title": "X"},
        )
        assert r.status_code in (401, 403)

    def test_intel_routes_registered(self):
        paths = {r.path for r in self.app.routes}
        assert any("intelligence/brands" in p for p in paths)
        assert any("intelligence/findings" in p for p in paths)
        assert any("intelligence/profile" in p for p in paths)

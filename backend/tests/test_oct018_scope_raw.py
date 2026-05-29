"""OCT-018: Scope raw persistence + ScopeChangeLog."""
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.main import app


def _token(role: str) -> str:
    from app.core.security.tokens import create_access_token
    return create_access_token(str(uuid.uuid4()), extra_claims={"role": role, "username": f"test{role}"})


def _fake_db():
    async def _gen():
        yield AsyncMock()
    return _gen


class TestScopeChangeLogModel:
    def test_model_importable(self):
        from app.models.scope_change_log import ScopeChangeLog
        assert ScopeChangeLog.__tablename__ == "scope_change_logs"

    def test_has_required_columns(self):
        from app.models.scope_change_log import ScopeChangeLog
        cols = {c.name for c in ScopeChangeLog.__table__.columns}
        assert {"id", "program_id", "changed_by", "change_type", "before", "after", "created_at"} <= cols

    def test_program_fk(self):
        from app.models.scope_change_log import ScopeChangeLog
        fks = {fk.column.table.name for fk in ScopeChangeLog.__table__.foreign_keys}
        assert "programs" in fks

    def test_before_after_jsonb(self):
        from app.models.scope_change_log import ScopeChangeLog
        from sqlalchemy.dialects.postgresql import JSONB
        assert isinstance(ScopeChangeLog.__table__.c["before"].type, JSONB)
        assert isinstance(ScopeChangeLog.__table__.c["after"].type, JSONB)

    def test_migration_exists(self):
        from pathlib import Path
        p = Path(__file__).parent.parent / "app" / "database" / "migrations" / "versions" / "0005_scope_change_log.py"
        assert p.exists()


class TestScopeSchemas:
    def test_scope_raw_update(self):
        from app.schemas.scope import ScopeRawUpdate
        s = ScopeRawUpdate(scope_raw="*.example.com\nout: admin.example.com")
        assert "example.com" in s.scope_raw


class TestScopeServiceLogic:
    @pytest.mark.asyncio
    async def test_update_creates_changelog_create_type(self):
        """First scope set → change_type='create', ScopeChangeLog added."""
        from app.modules.programs.scope_service import ScopeService
        from app.schemas.scope import ScopeRawUpdate

        db = AsyncMock()
        added = []
        db.add = MagicMock(side_effect=lambda x: added.append(x))

        svc = ScopeService(db)
        fake_program = MagicMock()
        fake_program.id = uuid.uuid4()
        fake_program.company_id = uuid.uuid4()
        fake_program.scope_raw = None  # no prior scope
        svc._programs.get_in_company_or_404 = AsyncMock(return_value=fake_program)

        await svc.update_scope_raw(
            fake_program.company_id, fake_program.id,
            ScopeRawUpdate(scope_raw="*.example.com"), uuid.uuid4(),
        )

        from app.models.scope_change_log import ScopeChangeLog
        logs = [a for a in added if isinstance(a, ScopeChangeLog)]
        assert len(logs) == 1
        assert logs[0].change_type == "create"
        assert logs[0].after == {"scope_raw": "*.example.com"}
        assert fake_program.scope_raw == "*.example.com"

    @pytest.mark.asyncio
    async def test_update_existing_is_update_type(self):
        from app.modules.programs.scope_service import ScopeService
        from app.schemas.scope import ScopeRawUpdate
        from app.models.scope_change_log import ScopeChangeLog

        db = AsyncMock()
        added = []
        db.add = MagicMock(side_effect=lambda x: added.append(x))

        svc = ScopeService(db)
        fake_program = MagicMock()
        fake_program.id = uuid.uuid4()
        fake_program.company_id = uuid.uuid4()
        fake_program.scope_raw = "old scope"
        svc._programs.get_in_company_or_404 = AsyncMock(return_value=fake_program)

        await svc.update_scope_raw(
            fake_program.company_id, fake_program.id,
            ScopeRawUpdate(scope_raw="new scope"), uuid.uuid4(),
        )

        logs = [a for a in added if isinstance(a, ScopeChangeLog)]
        assert logs[0].change_type == "update"
        assert logs[0].before == {"scope_raw": "old scope"}
        assert logs[0].after == {"scope_raw": "new scope"}


class TestScopeRBAC:
    def setup_method(self):
        self.client = TestClient(app, raise_server_exceptions=False)
        from app.database.session import get_db_session
        app.dependency_overrides[get_db_session] = _fake_db()

    def teardown_method(self):
        app.dependency_overrides.clear()

    def test_update_scope_viewer_blocked(self):
        cid, pid = uuid.uuid4(), uuid.uuid4()
        r = self.client.put(
            f"/companies/{cid}/programs/{pid}/scope/",
            json={"scope_raw": "*.example.com"},
            headers={"Authorization": f"Bearer {_token('viewer')}"},
        )
        assert r.status_code == status.HTTP_403_FORBIDDEN

    def test_update_scope_unauthenticated_blocked(self):
        cid, pid = uuid.uuid4(), uuid.uuid4()
        r = self.client.put(
            f"/companies/{cid}/programs/{pid}/scope/",
            json={"scope_raw": "*.example.com"},
        )
        assert r.status_code in (401, 403)

    def test_scope_routes_registered(self):
        paths = {r.path for r in app.routes}
        assert "/companies/{company_id}/programs/{program_id}/scope/" in paths
        assert "/companies/{company_id}/programs/{program_id}/scope/history" in paths

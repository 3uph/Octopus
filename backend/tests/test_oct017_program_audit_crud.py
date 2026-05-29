"""OCT-017: Program & Audit CRUD — routes, services, transitions, tenant isolation."""
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException, status
from fastapi.testclient import TestClient

from app.main import app
from app.models.program import ProgramStatus
from app.modules.programs.transitions import is_valid_transition


def _token(role: str) -> str:
    from app.core.security.tokens import create_access_token
    return create_access_token(str(uuid.uuid4()), extra_claims={"role": role, "username": f"test{role}"})


def _fake_db():
    async def _gen():
        yield AsyncMock()
    return _gen


# ---------------------------------------------------------------------------
# Transition rules (pure logic, no DB)
# ---------------------------------------------------------------------------

class TestTransitions:
    def test_planning_to_active_valid(self):
        assert is_valid_transition(ProgramStatus.PLANNING, ProgramStatus.ACTIVE)

    def test_active_to_paused_valid(self):
        assert is_valid_transition(ProgramStatus.ACTIVE, ProgramStatus.PAUSED)

    def test_paused_to_active_valid(self):
        assert is_valid_transition(ProgramStatus.PAUSED, ProgramStatus.ACTIVE)

    def test_any_to_closed_valid(self):
        assert is_valid_transition(ProgramStatus.ACTIVE, ProgramStatus.CLOSED)
        assert is_valid_transition(ProgramStatus.PLANNING, ProgramStatus.CLOSED)

    def test_closed_is_terminal(self):
        assert not is_valid_transition(ProgramStatus.CLOSED, ProgramStatus.ACTIVE)
        assert not is_valid_transition(ProgramStatus.CLOSED, ProgramStatus.PLANNING)

    def test_planning_to_paused_invalid(self):
        assert not is_valid_transition(ProgramStatus.PLANNING, ProgramStatus.PAUSED)

    def test_same_state_noop_allowed(self):
        assert is_valid_transition(ProgramStatus.ACTIVE, ProgramStatus.ACTIVE)


# ---------------------------------------------------------------------------
# Imports / structure
# ---------------------------------------------------------------------------

class TestStructure:
    def test_program_service_importable(self):
        from app.modules.programs.service import ProgramService, AuditService
        assert ProgramService is not None
        assert AuditService is not None

    def test_program_repository_importable(self):
        from app.database.repositories.program import ProgramRepository, AuditRepository
        assert ProgramRepository is not None
        assert AuditRepository is not None

    def test_routes_registered(self):
        paths = {r.path for r in app.routes}
        assert "/companies/{company_id}/programs/" in paths
        assert "/programs/{program_id}/audits/" in paths


# ---------------------------------------------------------------------------
# RBAC — viewer blocked from mutations
# ---------------------------------------------------------------------------

class TestProgramRBAC:
    def setup_method(self):
        self.client = TestClient(app, raise_server_exceptions=False)
        from app.database.session import get_db_session
        app.dependency_overrides[get_db_session] = _fake_db()

    def teardown_method(self):
        app.dependency_overrides.clear()

    def test_create_program_viewer_blocked(self):
        cid = uuid.uuid4()
        r = self.client.post(
            f"/companies/{cid}/programs/",
            json={"name": "BB", "program_type": "bug_bounty"},
            headers={"Authorization": f"Bearer {_token('viewer')}"},
        )
        assert r.status_code == status.HTTP_403_FORBIDDEN

    def test_create_program_unauthenticated_blocked(self):
        cid = uuid.uuid4()
        r = self.client.post(
            f"/companies/{cid}/programs/",
            json={"name": "BB", "program_type": "bug_bounty"},
        )
        assert r.status_code in (401, 403)

    def test_create_audit_viewer_blocked(self):
        pid = uuid.uuid4()
        r = self.client.post(
            f"/programs/{pid}/audits/",
            json={"title": "Round 1"},
            headers={"Authorization": f"Bearer {_token('viewer')}"},
        )
        assert r.status_code == status.HTTP_403_FORBIDDEN


# ---------------------------------------------------------------------------
# Service-level: tenant isolation + transition enforcement (mocked repo)
# ---------------------------------------------------------------------------

class TestProgramServiceLogic:
    @pytest.mark.asyncio
    async def test_get_in_company_rejects_wrong_tenant(self):
        from app.modules.programs.service import ProgramService
        svc = ProgramService(AsyncMock())

        fake_program = AsyncMock()
        fake_program.company_id = uuid.uuid4()  # different company
        svc._repo.get = AsyncMock(return_value=fake_program)

        with pytest.raises(HTTPException) as exc:
            await svc.get_in_company_or_404(uuid.uuid4(), uuid.uuid4())
        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_update_invalid_transition_raises_409(self):
        from app.modules.programs.service import ProgramService
        svc = ProgramService(AsyncMock())

        cid = uuid.uuid4()
        fake_program = AsyncMock()
        fake_program.company_id = cid
        fake_program.status = ProgramStatus.CLOSED  # terminal
        svc._repo.get = AsyncMock(return_value=fake_program)

        from app.schemas.program import ProgramUpdate
        with pytest.raises(HTTPException) as exc:
            await svc.update(cid, uuid.uuid4(), ProgramUpdate(status=ProgramStatus.ACTIVE))
        assert exc.value.status_code == status.HTTP_409_CONFLICT

    @pytest.mark.asyncio
    async def test_audit_get_rejects_wrong_program(self):
        from app.modules.programs.service import AuditService
        svc = AuditService(AsyncMock())

        fake_audit = AsyncMock()
        fake_audit.program_id = uuid.uuid4()  # different program
        svc._repo.get = AsyncMock(return_value=fake_audit)

        with pytest.raises(HTTPException) as exc:
            await svc.get_in_program_or_404(uuid.uuid4(), uuid.uuid4())
        assert exc.value.status_code == 404


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class TestSchemas:
    def test_program_create_valid(self):
        from app.schemas.program import ProgramCreate
        from app.models.program import ProgramType
        p = ProgramCreate(name="Test", program_type=ProgramType.BUG_BOUNTY)
        assert p.program_type == ProgramType.BUG_BOUNTY

    def test_audit_create_valid(self):
        from app.schemas.audit import AuditCreate
        a = AuditCreate(title="Round 1")
        assert a.status.value == "draft"

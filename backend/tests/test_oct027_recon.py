"""OCT-027/029 + BLOCK B: passive recon, dry-run, Scope Gate enforcement, dedup."""
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.enums import ScopeDecision
from app.modules.discovery.sources.base import PassiveSource, SourceResult
from app.modules.discovery.sources.crtsh import CrtShSource


class _MockSource(PassiveSource):
    name = "mock"

    def __init__(self, subs: list[str]) -> None:
        self._subs = subs

    async def discover(self, domain: str) -> SourceResult:
        return SourceResult(source_name=self.name, subdomains=self._subs)


# ---------------------------------------------------------------------------
# Models / migrations
# ---------------------------------------------------------------------------

class TestModels:
    def test_asset_model(self):
        from app.models.asset import Asset, AssetType
        assert Asset.__tablename__ == "assets"

    def test_scan_models(self):
        from app.models.scan import ScanProfile, ScanJob, ToolRun
        assert ScanJob.__tablename__ == "scan_jobs"
        assert ToolRun.__tablename__ == "tool_runs"

    def test_migration_exists(self):
        from pathlib import Path
        p = Path(__file__).parent.parent / "app/database/migrations/versions/0007_assets_scan.py"
        assert p.exists()


# ---------------------------------------------------------------------------
# crt.sh source — offline (injected fetch), NO network
# ---------------------------------------------------------------------------

class TestCrtShSource:
    @pytest.mark.asyncio
    async def test_parses_subdomains_offline(self):
        async def fake_fetch(url):
            return [{"name_value": "api.example.com\n*.example.com"},
                    {"name_value": "www.example.com"}]
        src = CrtShSource(fetch_json=fake_fetch)
        res = await src.discover("example.com")
        assert "api.example.com" in res.subdomains
        assert "www.example.com" in res.subdomains
        # wildcard prefix stripped
        assert "example.com" in res.subdomains

    @pytest.mark.asyncio
    async def test_fetch_error_is_non_fatal(self):
        async def boom(url):
            raise RuntimeError("network down")
        src = CrtShSource(fetch_json=boom)
        res = await src.discover("example.com")
        assert res.error is not None
        assert res.subdomains == []


# ---------------------------------------------------------------------------
# DiscoveryService — dry-run + passive, Scope Gate enforced (mocked DB)
# ---------------------------------------------------------------------------

def _gate_returning(decision_map: dict):
    """Build a mock gate whose check() returns decisions from a map (default OUT)."""
    gate = MagicMock()

    async def _check(program_id, target, kind):
        from app.modules.scope_gate.gate import ScopeGateResult
        dec = decision_map.get(target, ScopeDecision.OUT)
        return ScopeGateResult(target, kind, dec, dec == ScopeDecision.IN)
    gate.check = AsyncMock(side_effect=_check)
    return gate


class TestDiscoveryDryRun:
    @pytest.mark.asyncio
    async def test_dry_run_splits_eligible_blocked(self):
        from app.modules.discovery.service import DiscoveryService
        svc = DiscoveryService(AsyncMock(), sources=[_MockSource([])])
        svc._programs.get_in_company_or_404 = AsyncMock(return_value=MagicMock())
        svc._gate = _gate_returning({"in.com": ScopeDecision.IN, "out.com": ScopeDecision.OUT})

        plan = await svc.plan(uuid.uuid4(), uuid.uuid4(), ["in.com", "out.com"])
        assert plan.eligible_targets == ["in.com"]
        assert len(plan.blocked_targets) == 1
        assert plan.blocked_targets[0]["target"] == "out.com"


class TestDiscoveryPassive:
    @pytest.mark.asyncio
    async def test_blocked_targets_raise_403(self):
        from fastapi import HTTPException
        from app.modules.discovery.service import DiscoveryService
        db = AsyncMock()
        svc = DiscoveryService(db, sources=[_MockSource(["sub.out.com"])])
        svc._programs.get_in_company_or_404 = AsyncMock(return_value=MagicMock())
        svc._gate = _gate_returning({"out.com": ScopeDecision.OUT})

        with pytest.raises(HTTPException) as exc:
            await svc.run_passive(uuid.uuid4(), uuid.uuid4(), ["out.com"], None)
        assert exc.value.status_code == 403

    @pytest.mark.asyncio
    async def test_passive_saves_assets_for_eligible(self):
        from app.modules.discovery.service import DiscoveryService
        db = AsyncMock()
        pid = uuid.uuid4()
        svc = DiscoveryService(db, sources=[_MockSource(["api.in.com", "www.in.com"])])
        svc._programs.get_in_company_or_404 = AsyncMock(return_value=MagicMock())
        # in.com is in scope; discovered subs also in scope
        svc._gate = _gate_returning({
            "in.com": ScopeDecision.IN,
            "api.in.com": ScopeDecision.IN,
            "www.in.com": ScopeDecision.IN,
        })
        # asset repo upsert returns (asset, created=True)
        svc._assets.upsert = AsyncMock(return_value=(MagicMock(), True))

        result = await svc.run_passive(uuid.uuid4(), pid, ["in.com"], None)
        assert result.assets_created == 2
        assert result.eligible_targets == ["in.com"]
        assert svc._assets.upsert.await_count == 2

    @pytest.mark.asyncio
    async def test_out_of_scope_subdomain_counted_not_in(self):
        from app.modules.discovery.service import DiscoveryService
        db = AsyncMock()
        svc = DiscoveryService(db, sources=[_MockSource(["leak.out-of-scope.com"])])
        svc._programs.get_in_company_or_404 = AsyncMock(return_value=MagicMock())
        svc._gate = _gate_returning({
            "in.com": ScopeDecision.IN,
            "leak.out-of-scope.com": ScopeDecision.OUT,  # discovered but OOS
        })
        captured = {}
        async def _upsert(**kwargs):
            captured["scope_decision"] = kwargs["scope_decision"]
            return (MagicMock(), True)
        svc._assets.upsert = AsyncMock(side_effect=_upsert)

        result = await svc.run_passive(uuid.uuid4(), uuid.uuid4(), ["in.com"], None)
        assert result.subdomains_out_of_scope == 1
        # asset persisted with OUT decision, not IN
        assert captured["scope_decision"] == ScopeDecision.OUT


# ---------------------------------------------------------------------------
# Recon routes — RBAC + active placeholder
# ---------------------------------------------------------------------------

class TestReconRoutes:
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

    def test_passive_run_viewer_blocked(self):
        cid, pid = uuid.uuid4(), uuid.uuid4()
        r = self.client.post(
            f"/companies/{cid}/programs/{pid}/recon/passive/run",
            json={"targets": ["example.com"]},
            headers={"Authorization": f"Bearer {self._token('viewer')}"},
        )
        assert r.status_code == 403

    def test_active_not_implemented(self):
        cid, pid = uuid.uuid4(), uuid.uuid4()
        r = self.client.post(
            f"/companies/{cid}/programs/{pid}/recon/active/run",
            headers={"Authorization": f"Bearer {self._token('operator')}"},
        )
        assert r.status_code == 501

    def test_routes_registered(self):
        paths = {r.path for r in self.app.routes}
        assert any("recon/passive/dry-run" in p for p in paths)
        assert any("recon/passive/run" in p for p in paths)
        assert any("/assets" in p for p in paths)
        assert any("scan-jobs" in p for p in paths)

"""OCT-016: Company CRUD routes — tests with mocked DB."""
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.main import app


def _make_company(name: str = "ACME Corp") -> MagicMock:
    c = MagicMock()
    c.id = uuid.uuid4()
    c.name_legal = name
    c.name_commercial = None
    c.description = None
    c.created_at = datetime.now(timezone.utc)
    return c


def _make_operator_token() -> str:
    from app.core.security.tokens import create_access_token
    return create_access_token(
        str(uuid.uuid4()),
        extra_claims={"role": "operator", "username": "testop"},
    )


def _make_viewer_token() -> str:
    from app.core.security.tokens import create_access_token
    return create_access_token(
        str(uuid.uuid4()),
        extra_claims={"role": "viewer", "username": "testviewer"},
    )


class TestCompanyRoutes:
    def setup_method(self):
        self.client = TestClient(app, raise_server_exceptions=False)

    def test_list_companies_requires_auth(self):
        from app.database.session import get_db_session
        async def fake_db():
            yield AsyncMock()
        app.dependency_overrides[get_db_session] = fake_db
        r = self.client.get("/companies/")
        app.dependency_overrides.clear()
        assert r.status_code in (401, 403)

    def test_create_company_requires_operator(self):
        """Viewer should be blocked from create."""
        viewer_token = _make_viewer_token()

        async def fake_db():
            yield AsyncMock()

        from app.database.session import get_db_session
        app.dependency_overrides[get_db_session] = fake_db

        r = self.client.post(
            "/companies/",
            json={"name_legal": "Test Corp"},
            headers={"Authorization": f"Bearer {viewer_token}"},
        )
        assert r.status_code == status.HTTP_403_FORBIDDEN
        app.dependency_overrides.clear()


class TestCompanyService:
    def test_service_importable(self):
        from app.modules.companies.service import CompanyService
        assert CompanyService is not None

    def test_repository_importable(self):
        from app.database.repositories.company import CompanyRepository
        assert CompanyRepository is not None


class TestCompanySchemas:
    def test_create_schema_valid(self):
        from app.schemas.company import CompanyCreate
        c = CompanyCreate(name_legal="BigCorp", description="desc")
        assert c.name_legal == "BigCorp"

    def test_read_schema_no_password(self):
        from app.schemas.company import CompanyRead
        fields = CompanyRead.model_fields.keys()
        assert "password" not in fields
        assert "password_hash" not in fields

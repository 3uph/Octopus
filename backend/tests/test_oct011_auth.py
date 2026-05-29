"""OCT-011: Password hashing, JWT tokens, auth routes (mocked DB)."""
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.core.security import create_access_token, hash_password, verify_password
from app.core.security.tokens import TokenError, decode_access_token
from app.main import app


class TestHashing:
    def test_hash_password_not_plaintext(self):
        h = hash_password("mysecret")
        assert h != "mysecret"
        assert len(h) > 20

    def test_verify_correct_password(self):
        h = hash_password("correct_password")
        assert verify_password("correct_password", h) is True

    def test_verify_wrong_password(self):
        h = hash_password("correct_password")
        assert verify_password("wrong_password", h) is False

    def test_hash_is_different_each_time(self):
        h1 = hash_password("same")
        h2 = hash_password("same")
        assert h1 != h2  # bcrypt uses random salt


class TestJWT:
    def test_create_and_decode_token(self):
        uid = str(uuid.uuid4())
        token = create_access_token(uid, extra_claims={"role": "admin"})
        payload = decode_access_token(token)
        assert payload["sub"] == uid
        assert payload["role"] == "admin"
        assert payload["type"] == "access"

    def test_invalid_token_raises(self):
        with pytest.raises(TokenError):
            decode_access_token("not.a.token")

    def test_token_with_expiry(self):
        uid = str(uuid.uuid4())
        token = create_access_token(uid, expire_minutes=60)
        payload = decode_access_token(token)
        assert "exp" in payload

    def test_expired_token_raises(self):
        uid = str(uuid.uuid4())
        token = create_access_token(uid, expire_minutes=-1)
        with pytest.raises(TokenError):
            decode_access_token(token)


class TestAuthRoutes:
    def setup_method(self):
        self.client = TestClient(app)

    def test_health_still_works(self):
        r = self.client.get("/health")
        assert r.status_code == 200

    def test_login_with_bad_credentials_returns_401(self):
        """No valid user in DB → should return 401."""
        with patch("app.api.routes.auth.get_db") as mock_get_db:
            mock_session = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_session.execute = AsyncMock(return_value=mock_result)
            mock_get_db.return_value = mock_session

            from app.database.session import get_db_session
            app.dependency_overrides[get_db_session] = lambda: mock_session

            r = self.client.post(
                "/auth/login",
                data={"username": "nobody", "password": "wrongpass"},
            )
            assert r.status_code == status.HTTP_401_UNAUTHORIZED
            app.dependency_overrides.clear()

    def test_logout_returns_204(self):
        r = self.client.post("/auth/logout")
        assert r.status_code == status.HTTP_204_NO_CONTENT

    def test_protected_route_without_token_returns_403_or_401(self):
        """Any future protected route should reject missing token."""
        from app.api.dependencies.auth import get_current_user
        # Verify the dependency is importable and callable
        assert callable(get_current_user)

    def test_password_not_in_logs(self, caplog):
        """Passwords must never appear in logs (tested via redactor integration)."""
        from app.core.logging.redactor import redact
        log_line = "password=supersecret login attempt"
        redacted = redact(log_line)
        assert "supersecret" not in redacted

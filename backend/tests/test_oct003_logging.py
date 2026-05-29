"""OCT-003: Verify config settings and logging redaction."""
import os

import pytest


class TestRedactor:
    def test_redacts_bearer_token(self):
        from app.core.logging.redactor import redact
        result = redact("Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.payload.sig")
        assert "eyJhbGciOiJIUzI1NiJ9" not in result
        assert "[REDACTED]" in result

    def test_redacts_password_field(self):
        from app.core.logging.redactor import redact
        result = redact("password=supersecret123")
        assert "supersecret123" not in result
        assert "[REDACTED]" in result

    def test_redacts_api_key_field(self):
        from app.core.logging.redactor import redact
        result = redact("api_key=sk-abc123xyz")
        assert "sk-abc123xyz" not in result
        assert "[REDACTED]" in result

    def test_redacts_secret_key_field(self):
        from app.core.logging.redactor import redact
        result = redact("secret_key=my_very_secret_value")
        assert "my_very_secret_value" not in result
        assert "[REDACTED]" in result

    def test_redacts_jwt_shaped_token(self):
        from app.core.logging.redactor import redact
        jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0In0.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
        result = redact(f"token={jwt}")
        assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in result

    def test_preserves_non_sensitive_text(self):
        from app.core.logging.redactor import redact
        text = "User created: user_id=123, email=test@example.com"
        result = redact(text)
        assert "user_id=123" in result
        assert "email=test@example.com" in result

    def test_empty_string(self):
        from app.core.logging.redactor import redact
        assert redact("") == ""


class TestSettings:
    def test_settings_import(self):
        from app.core.config import settings
        assert settings is not None

    def test_settings_has_app_name(self):
        from app.core.config import settings
        assert settings.app_name == "octopus"

    def test_settings_log_level_valid(self):
        from app.core.config import settings
        assert settings.log_level in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")

    def test_settings_no_hardcoded_credentials(self):
        from app.core.config.settings import Settings
        import inspect
        source = inspect.getsource(Settings)
        # Ensure no real API key patterns are hardcoded
        assert "sk-" not in source
        assert "ghp_" not in source

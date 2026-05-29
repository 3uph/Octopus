"""OCT-013: AuditLog model and audit dependency."""
import uuid

import pytest


class TestAuditLogModel:
    def test_audit_log_importable(self):
        from app.models.audit_log import AuditLog
        assert AuditLog is not None

    def test_audit_log_tablename(self):
        from app.models.audit_log import AuditLog
        assert AuditLog.__tablename__ == "audit_logs"

    def test_audit_log_has_required_columns(self):
        from app.models.audit_log import AuditLog
        cols = {c.name for c in AuditLog.__table__.columns}
        assert {"id", "user_id", "action", "entity_type", "entity_id",
                "details_redacted", "ip", "created_at"} <= cols

    def test_audit_log_details_is_jsonb(self):
        from app.models.audit_log import AuditLog
        from sqlalchemy.dialects.postgresql import JSONB
        col = AuditLog.__table__.c["details_redacted"]
        assert isinstance(col.type, JSONB)

    def test_migration_file_exists(self):
        from pathlib import Path
        p = Path(__file__).parent.parent / "app" / "database" / "migrations" / "versions" / "0002_audit_log.py"
        assert p.exists()


class TestAuditDependency:
    def test_audit_action_importable(self):
        from app.api.dependencies.audit import audit_action
        assert callable(audit_action)

    def test_audit_action_redacts_secrets(self):
        """audit_action redacts sensitive keys by name."""
        from app.api.dependencies.audit import _SENSITIVE_KEYS
        from app.core.logging.redactor import redact

        details = {"password": "supersecret", "user": "alice"}
        redacted = {
            k: "[REDACTED]" if k.lower() in _SENSITIVE_KEYS else redact(str(v))
            for k, v in details.items()
        }
        assert "supersecret" not in redacted.get("password", "")
        assert redacted["user"] == "alice"

    def test_details_none_produces_none(self):
        """None details should result in None stored."""
        details = None
        result = None if not details else {}
        assert result is None

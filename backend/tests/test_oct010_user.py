"""OCT-010: User model and schema."""
import uuid

import pytest


class TestUserModel:
    def test_user_model_importable(self):
        from app.models.user import User, UserRole
        assert User is not None
        assert UserRole is not None

    def test_user_role_enum_values(self):
        from app.models.user import UserRole
        assert UserRole.ADMIN == "admin"
        assert UserRole.OPERATOR == "operator"
        assert UserRole.VIEWER == "viewer"

    def test_user_tablename(self):
        from app.models.user import User
        assert User.__tablename__ == "users"

    def test_user_has_required_columns(self):
        from app.models.user import User
        columns = {c.name for c in User.__table__.columns}
        assert {"id", "username", "email", "password_hash", "role",
                "is_active", "last_login_at", "created_at", "updated_at"} <= columns

    def test_user_username_unique(self):
        from app.models.user import User
        col = User.__table__.c["username"]
        # Check unique constraint exists (either on column or via index)
        assert col.unique or any(
            idx.unique and "username" in [c.name for c in idx.columns]
            for idx in User.__table__.indexes
        )

    def test_user_email_unique(self):
        from app.models.user import User
        col = User.__table__.c["email"]
        assert col.unique or any(
            idx.unique and "email" in [c.name for c in idx.columns]
            for idx in User.__table__.indexes
        )


class TestUserSchemas:
    def test_user_create_valid(self):
        from app.schemas.user import UserCreate, UserRole
        u = UserCreate(username="alice", email="alice@example.com", password="secret123")
        assert u.username == "alice"
        assert u.role == UserRole.VIEWER

    def test_user_create_short_username_rejected(self):
        from app.schemas.user import UserCreate
        with pytest.raises(Exception):
            UserCreate(username="ab", email="a@b.com", password="secret123")

    def test_user_create_short_password_rejected(self):
        from app.schemas.user import UserCreate
        with pytest.raises(Exception):
            UserCreate(username="alice", email="a@b.com", password="short")

    def test_user_read_has_no_password_field(self):
        from app.schemas.user import UserRead
        import inspect
        fields = UserRead.model_fields.keys()
        assert "password" not in fields
        assert "password_hash" not in fields

    def test_user_read_from_orm(self):
        from app.schemas.user import UserRead, UserRole
        from datetime import datetime, timezone
        # Simulate ORM object
        class FakeUser:
            id = uuid.uuid4()
            username = "bob"
            email = "bob@example.com"
            role = UserRole.ADMIN
            is_active = True
            last_login_at = None
            created_at = datetime.now(timezone.utc)

        result = UserRead.model_validate(FakeUser())
        assert result.username == "bob"
        assert result.role == UserRole.ADMIN

    def test_migration_file_exists(self):
        from pathlib import Path
        p = Path(__file__).parent.parent / "app" / "database" / "migrations" / "versions" / "0001_user.py"
        assert p.exists()

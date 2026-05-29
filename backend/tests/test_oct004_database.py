"""OCT-004: Verify SQLAlchemy + Alembic setup (unit-level, no live DB required)."""
from pathlib import Path

import pytest
import sqlalchemy as sa


class TestDatabaseModuleImports:
    def test_base_importable(self):
        from app.database.base import Base, TimestampMixin
        assert Base is not None
        assert TimestampMixin is not None

    def test_get_db_session_importable(self):
        from app.database.session import get_db_session
        assert callable(get_db_session)

    def test_get_engine_importable(self):
        # Only import the factory function, NOT calling it (avoids asyncpg at test time)
        from app.database.engine import get_engine
        assert callable(get_engine)

    def test_db_dependency_importable(self):
        from app.api.dependencies.db import get_db
        assert callable(get_db)


class TestTimestampMixin:
    def test_mixin_has_id_field(self):
        from app.database.base import TimestampMixin
        assert hasattr(TimestampMixin, "id")

    def test_mixin_has_created_at(self):
        from app.database.base import TimestampMixin
        assert hasattr(TimestampMixin, "created_at")

    def test_mixin_has_updated_at(self):
        from app.database.base import TimestampMixin
        assert hasattr(TimestampMixin, "updated_at")

    def test_mixin_composable(self):
        from app.database.base import Base, TimestampMixin

        class DummyModel(TimestampMixin, Base):
            __tablename__ = "dummy_test_oct004"
            name: str = sa.Column(sa.String, nullable=False)

        assert hasattr(DummyModel, "id")
        assert hasattr(DummyModel, "created_at")
        assert hasattr(DummyModel, "updated_at")
        # Check id column is UUID type
        assert "UUID" in str(DummyModel.__table__.c["id"].type)


class TestAlembicSetup:
    def test_alembic_ini_exists(self):
        root = Path(__file__).parent.parent
        assert (root / "alembic.ini").exists()

    def test_migrations_dir_exists(self):
        root = Path(__file__).parent.parent
        assert (root / "app" / "database" / "migrations").is_dir()

    def test_env_py_exists(self):
        root = Path(__file__).parent.parent
        assert (root / "app" / "database" / "migrations" / "env.py").exists()

    def test_script_mako_exists(self):
        root = Path(__file__).parent.parent
        assert (root / "app" / "database" / "migrations" / "script.py.mako").exists()

    def test_versions_dir_exists(self):
        root = Path(__file__).parent.parent
        assert (root / "app" / "database" / "migrations" / "versions").is_dir()

    def test_alembic_ini_no_real_password(self):
        root = Path(__file__).parent.parent
        ini = (root / "alembic.ini").read_text()
        # Should not contain actual password — URL is overridden by env.py
        assert "change_me" not in ini
        assert "postgresql+asyncpg://octopus:" not in ini

    def test_env_py_reads_settings(self):
        root = Path(__file__).parent.parent
        env_content = (root / "app" / "database" / "migrations" / "env.py").read_text()
        assert "settings.database_url" in env_content
        assert "target_metadata" in env_content


class TestEngineConfig:
    def test_engine_url_uses_async_driver(self):
        from app.core.config import settings
        # Verify the configured URL uses asyncpg driver (checked from settings, not engine)
        assert "asyncpg" in settings.database_url or "postgresql" in settings.database_url

    def test_no_shell_true_in_database_module(self):
        root = Path(__file__).parent.parent / "app" / "database"
        for py_file in root.rglob("*.py"):
            source = py_file.read_text()
            assert "shell=True" not in source, f"shell=True found in {py_file}"

    def test_default_database_url_is_async(self):
        from app.core.config import settings
        assert "asyncpg" in settings.database_url

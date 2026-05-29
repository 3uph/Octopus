"""OCT-014: Setting model with encrypted secrets."""
import os

import pytest


class TestEncryption:
    def _make_fernet_key(self) -> str:
        from cryptography.fernet import Fernet
        return Fernet.generate_key().decode()

    def test_encrypt_decrypt_roundtrip(self, monkeypatch):
        key = self._make_fernet_key()
        monkeypatch.setenv("ENCRYPTION_KEY", key)
        # Reset lru_cache so settings picks up new env
        from app.core.config.settings import get_settings
        get_settings.cache_clear()

        from app.core.security.encryption import decrypt_value, encrypt_value
        ct = encrypt_value("my_api_key_12345")
        pt = decrypt_value(ct)
        assert pt == "my_api_key_12345"

    def test_encrypted_differs_from_plain(self, monkeypatch):
        key = self._make_fernet_key()
        monkeypatch.setenv("ENCRYPTION_KEY", key)
        from app.core.config.settings import get_settings
        get_settings.cache_clear()

        from app.core.security.encryption import encrypt_value
        ct = encrypt_value("secret_value")
        assert ct != "secret_value"
        assert len(ct) > 20

    def test_wrong_key_raises(self, monkeypatch):
        from cryptography.fernet import Fernet
        key1 = Fernet.generate_key().decode()
        key2 = Fernet.generate_key().decode()

        monkeypatch.setenv("ENCRYPTION_KEY", key1)
        from app.core.config.settings import get_settings
        get_settings.cache_clear()
        from app.core.security.encryption import encrypt_value
        ct = encrypt_value("secret")

        monkeypatch.setenv("ENCRYPTION_KEY", key2)
        get_settings.cache_clear()
        from app.core.security.encryption import decrypt_value, EncryptionError
        with pytest.raises(EncryptionError):
            decrypt_value(ct)


class TestSettingModel:
    def test_setting_importable(self):
        from app.models.setting import Setting, SettingScope
        assert Setting is not None
        assert SettingScope is not None

    def test_setting_scope_values(self):
        from app.models.setting import SettingScope
        assert SettingScope.GLOBAL == "global"
        assert SettingScope.COMPANY == "company"
        assert SettingScope.PROGRAM == "program"

    def test_setting_tablename(self):
        from app.models.setting import Setting
        assert Setting.__tablename__ == "settings"

    def test_setting_has_required_columns(self):
        from app.models.setting import Setting
        cols = {c.name for c in Setting.__table__.columns}
        assert {"id", "scope", "scope_id", "key", "value", "is_secret"} <= cols

    def test_make_encrypted_value_wraps_in_dict(self, monkeypatch):
        from cryptography.fernet import Fernet
        key = Fernet.generate_key().decode()
        monkeypatch.setenv("ENCRYPTION_KEY", key)
        from app.core.config.settings import get_settings
        get_settings.cache_clear()

        from app.models.setting import Setting
        wrapped = Setting.make_encrypted_value("my_secret")
        assert "_enc" in wrapped
        assert wrapped["_enc"] != "my_secret"

    def test_migration_file_exists(self):
        from pathlib import Path
        p = Path(__file__).parent.parent / "app" / "database" / "migrations" / "versions" / "0003_setting.py"
        assert p.exists()

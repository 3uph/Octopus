"""Symmetric encryption for Setting.is_secret values using Fernet.

Key must be a URL-safe base64-encoded 32-byte key.
Generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
Set as ENCRYPTION_KEY in .env.
"""
from __future__ import annotations

import base64

from cryptography.fernet import Fernet, InvalidToken

from app.core.logging import get_logger

logger = get_logger(__name__)


class EncryptionError(Exception):
    """Raised when encryption or decryption fails."""


def _get_fernet() -> Fernet:
    from app.core.config.settings import get_settings
    key = get_settings().encryption_key.strip()
    # If key is a hex string (32 bytes = 64 hex chars), convert to Fernet key
    if len(key) == 64 and all(c in "0123456789abcdefABCDEF" for c in key):
        key = base64.urlsafe_b64encode(bytes.fromhex(key)).decode()
    try:
        return Fernet(key.encode() if isinstance(key, str) else key)
    except Exception as exc:
        raise EncryptionError(
            "Invalid ENCRYPTION_KEY. Generate with: "
            "python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
        ) from exc


def encrypt_value(plaintext: str) -> str:
    """Encrypt a string value. Returns base64-encoded ciphertext."""
    try:
        return _get_fernet().encrypt(plaintext.encode()).decode()
    except Exception as exc:
        raise EncryptionError("Encryption failed") from exc


def decrypt_value(ciphertext: str) -> str:
    """Decrypt a Fernet-encrypted value. Raises EncryptionError on failure."""
    try:
        return _get_fernet().decrypt(ciphertext.encode()).decode()
    except InvalidToken as exc:
        raise EncryptionError("Decryption failed: invalid token or wrong key") from exc
    except Exception as exc:
        raise EncryptionError(f"Decryption error: {exc}") from exc

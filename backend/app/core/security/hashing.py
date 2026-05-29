"""Password hashing with argon2 (via passlib).

argon2 is the preferred algorithm (D-23) and avoids bcrypt 4.x compatibility issues.
"""
from passlib.context import CryptContext

_ctx = CryptContext(schemes=["argon2"], deprecated="auto")


def hash_password(plain: str) -> str:
    """Return argon2 hash of plain-text password."""
    return _ctx.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Return True if plain matches the hash. Timing-safe."""
    return _ctx.verify(plain, hashed)

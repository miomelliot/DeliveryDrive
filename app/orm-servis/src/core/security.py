# src/core/security.py
from typing import cast

from passlib.context import CryptContext

_pwd_ctx = CryptContext(schemes=["argon2"], deprecated="auto")


# ─────────────────────── password helpers ─────────────────────
def hash_password(password: str) -> str:
    return cast(str, _pwd_ctx.hash(password))


def verify_password(password: str, password_hash: str) -> bool:
    return cast(bool, _pwd_ctx.verify(password, password_hash))

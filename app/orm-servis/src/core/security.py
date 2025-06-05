# src/core/security.py
from typing import cast

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# --- Password hash ---
def hash_password(password: str) -> str:
    return cast(str, pwd_context.hash(password))


def verify_password(password: str, password_hash: str) -> bool:
    return cast(bool, pwd_context.verify(password, password_hash))

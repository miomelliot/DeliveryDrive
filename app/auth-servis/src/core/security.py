from __future__ import annotations

from datetime import datetime
from typing import Dict, Union, cast
from uuid import UUID

from jose import JWTError, jwt
from passlib.context import CryptContext

from src.core.config import Settings, get_settings

_cfg: Settings = get_settings()

# ── конфигурация Argon2 ───────────────────────────────────────
_pwd_ctx: CryptContext = CryptContext(schemes=["argon2"], deprecated="auto")


# ─────────────────────── password helpers ─────────────────────
def hash_password(raw: str) -> str:
    """Вернуть Argon2-хеш пароля."""
    return cast(str, _pwd_ctx.hash(raw))


def verify_password(raw: str, hashed: str) -> bool:
    """Проверить совпадение пароля с хешем."""
    return cast(bool, _pwd_ctx.verify(raw, hashed))


# ─────────────────────── JWT helpers ──────────────────────────
def create_access_token(*, user_id: UUID, role: str) -> str:
    """
    Сформировать access-token.

    exp пишем как Unix-timestamp (int), чтобы гарантировать JSON-совместимость.
    """
    exp_ts: int = int((datetime.utcnow() + _cfg.access_token_expire).timestamp())
    payload: Dict[str, Union[str, int]] = {
        "sub": str(user_id),
        "role": role,
        "exp": exp_ts,
    }
    return cast(str, jwt.encode(payload, _cfg.jwt_secret, algorithm=_cfg.jwt_alg))


def decode_access_token(token: str) -> Dict[str, Union[str, int]]:
    """
    Декодировать JWT, вернуть payload.

    При ошибке подписи/срока — ValueError.
    """
    try:
        decoded: Dict[str, str | int] = cast(
            Dict[str, Union[str, int]],
            jwt.decode(token, _cfg.jwt_secret, algorithms=[_cfg.jwt_alg]),
        )
        return decoded
    except JWTError as exc:
        raise ValueError("Invalid or expired token") from exc

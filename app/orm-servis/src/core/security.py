# src/core/security.py
from typing import Union, cast

from jose import JWTError, jwt
from passlib.context import CryptContext

from src.core.config import Settings, get_settings

_cfg: Settings = get_settings()
_pwd_ctx = CryptContext(schemes=["argon2"], deprecated="auto")



def hash_password(password: str) -> str:
    return cast(str, _pwd_ctx.hash(password))


def verify_password(password: str, password_hash: str) -> bool:
    return cast(bool, _pwd_ctx.verify(password, password_hash))


def decode_access_token(token: str) -> dict[str, Union[str, int]]:
    try:
        decoded: dict[str, str | int] = cast(
            dict[str, Union[str, int]],
            jwt.decode(token, _cfg.jwt_secret, algorithms=[_cfg.jwt_alg]),
        )
        return decoded
    except JWTError as exc:
        raise ValueError("Invalid or expired token") from exc

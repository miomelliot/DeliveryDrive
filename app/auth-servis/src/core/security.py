from datetime import datetime, timedelta, timezone
from typing import Any, cast

from jose import JWTError, jwt
from passlib.context import CryptContext

from src.core.config import Settings, get_settings
from src.schemas.schemas import TokenPayload

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
settings: Settings = get_settings()


# --- Password hash ---
def hash_password(password: str) -> str:
    return cast(str, pwd_context.hash(password))


def verify_password(password: str, password_hash: str) -> bool:
    return cast(bool, pwd_context.verify(password, password_hash))


# --- JWT ---
def create_access_token(*, user_id: str, role: str, expires_delta: timedelta | None = None) -> str:
    expire: datetime = datetime.now(timezone.utc) + (expires_delta or settings.access_token_expire)
    to_encode: dict[str, Any] = {
        "sub": str(user_id),
        "role": role,
        "exp": int(expire.timestamp()),
    }
    return cast(
        str,
        jwt.encode(
            to_encode,
            settings.jwt_secret.get_secret_value(),
            algorithm=settings.jwt_alg,
        ),
    )


def decode_access_token(token: str) -> TokenPayload:
    try:
        payload: dict[str, Any] = jwt.decode(
            token, settings.jwt_secret.get_secret_value(), algorithms=[settings.jwt_alg]
        )
        return TokenPayload(**payload)
    except JWTError as err:
        raise ValueError("Invalid or expired token") from err

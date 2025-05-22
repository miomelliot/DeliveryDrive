# src/api/deps.py
from typing import Any
from uuid import UUID

from fastapi import Header, HTTPException
from jose import JWTError, jwt
from pydantic import BaseModel

from src.core.config import Settings, get_settings

settings: Settings = get_settings()

SECRET_KEY: str = settings.jwt_secret.get_secret_value()
ALGORITHM: str = settings.jwt_alg


class CurrentUser(BaseModel):
    user_id: UUID
    role: str


def get_current_user(authorization: str = Header(...)) -> CurrentUser:
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Недопустимая схема авторизации")

    try:
        payload: dict[str, Any] = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return CurrentUser(
            user_id=UUID(payload["user_id"]),
            role=payload["role"],
        )
    except JWTError as err:
        raise HTTPException(status_code=401, detail="Недействительный или просроченный токен") from err

# src/api/auth.py
from typing import Dict
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import (
    create_access_token,
    decode_access_token,
    verify_password,
)
from src.db.models import User
from src.db.session import get_session
from src.schemas.schemas import AuthLogin, Token, UserOut
from src.utils.http_error import _raise_401

router = APIRouter(prefix="/auth", tags=["Auth"])

# Bearer-заголовок вида «Authorization: Bearer <JWT>»
bearer_scheme = HTTPBearer(auto_error=False)


# ───────────────────────── login ────────────────────────────
@router.post(
    "/login",
    response_model=Token,
    summary="Login → получить access-token",
)
async def login(
    data: AuthLogin,
    session: AsyncSession = Depends(get_session),
) -> Token:
    user: User | None = await session.scalar(select(User).where(User.email == data.email))

    if user is None or not verify_password(data.password, user.password_hash):
        _raise_401("Неверный email или пароль")

    token: str = create_access_token(user_id=user.id, role=user.role.name)
    return Token(access_token=token)


# ─────────────────── current user dependency ────────────────
async def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_session),
) -> User:
    """Извлечь User из Bearer-токена (используй как Depends)."""
    if creds is None:
        _raise_401("Отсутствует токен авторизации")

    payload: Dict[str, str | int] = decode_access_token(creds.credentials)
    sub_raw: str | int = payload["sub"]
    try:
        user_id: UUID = UUID(str(sub_raw))
    except Exception:
        _raise_401("Неверный или просроченный токен")

    user: User | None = await session.get(User, user_id)
    if user is None:
        _raise_401("Пользователь не найден")

    return user


# ───────────────────────── /me ───────────────────────────────
@router.get("/me", response_model=UserOut, summary="Текущий пользователь")
async def read_me(current_user: User = Depends(get_current_user)) -> User:
    return current_user

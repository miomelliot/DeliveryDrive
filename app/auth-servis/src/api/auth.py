# src/api/auth.py
from typing import Dict, Tuple
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload  #  ← добавили

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
bearer_scheme = HTTPBearer(auto_error=False)


# ───────────────────────── login ────────────────────────────
@router.post("/login", response_model=Token, summary="Login → получить access-token")
async def login(
    data: AuthLogin,
    session: AsyncSession = Depends(get_session),
) -> Token:
    stmt: Select[Tuple[User]] = select(User).options(selectinload(User.role)).where(User.email == data.email)
    user: User | None = await session.scalar(stmt)

    if user is None or not verify_password(data.password, user.password_hash):
        _raise_401("Неверный email или пароль")

    token = create_access_token(user_id=user.id, role=user.role.name)
    return Token(access_token=token)


# ─────────────────── current user dependency ────────────────
async def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_session),
) -> User:
    if creds is None:
        _raise_401("Отсутствует токен авторизации")

    payload: Dict[str, str | int] = decode_access_token(creds.credentials)
    try:
        user_id = UUID(str(payload["sub"]))
    except Exception:
        _raise_401("Неверный или просроченный токен")

    stmt: Select[Tuple[User]] = select(User).options(selectinload(User.role)).where(User.id == user_id)
    user: User | None = await session.scalar(stmt)
    if user is None:
        _raise_401("Пользователь не найден")

    return user


# ───────────────────────── /me ───────────────────────────────
@router.get("/me", response_model=UserOut, summary="Текущий пользователь")
async def read_me(current_user: User = Depends(get_current_user)) -> UserOut:
    return UserOut(
        id=current_user.id,
        email=current_user.email,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        phone=current_user.phone,
        avatar_path=current_user.avatar_path,
        role=current_user.role.name,
    )

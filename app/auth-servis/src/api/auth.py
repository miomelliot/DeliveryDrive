# src/api/auth.py
from typing import Tuple

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import Result, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import (
    create_access_token,
    decode_access_token,
    verify_password,
)
from src.db.models import User
from src.db.session import get_session
from src.schemas.schemas import Token, TokenPayload, UserOut
from src.utils.http_error import _raise_401

router = APIRouter(prefix="/auth", tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_session),
) -> Token:
    """
    Аутентификация по email и паролю.
    Возвращает JWT access token.
    """
    result: Result[Tuple[User]] = await session.execute(select(User).where(User.email == form_data.username))
    user: User | None = result.scalar_one_or_none()

    if user is None or not verify_password(form_data.password, user.password_hash):
        _raise_401("Неверный логин или пароль")

    token: str = create_access_token(user_id=str(user.id), role=user.role.name)
    return Token(access_token=token, token_type="bearer")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_session),
) -> User:
    """
    Извлекает пользователя из токена доступа.
    Используется как зависимость в защищённых маршрутах.
    """
    try:
        payload: TokenPayload = decode_access_token(token)
    except Exception:
        _raise_401("Недействительный или просроченный токен")

    result: Result[Tuple[User]] = await session.execute(select(User).where(User.id == payload.sub))
    user: User | None = result.scalar_one_or_none()

    if user is None:
        _raise_401("Пользователь не найден")

    return user


@router.get("/me", response_model=UserOut)
async def read_me(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Возвращает информацию о текущем пользователе (на основе JWT).
    """
    return current_user

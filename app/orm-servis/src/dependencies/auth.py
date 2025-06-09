# src/dependencies/auth.py
from typing import Dict, Tuple
from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.security import decode_access_token
from src.db.models import User
from src.db.session import get_session
from src.schemas.auth import CurrentUser
from src.utils.http_error import _raise_401

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_session),
) -> CurrentUser:
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

    return CurrentUser(id=user.id, role=user.role.name)

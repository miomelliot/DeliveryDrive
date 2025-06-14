from collections.abc import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from src.db.session import AsyncSessionFactory
from src.dependencies.auth import get_current_user
from src.schemas.auth import CurrentUser


async def get_session_with_user(
    current_user: CurrentUser = Depends(get_current_user),
) -> AsyncGenerator[AsyncSession]:
    async with AsyncSessionFactory() as session:
        session.info["user_id"] = current_user.id
        async with session.begin():
            try:
                yield session
            finally:
                ...

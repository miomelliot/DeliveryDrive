# src/db/session.py
from collections.abc import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.core.config import Settings, get_settings
from src.dependencies.auth import get_current_user
from src.schemas.auth import CurrentUser

settings: Settings = get_settings()

engine: AsyncEngine = create_async_engine(
    settings.sqlalchemy_dsn_str,
    echo=settings.debug,
    pool_pre_ping=True,
    future=True,
)

AsyncSessionFactory: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionFactory() as session:
        async with session.begin():
            try:
                yield session
            except Exception:
                raise


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

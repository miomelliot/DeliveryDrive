# src/db/session.py
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.core.config import Settings, get_settings

settings: Settings = get_settings()

engine: AsyncEngine = create_async_engine(
    settings.sqlalchemy_dsn_str,
    echo=settings.debug,
)

AsyncSessionFactory = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionFactory() as session:
        async with session.begin():
            try:
                yield session
            except Exception:
                raise

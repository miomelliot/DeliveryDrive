from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

from sqlalchemy import CursorResult, text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.ext.asyncio.engine import AsyncEngine

from db.models import Base


PG_USER: str = os.getenv("POSTGRES_USER", "pg_user")
PG_PASS: str = os.getenv("POSTGRES_PASSWORD", "pg_password")
PG_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
PG_PORT: str = os.getenv("POSTGRES_PORT", "5432")
PG_DB: str = os.getenv("POSTGRES_DB", "postgres")

PG_DSN_ADMIN: str = (
    f"postgresql+asyncpg://{PG_USER}:{PG_PASS}@{PG_HOST}:{PG_PORT}/{PG_DB}"
)

PG_DSN_APP: str = PG_DSN_ADMIN

# ─────────── helpers ───────────
async def _database_exists() -> bool:
    admin_engine: AsyncEngine = create_async_engine(PG_DSN_ADMIN, isolation_level="AUTOCOMMIT")
    async with admin_engine.connect() as conn:
        result: CursorResult[Any] = await conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname=:name"),
            {"name": PG_DB},
        )
        return result.scalar() is not None


async def _create_database() -> None:
    admin_engine: AsyncEngine = create_async_engine(PG_DSN_ADMIN, isolation_level="AUTOCOMMIT")
    async with admin_engine.connect() as conn:
        await conn.execute(text(f'CREATE DATABASE "{PG_DB}"'))
        await conn.commit()


async def init_database() -> None:
    """Выполнить one-shot инициализацию при старте контейнера."""
    if not await _database_exists():
        await _create_database()

    engine: AsyncEngine = create_async_engine(PG_DSN_APP, pool_pre_ping=True)
    async with engine.begin() as conn:
        # если нужен alembic – вместо create_all вызвать upgrade.
        await conn.run_sync(Base.metadata.create_all)


# ─────────── session factory ───────────
_engine: AsyncEngine = create_async_engine(PG_DSN_APP, pool_pre_ping=True)
SessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=_engine,
    autoflush=False,
    expire_on_commit=False,
)


@asynccontextmanager
async def get_session() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:
        yield session

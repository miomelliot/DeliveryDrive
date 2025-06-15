from contextlib import asynccontextmanager
from typing import AsyncIterator

from neo4j import AsyncDriver, AsyncGraphDatabase, AsyncSession

from src.core.config import Settings, get_settings

_settings: Settings = get_settings()
_driver: AsyncDriver | None = None


def get_driver() -> AsyncDriver:
    global _driver
    if _driver is None:
        _driver = AsyncGraphDatabase.driver(
            _settings.neo4j_dsn,
            auth=(_settings.neo4j_user, _settings.neo4j_password),
        )
    return _driver


@asynccontextmanager
async def get_neo4j_session() -> AsyncIterator[AsyncSession]:
    driver: AsyncDriver = get_driver()
    async with driver.session() as session:
        yield session

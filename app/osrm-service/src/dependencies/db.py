# src/dependencies/db.py
from typing import AsyncContextManager, AsyncGenerator

from fastapi import Depends
from neo4j import AsyncSession

from src.db.graph import get_neo4j_session


async def neo4j_session(
    dep: AsyncContextManager[AsyncSession] = Depends(get_neo4j_session),
) -> AsyncGenerator[AsyncSession, None]:
    async with dep as session:
        yield session

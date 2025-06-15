# src/dependencies/db.py
from fastapi import Depends

from src.db.graph import get_neo4j_session


async def neo4j_session(dep=Depends(get_neo4j_session)):
    async with dep as session:
        yield session

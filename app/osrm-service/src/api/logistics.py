# src/api/logistics.py
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import APIRouter, Depends, status
from neo4j._async.work.session import AsyncSession

from src.core.config import get_settings
from src.db.graph import get_neo4j_session
from src.schemas.logistics import Logistics
from src.services.logistics_service import process_logistics

router = APIRouter(prefix="/logistics", tags=["Logistics"])


@asynccontextmanager
async def neo4j_session_ctx() -> AsyncIterator[AsyncSession]:
    async with get_neo4j_session() as session:
        yield session


@router.post("/", status_code=status.HTTP_200_OK)
async def upload_logistics(
    payload: Logistics,
    neo: AsyncSession = Depends(neo4j_session_ctx),
) -> dict[str, list[list[str]]]:
    settings = get_settings()
    routes = await process_logistics(payload, neo, settings)
    return {"routes": routes}

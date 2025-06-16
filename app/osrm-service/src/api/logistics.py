# src/api/logistics.py
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import APIRouter, BackgroundTasks, status
from neo4j._async.work.session import AsyncSession

from src.db.graph import get_neo4j_session
from src.schemas.logistics import Logistics
from src.services.logistics_service import ingest_addresses

router = APIRouter(prefix="/logistics", tags=["Logistics"])


@asynccontextmanager
async def neo4j_session_ctx() -> AsyncIterator[AsyncSession]:
    async with get_neo4j_session() as session:
        yield session


async def _background_ingest(payload: Logistics) -> None:
    async with neo4j_session_ctx() as neo:
        await ingest_addresses(payload, neo)


@router.post("/", status_code=status.HTTP_202_ACCEPTED)
async def upload_logistics(
    payload: Logistics,
    background: BackgroundTasks,
) -> dict[str, str]:
    background.add_task(_background_ingest, payload)
    return {"detail": f"{len(payload.orders)} orders accepted"}

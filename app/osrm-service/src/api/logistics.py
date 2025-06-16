# src/api/logistics.py
import asyncio
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator
from uuid import UUID

from fastapi import APIRouter, status
from loguru import logger
from neo4j._async.work.session import AsyncSession

from src.core.config import Settings, get_settings
from src.db.graph import get_neo4j_session
from src.db.session import AsyncSessionFactory
from src.schemas.logistics import Logistics
from src.services.logistics_builder import build_logistics
from src.services.logistics_service import process_logistics
from src.services.route_service import save_routes

router = APIRouter(prefix="/logistics", tags=["Logistics"])


async def _save_routes_bg(plans: list[dict[str, Any]]) -> None:
    async with AsyncSessionFactory() as session:
        async with session.begin():
            await save_routes(session, plans)


async def _process_and_save(payload: Logistics, settings: Settings) -> None:
    routes: list[dict[str, Any]] = await process_logistics(payload, settings)
    await _save_routes_bg(routes)


async def _assign_routes_bg(order_ids: list[UUID], settings: Settings) -> None:
    async with AsyncSessionFactory() as session:
        async with session.begin():
            payload: Logistics = await build_logistics(session, order_ids)
            plans: list[dict[str, Any]] = await process_logistics(payload, settings)
            await save_routes(session, plans)


@asynccontextmanager
async def neo4j_session_ctx() -> AsyncIterator[AsyncSession]:
    async with get_neo4j_session() as session:
        yield session


@router.post("/", status_code=status.HTTP_202_ACCEPTED)
async def upload_logistics(
    payload: Logistics,
) -> dict[str, str]:
    logger.info(
        f"Received logistics payload with {len(payload.orders)} orders and {len(payload.creates)} couriers",
    )
    settings: Settings = get_settings()
    asyncio.create_task(_process_and_save(payload, settings))
    logger.info("Scheduled logistics processing")
    return {"status": "processing"}


@router.post("/assign", status_code=status.HTTP_202_ACCEPTED)
async def assign_routes(
    order_ids: list[UUID],
) -> dict[str, str]:
    logger.info(f"Assigning routes for {len(order_ids)} orders")
    settings: Settings = get_settings()
    asyncio.create_task(_assign_routes_bg(order_ids, settings))
    logger.info("Scheduled route assignment")
    return {"status": "processing"}

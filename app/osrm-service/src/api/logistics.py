# src/api/logistics.py
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator
from uuid import UUID

from fastapi import APIRouter, Depends, status
from neo4j._async.work.session import AsyncSession
from sqlalchemy.ext.asyncio import AsyncSession as DBSession

from src.core.config import Settings, get_settings
from src.db.graph import get_neo4j_session
from src.db.models import Route
from src.db.session import get_session
from src.schemas.logistics import Logistics
from src.services.logistics_builder import build_logistics
from src.services.logistics_service import process_logistics
from src.services.route_service import save_routes

router = APIRouter(prefix="/logistics", tags=["Logistics"])


@asynccontextmanager
async def neo4j_session_ctx() -> AsyncIterator[AsyncSession]:
    async with get_neo4j_session() as session:
        yield session


@router.post("/", status_code=status.HTTP_200_OK)
async def upload_logistics(
    payload: Logistics,
    session: DBSession = Depends(get_session),
) -> dict[str, list[str]]:
    settings: Settings = get_settings()
    plans: list[dict[str, Any]] = await process_logistics(payload, settings)
    created: list[Route] = await save_routes(session, plans)
    await session.commit()
    return {"routes": [str(r.id) for r in created]}


@router.post("/assign", status_code=status.HTTP_201_CREATED)
async def assign_routes(
    order_ids: list[UUID],
    session: DBSession = Depends(get_session),
) -> dict[str, list[str]]:
    payload: Logistics = await build_logistics(session, order_ids)
    settings: Settings = get_settings()
    plans: list[dict[str, Any]] = await process_logistics(payload, settings)
    created: list[Route] = await save_routes(session, plans)
    await session.commit()
    return {"routes": [str(r.id) for r in created]}

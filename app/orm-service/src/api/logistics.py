# src/schemas/logistics.py
from typing import Any, cast
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import Settings, get_settings
from src.db.models import Order
from src.dependencies.db import get_session_with_user
from src.repositories.tables.order_status import OrderStatusRepository
from src.schemas.logistics import Logistics
from src.services.logistics_service import build_logistics

router = APIRouter(prefix="/logistics", tags=["Logistics"])

settings: Settings = get_settings()
OSRM_URL: str = settings.osrm_service_url.rstrip("/")


async def _update_orders_status(
    session: AsyncSession,
    order_ids: list[UUID],
    code: str,
) -> None:
    if not order_ids:
        return
    status_id: int = await OrderStatusRepository().get_code_id(session, code)
    await session.execute(update(Order).where(Order.id.in_(order_ids)).values(status_id=status_id))


@router.post("/", status_code=status.HTTP_202_ACCEPTED)
async def get_logistics(
    order_ids: list[UUID],
    session: AsyncSession = Depends(get_session_with_user),
) -> dict[str, Any]:
    logger.info(
        f"Building logistics for {len(order_ids)} orders",
    )
    await _update_orders_status(session, order_ids, "in_processing")
    logistics: Logistics = await build_logistics(session, order_ids)
    try:
        async with httpx.AsyncClient(base_url=OSRM_URL, timeout=5.0) as client:
            resp: httpx.Response = await client.post(
                "/logistics/",
                json=logistics.model_dump(mode="json"),
            )
    except httpx.RequestError as exc:
        detail: str = f"Failed to reach OSRM service at {OSRM_URL}: {exc}"
        logger.error(detail)
        await _update_orders_status(session, order_ids, "new")
        raise HTTPException(status_code=502, detail=detail) from exc

    if resp.status_code not in (status.HTTP_200_OK, status.HTTP_202_ACCEPTED):
        logger.error(f"OSRM service returned {resp.status_code}: {resp.text}")
        await _update_orders_status(session, order_ids, "new")
        raise HTTPException(status_code=resp.status_code, detail=resp.text)

    logger.info("Received routes from OSRM service")
    return cast(dict[str, Any], resp.json())

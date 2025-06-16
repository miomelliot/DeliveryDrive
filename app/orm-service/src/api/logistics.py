# src/schemas/logistics.py
from typing import Any, cast
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import Settings, get_settings
from src.dependencies.db import get_session_with_user
from src.schemas.logistics import Logistics
from src.services.logistics_service import build_logistics

router = APIRouter(prefix="/logistics", tags=["Logistics"])

settings: Settings = get_settings()
OSRM_URL: str = settings.osrm_service_url.rstrip("/")


@router.post("/", status_code=status.HTTP_202_ACCEPTED)
async def get_logistics(
    order_ids: list[UUID],
    session: AsyncSession = Depends(get_session_with_user),
) -> dict[str, Any]:
    logistics: Logistics = await build_logistics(session, order_ids)
    try:
        async with httpx.AsyncClient(base_url=OSRM_URL, timeout=5.0) as client:
            resp: httpx.Response = await client.post(
                "/logistics/",
                json=logistics.model_dump(mode="json"),
            )
    except httpx.RequestError as exc:
        detail = f"Failed to reach OSRM service at {OSRM_URL}: {exc}"
        raise HTTPException(status_code=502, detail=detail) from exc

    if resp.status_code != status.HTTP_200_OK:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)

    return cast(dict[str, Any], resp.json())

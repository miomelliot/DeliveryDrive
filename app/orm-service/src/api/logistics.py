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
from src.services.route_service import save_routes

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
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    # The OSRM service now returns 200 on success
    if resp.status_code != status.HTTP_200_OK:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)

    return cast(dict[str, Any], resp.json())


@router.post("/assign", status_code=status.HTTP_201_CREATED)
async def assign_routes(
    order_ids: list[UUID],
    session: AsyncSession = Depends(get_session_with_user),
) -> dict[str, list[str]]:
    logistics: Logistics = await build_logistics(session, order_ids)
    try:
        async with httpx.AsyncClient(base_url=OSRM_URL, timeout=5.0) as client:
            resp: httpx.Response = await client.post(
                "/logistics/",
                json=logistics.model_dump(mode="json"),
            )
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    if resp.status_code != status.HTTP_200_OK:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)

    data = cast(dict[str, Any], resp.json())
    routes_data = cast(list[dict[str, Any]], data.get("routes", []))
    created = await save_routes(session, routes_data)
    await session.commit()
    return {"routes": [str(r.id) for r in created]}

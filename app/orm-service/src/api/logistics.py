# src/schemas/logistics.py
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.dependencies.db import get_session_with_user
from src.schemas.logistics import Logistics
from src.services.logistics_service import build_logistics

router = APIRouter(prefix="/logistics", tags=["Logistics"])


@router.post("/")
async def get_logistics(
    order_ids: list[UUID],
    session: AsyncSession = Depends(get_session_with_user),
) -> dict[str, Any]:
    logistics: Logistics = await build_logistics(session, order_ids)
    return logistics.model_dump(mode="json")

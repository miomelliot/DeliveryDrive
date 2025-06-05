# src/api/routing_chart.py
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from schemas.routing_chart import RoutingChartFilter, RoutingChartRead
from src.db.session import get_session
from src.repositories.routing_chart import RoutingChartRepository

router = APIRouter(prefix="/charts/routing", tags=["Routing Chart"])


@router.get("/", response_model=list[RoutingChartRead])
async def get_routing_chart(
    filters: Annotated[RoutingChartFilter, Depends()],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[RoutingChartRead]:
    repo = RoutingChartRepository(session)
    return await repo.get_chart(filters)


@router.get("/descriptions", response_model=list[str])
async def get_routing_status_descriptions(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[str]:
    repo = RoutingChartRepository(session)
    return await repo.get_unique_descriptions()

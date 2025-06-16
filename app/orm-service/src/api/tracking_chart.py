# src/api/tracking_chart.py
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.dependencies.db import get_session_with_user
from src.repositories.charts.tracking_chart import TrackingChartRepository
from src.schemas.routing_chart import RoutingChartFilter
from src.schemas.tracking_chart import TrackingChart

router = APIRouter(prefix="/charts/tracking", tags=["Tracking Chart"])


@router.get("/", response_model=TrackingChart)
async def get_tracking_chart(
    route_id: UUID = Query(...),
    filters: RoutingChartFilter = Depends(),
    session: AsyncSession = Depends(get_session_with_user),
) -> TrackingChart:
    repo = TrackingChartRepository(session)
    return await repo.get_chart(route_id, filters)

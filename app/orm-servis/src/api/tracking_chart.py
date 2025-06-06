# src/api/tracking_chart.py
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_session
from src.repositories.tracking_chart import TrackingChartRepository
from src.schemas.routing_chart import RoutingChartFilter
from src.schemas.tracking_chart import TrackingChart

router = APIRouter(prefix="/charts/tracking", tags=["TrackingChart"])


@router.get("/", response_model=TrackingChart)
async def get_tracking_chart(
    route_id: UUID = Query(...),
    filters: RoutingChartFilter = Depends(),
    session: AsyncSession = Depends(get_session),
) -> TrackingChart:
    repo = TrackingChartRepository(session)
    return await repo.get_tracking_chart(route_id, filters)

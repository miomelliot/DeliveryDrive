# src/api/tracking_chart.py
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_session
from src.dependencies.auth import get_current_user
from src.repositories.charts.tracking_chart import TrackingChartRepository
from src.schemas.auth import CurrentUser
from src.schemas.routing_chart import RoutingChartFilter
from src.schemas.tracking_chart import TrackingChart

router = APIRouter(prefix="/charts/tracking", tags=["Tracking Chart"])


@router.get("/", response_model=TrackingChart)
async def get_tracking_chart(
    route_id: UUID = Query(...),
    filters: RoutingChartFilter = Depends(),
    session: AsyncSession = Depends(get_session),
    current_user: CurrentUser = Depends(get_current_user),
) -> TrackingChart:
    repo = TrackingChartRepository(session)
    return await repo.get_chart(route_id, filters)

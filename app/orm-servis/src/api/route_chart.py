# src/api/route_chart.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_session
from src.repositories.route_chart import RouteChartRepository
from src.schemas.route_chart import RouteChart, RouteChartFilter

router = APIRouter(prefix="/charts/route", tags=["TrackingChart"])


@router.get("/", response_model=list[RouteChart])
async def get_tracking_chart(
    filters: RouteChartFilter = Depends(),
    session: AsyncSession = Depends(get_session),
) -> list[RouteChart]:
    repo = RouteChartRepository(session)
    return await repo.get_chart(filters)

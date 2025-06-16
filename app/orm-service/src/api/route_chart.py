# src/api/route_chart.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.dependencies.db import get_session_with_user
from src.repositories.charts.route_chart import RouteChartRepository
from src.schemas.route_chart import RouteChart, RouteChartFilter

router = APIRouter(prefix="/charts/route", tags=["Route Chart"])


@router.get("/", response_model=list[RouteChart])
async def get_route_chart(
    filters: RouteChartFilter = Depends(),
    session: AsyncSession = Depends(get_session_with_user),
) -> list[RouteChart]:
    repo = RouteChartRepository(session)
    return await repo.get_chart(filters)

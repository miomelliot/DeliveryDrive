# src/api/route_chart.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_session
from src.dependencies.auth import get_current_user
from src.repositories.charts.route_chart import RouteChartRepository
from src.schemas.auth import CurrentUser
from src.schemas.route_chart import RouteChart, RouteChartFilter

router = APIRouter(prefix="/charts/route", tags=["Route Chart"])


@router.get("/", response_model=list[RouteChart])
async def get_route_chart(
    filters: RouteChartFilter = Depends(),
    session: AsyncSession = Depends(get_session),
    current_user: CurrentUser = Depends(get_current_user),
) -> list[RouteChart]:
    repo = RouteChartRepository(session)
    return await repo.get_chart(filters)

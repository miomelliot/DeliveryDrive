# src/api/route_sheet_chart.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.dependencies.db import get_session_with_user
from src.repositories.charts.route_sheet_chart import RouteSheetChartRepository
from src.schemas.route_sheet_chart import RouteSheetChart, RouteSheetChartFilter

router = APIRouter(prefix="/charts/route-sheet", tags=["Route Sheet Chart"])


@router.get("/", response_model=list[RouteSheetChart])
async def get_route_sheet_chart(
    filters: RouteSheetChartFilter = Depends(),
    session: AsyncSession = Depends(get_session_with_user),
) -> list[RouteSheetChart]:
    return await RouteSheetChartRepository().get_chart(session, filters)

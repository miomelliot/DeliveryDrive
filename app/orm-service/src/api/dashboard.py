# src/api/dashboard.py
from datetime import date, timedelta
from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.dependencies.db import get_session_with_user
from src.repositories.charts.dashboard import DashboardRepository
from src.schemas.dashboard import (
    DayCount,
    EquipmentStockResponse,
    OrdersSummaryResponse,
    WarehouseSummaryResponse,
)

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/orders/daily", response_model=List[DayCount])
async def orders_daily(
    from_: date | None = Query(None, alias="from"),
    to: date | None = Query(None, alias="to"),
    session: AsyncSession = Depends(get_session_with_user),
) -> List[DayCount]:
    end: date = to or date.today()
    start: date = from_ or (end - timedelta(days=15))

    repo = DashboardRepository()
    return await repo.orders_count_by_day(session, start, end)


@router.get("/orders/summary", response_model=OrdersSummaryResponse)
async def orders_summary(
    date_: date | None = Query(None, alias="date"),
    session: AsyncSession = Depends(get_session_with_user),
) -> OrdersSummaryResponse:
    day = date_ or date.today()

    repo = DashboardRepository()
    return await repo.orders_summary_for_day(session, day)


@router.get("/warehouse/summary", response_model=WarehouseSummaryResponse)
async def warehouse_summary(
    session: AsyncSession = Depends(get_session_with_user),
) -> WarehouseSummaryResponse:
    repo = DashboardRepository()
    return await repo.warehouse_summary(session)


@router.get("/equipment/stock", response_model=List[EquipmentStockResponse])
async def equipment_stock(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    session: AsyncSession = Depends(get_session_with_user),
) -> List[EquipmentStockResponse]:
    offset: int = (page - 1) * size

    repo = DashboardRepository()
    items: List[EquipmentStockResponse] = await repo.equipment_stock(session, offset, size)

    return items

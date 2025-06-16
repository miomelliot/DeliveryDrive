# src/api/dashboard.py
from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.dependencies.db import get_session_with_user
from src.repositories.charts.dashboard import DashboardRepository
from src.schemas.dashboard import (
    CourierOrdersCount,
    DayCount,
    EquipmentStatusCount,
    FinanceDaily,
    OrderStatusDaily,
)

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/orders/daily", response_model=list[DayCount])
async def orders_daily(
    from_: date | None = Query(None, alias="from"),
    to: date | None = Query(None, alias="to"),
    session: AsyncSession = Depends(get_session_with_user),
) -> list[DayCount]:
    end: date = to or date.today()
    start: date = from_ or (end - timedelta(days=15))

    return await DashboardRepository().orders_count_by_day(session, start, end)


@router.get("/orders/status_daily", response_model=list[OrderStatusDaily])
async def orders_status_daily(
    from_: date | None = Query(None, alias="from"),
    to: date | None = Query(None, alias="to"),
    session: AsyncSession = Depends(get_session_with_user),
) -> list[OrderStatusDaily]:
    end: date = to or date.today()
    start: date = from_ or (end - timedelta(days=30))

    return await DashboardRepository().orders_by_status_daily(session, start, end)


@router.get("/orders/by_courier", response_model=list[CourierOrdersCount])
async def orders_by_courier(
    from_: date | None = Query(None, alias="from"),
    to: date | None = Query(None, alias="to"),
    session: AsyncSession = Depends(get_session_with_user),
) -> list[CourierOrdersCount]:
    end: date = to or date.today()
    start: date = from_ or (end - timedelta(days=30))

    return await DashboardRepository().orders_by_courier(session, start, end)


@router.get("/equipment/status_counts", response_model=list[EquipmentStatusCount])
async def equipment_status_counts(
    session: AsyncSession = Depends(get_session_with_user),
) -> list[EquipmentStatusCount]:
    return await DashboardRepository().equipment_status_counts(session)


@router.get("/finance/daily", response_model=list[FinanceDaily])
async def finance_daily(
    from_: date | None = Query(None, alias="from"),
    to: date | None = Query(None, alias="to"),
    session: AsyncSession = Depends(get_session_with_user),
) -> list[FinanceDaily]:
    end: date = to or date.today()
    start: date = from_ or (end - timedelta(days=30))

    return await DashboardRepository().finance_daily(session, start, end)

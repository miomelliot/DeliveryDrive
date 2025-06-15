# src/api/widget.py
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.dependencies.db import get_session_with_user
from src.repositories.charts.dashboard import DashboardRepository
from src.repositories.charts.invoice_chart import InvoiceChartRepository
from src.schemas.dashboard import (
    EquipmentStockResponse,
    OrdersSummaryResponse,
    WarehouseSummaryResponse,
)
from src.schemas.invoice_chart import InvoiceWidgetRead

router = APIRouter(prefix="/widget", tags=["Widget"])


@router.get("/orders/summary", response_model=OrdersSummaryResponse)
async def orders_summary(
    date_: date | None = Query(None, alias="date"),
    session: AsyncSession = Depends(get_session_with_user),
) -> OrdersSummaryResponse:
    day: date = date_ or date.today()

    return await DashboardRepository().orders_summary_for_day(session, day)


@router.get("/warehouse/summary", response_model=WarehouseSummaryResponse)
async def warehouse_summary(
    session: AsyncSession = Depends(get_session_with_user),
) -> WarehouseSummaryResponse:
    return await DashboardRepository().warehouse_summary(session)


@router.get("/equipment/stock", response_model=list[EquipmentStockResponse])
async def equipment_stock(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    session: AsyncSession = Depends(get_session_with_user),
) -> list[EquipmentStockResponse]:
    offset: int = (page - 1) * size

    return await DashboardRepository().equipment_stock(session, offset, size)


@router.get("/widget", response_model=InvoiceWidgetRead)
async def get_invoice_widget(
    session: AsyncSession = Depends(get_session_with_user),
) -> InvoiceWidgetRead:
    return await InvoiceChartRepository().get_widget(session)

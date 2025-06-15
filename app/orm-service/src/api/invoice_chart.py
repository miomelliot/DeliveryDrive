# src/api/invoice_chart.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.dependencies.db import get_session_with_user
from src.repositories.charts.invoice_chart import InvoiceChartRepository
from src.schemas.invoice_chart import InvoiceChartFilter, InvoiceChartRead, InvoiceWidgetRead

router = APIRouter(prefix="/charts/invoice", tags=["Invoice Chart"])


@router.get("/", response_model=list[InvoiceChartRead])
async def get_invoice_chart(
    filters: InvoiceChartFilter = Depends(),
    session: AsyncSession = Depends(get_session_with_user),
) -> list[InvoiceChartRead]:
    return await InvoiceChartRepository().get_chart(session, filters)


@router.get("/widget", response_model=InvoiceWidgetRead)
async def get_invoice_widget(
    session: AsyncSession = Depends(get_session_with_user),
) -> InvoiceWidgetRead:
    return await InvoiceChartRepository().get_widget(session)

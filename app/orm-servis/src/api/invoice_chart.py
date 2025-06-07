# src/api/invoice_chart.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_session
from src.repositories.invoice_chart import InvoiceChartRepository
from src.schemas.invoice_chart import InvoiceChartFilter, InvoiceChartRead, InvoiceWidgetRead

router = APIRouter(prefix="/charts/invoice", tags=["Invoice Chart"])


@router.get("/", response_model=list[InvoiceChartRead])
async def get_invoice_chart(
    filters: InvoiceChartFilter = Depends(),
    session: AsyncSession = Depends(get_session),
) -> list[InvoiceChartRead]:
    repo = InvoiceChartRepository(session)
    return await repo.get_chart(filters)


@router.get("/widget", response_model=InvoiceWidgetRead)
async def get_invoice_widget(
    session: AsyncSession = Depends(get_session),
) -> InvoiceWidgetRead:
    repo = InvoiceChartRepository(session)
    return await repo.get_widget()

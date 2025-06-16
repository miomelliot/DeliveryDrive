# src/api/order_chart.py
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.dependencies.db import get_session_with_user
from src.repositories.charts.order_chart import OrderChartRepository
from src.schemas.order_chart import OrderChartFilter, OrderChartRead

router = APIRouter(prefix="/charts/order", tags=["Order Chart"])


@router.get("/", response_model=list[OrderChartRead])
async def get_order_chart(
    filters: Annotated[OrderChartFilter, Depends()],
    session: Annotated[AsyncSession, Depends(get_session_with_user)],
) -> list[OrderChartRead]:
    return await OrderChartRepository().get_chart(session, filters)

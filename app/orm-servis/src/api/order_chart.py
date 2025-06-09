# src/api/order_chart.py
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_session
from src.dependencies.auth import get_current_user
from src.repositories.order_chart import OrderChartRepository
from src.schemas.auth import CurrentUser
from src.schemas.order_chart import OrderChartFilter, OrderChartRead

router = APIRouter(prefix="/charts/order", tags=["Order Chart"])


@router.get("/", response_model=list[OrderChartRead])
async def get_order_chart(
    filters: Annotated[OrderChartFilter, Depends()],
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: CurrentUser = Depends(get_current_user),
) -> list[OrderChartRead]:
    repo = OrderChartRepository(session)
    return await repo.get_chart(filters)


@router.get("/descriptions", response_model=list[str])
async def get_order_status_descriptions(
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: CurrentUser = Depends(get_current_user),
) -> list[str]:
    repo = OrderChartRepository(session)
    return await repo.get_unique_descriptions()


@router.get("/courier-full-names", response_model=list[str])
async def get_courier_full_names(
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: CurrentUser = Depends(get_current_user),
) -> list[str]:
    repo = OrderChartRepository(session)
    return await repo.get_unique_full_names()

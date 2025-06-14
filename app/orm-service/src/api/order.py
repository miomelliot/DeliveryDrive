# src/api/order.py
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Body, Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Order
from src.db.session import get_session
from src.dependencies.auth import get_current_user
from src.repositories.charts.order_chart import OrderChartRepository
from src.repositories.charts.order_detail_read import OrderDetailRepository
from src.repositories.order import OrderRepository
from src.schemas.auth import CurrentUser
from src.schemas.order import OrderCreateAPI
from src.schemas.order_detail_read import OrderDetailRead, OrderDetailUpdate

router = APIRouter(prefix="/order", tags=["Order"])


@router.post("/", response_model=None, status_code=201)
async def create_order(
    data: OrderCreateAPI,
    session: AsyncSession = Depends(get_session),
    current_user: CurrentUser = Depends(get_current_user),
) -> dict[str, str]:
    repo = OrderRepository(session)
    order: Order = await repo.create_order(data, current_user.id)
    return {
        "id": f"{order.id}",
        "detail": "Заказ успешно создан",
    }


@router.get("/{order_id}", response_model=OrderDetailRead)
async def get_order_detail(
    order_id: UUID = Path(..., description="ID заказа"),
    session: AsyncSession = Depends(get_session),
    current_user: CurrentUser = Depends(get_current_user),
) -> OrderDetailRead:
    repo = OrderDetailRepository(session)
    return await repo.get_detail(order_id)


@router.patch("/{order_id}")
async def update_order_detail(
    order_id: UUID = Path(..., description="ID заказа"),
    data: OrderDetailUpdate = Body(...),
    session: AsyncSession = Depends(get_session),
    current_user: CurrentUser = Depends(get_current_user),
) -> dict[str, str]:
    repo = OrderDetailRepository(session)
    await repo.update_detail(order_id, data)
    return {"status": "success"}


@router.delete("/{order_id}")
async def delete_order(
    order_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: CurrentUser = Depends(get_current_user),
) -> dict[str, str]:
    repo = OrderRepository(session)
    await repo.delete_order(order_id)
    return {"detail": f"Заказ {order_id} удалён"}


@router.get("/status", response_model=list[str])
async def get_order_status(
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: CurrentUser = Depends(get_current_user),
) -> list[str]:
    repo = OrderChartRepository(session)
    return await repo.get_unique_descriptions()


@router.get("/courier-name", response_model=list[str])
async def get_courier_full_names(
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: CurrentUser = Depends(get_current_user),
) -> list[str]:
    repo = OrderChartRepository(session)
    return await repo.get_unique_full_names()

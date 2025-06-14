# src/api/order.py
from uuid import UUID

from fastapi import APIRouter, Body, Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Order
from src.dependencies.db import get_session_with_user
from src.repositories.charts.order_chart import OrderChartRepository
from src.repositories.charts.order_detail_read import OrderDetailRepository
from src.repositories.tables.order import OrderRepository
from src.schemas.order import OrderCreateAPI
from src.schemas.order_detail_read import OrderDetailRead, OrderDetailUpdate

router = APIRouter(prefix="/v2/order", tags=["Order v2"])


@router.post("/", response_model=None, status_code=201)
async def create_order(
    data: OrderCreateAPI,
    session: AsyncSession = Depends(get_session_with_user),
) -> dict[str, str]:
    order: Order = await OrderRepository().create_raw(session, data)
    return {
        "id": f"{order.id}",
        "detail": "Заказ успешно создан",
    }


@router.get("/{order_id}", response_model=OrderDetailRead)
async def get_order_detail(
    order_id: UUID = Path(..., description="ID заказа"),
    session: AsyncSession = Depends(get_session_with_user),
) -> OrderDetailRead:
    repo = OrderDetailRepository(session)
    return await repo.get_detail(order_id)


@router.patch("/{order_id}")
async def update_order_detail(
    order_id: UUID = Path(..., description="ID заказа"),
    data: OrderDetailUpdate = Body(...),
    session: AsyncSession = Depends(get_session_with_user),
) -> dict[str, str]:
    repo = OrderDetailRepository(session)
    await repo.update_detail(order_id, data)
    return {"status": "success"}


@router.delete("/{order_id}")
async def delete_order(
    order_id: UUID,
    session: AsyncSession = Depends(get_session_with_user),
) -> dict[str, str]:
    await OrderRepository().delete(session, order_id)
    return {"detail": "Заказ  удалён"}


@router.get("/status", response_model=list[str])
async def get_order_status(
    session: AsyncSession = Depends(get_session_with_user),
) -> list[str]:
    repo = OrderChartRepository(session)
    return await repo.get_unique_descriptions()


@router.get("/courier-name", response_model=list[str])
async def get_courier_full_names(
    session: AsyncSession = Depends(get_session_with_user),
) -> list[str]:
    repo = OrderChartRepository(session)
    return await repo.get_unique_full_names()

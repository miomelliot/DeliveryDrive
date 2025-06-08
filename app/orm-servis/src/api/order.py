# src/api/order.py
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Order
from src.db.session import get_session
from src.repositories.order import OrderRepository
from src.schemas.order import OrderCreate

router = APIRouter(prefix="/order", tags=["Order"])


@router.post("/", response_model=None, status_code=201)
async def create_order(
    data: OrderCreate,
    session: AsyncSession = Depends(get_session),
) -> dict[str, str]:
    repo = OrderRepository(session)

    try:
        order: Order = await repo.create_order(data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    return {"detail": f"Заказ {order.id} успешно создан"}


@router.delete("/{order_id}")
async def delete_order(
    order_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> dict[str, str]:
    repo = OrderRepository(session)

    await repo.delete_order(order_id)
    return {"detail": f"Заказ {order_id} удалён"}

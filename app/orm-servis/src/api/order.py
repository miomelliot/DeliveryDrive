# src/api/order.py
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Order
from src.db.session import get_session
from src.repositories.order import OrderRepository
from src.schemas.order import OrderCreate
from src.utils.http_error import _raise_400

router = APIRouter(prefix="/order", tags=["Order"])


@router.post("/", response_model=None, status_code=201)
async def create_order(
    data: OrderCreate,
    session: AsyncSession = Depends(get_session),
) -> dict[str, str]:
    repo = OrderRepository(session)
    try:
        order: Order = await repo.create_order(data)
        return {
            "id": f"{order.id}",
            "detail": "Заказ успешно создан",
        }
    except ValueError as e:
        _raise_400(e)


@router.delete("/{order_id}")
async def delete_order(
    order_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> dict[str, str]:
    repo = OrderRepository(session)
    try:
        await repo.delete_order(order_id)
        return {"detail": f"Заказ {order_id} удалён"}
    except ValueError as e:
        _raise_400(e)

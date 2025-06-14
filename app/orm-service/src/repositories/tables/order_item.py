# src/schemas/OrderItem_item.py
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import OrderItem
from src.repositories.tables.base import CRUDRepository
from src.schemas.order_item import OrderItemCreate, OrderItemUpdate


class OrderItemRepository(CRUDRepository[OrderItem, OrderItemCreate, OrderItemUpdate]):
    def __init__(self) -> None:
        super().__init__(OrderItem)

    async def create(self, session: AsyncSession, obj_in: OrderItemCreate) -> OrderItem:
        return await super().create(session, obj_in)

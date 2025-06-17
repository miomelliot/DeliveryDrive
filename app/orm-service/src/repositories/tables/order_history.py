# src/repositories/tables/order_history.py
from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import OrderHistory
from src.repositories.tables.base import CRUDRepository
from src.schemas.order_history import OrderHistoryCreate, OrderHistoryUpdate


class OrderHistoryRepository(CRUDRepository[OrderHistory, OrderHistoryCreate, OrderHistoryUpdate]):
    def __init__(self) -> None:
        super().__init__(OrderHistory)

    #  запрещённые операции -
    async def update(
        self,
        session: AsyncSession,
        db_obj: OrderHistory,
        obj_in: OrderHistoryUpdate,
    ) -> OrderHistory:
        raise NotImplementedError("Строки истории заказов являются неизменяемыми")

    async def delete(
        self,
        session: AsyncSession,
        id: UUID | int,
    ) -> None:
        raise NotImplementedError("Строки истории заказов являются неизменяемыми")

# src/repositories/tables/order_item.py
from decimal import Decimal
from typing import Tuple
from uuid import UUID

from sqlalchemy import Result, Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Equipment, HeaterType, OrderItem
from src.repositories.tables.base import CRUDRepository
from src.repositories.tables.equipment_status import EquipmentStatusRepository
from src.schemas.order_item import OrderItemCreate, OrderItemDetailed, OrderItemUpdate


class OrderItemRepository(CRUDRepository[OrderItem, OrderItemCreate, OrderItemUpdate]):
    def __init__(self) -> None:
        super().__init__(OrderItem)

    async def get_item_from_order_id(self, session: AsyncSession, order_id: UUID | int) -> list[Equipment]:
        stmt: Select[Tuple[Equipment]] = (
            select(Equipment)
            .join(OrderItem, Equipment.heater_type_id == OrderItem.heater_type_id)
            .where(OrderItem.order_id == order_id)
        )
        res: Result[Tuple[Equipment]] = await session.execute(stmt)
        return list(res.scalars().all())

    async def get_items_rented(self, session: AsyncSession, order_id: UUID) -> list[OrderItemDetailed]:
        rented_status_id: int = await EquipmentStatusRepository().get_code_id(session, "rented")

        stmt: Select[Tuple[str, str, float, float, int]] = (
            select(
                Equipment.serial_number,
                HeaterType.model,
                HeaterType.price,
                HeaterType.weight,
                OrderItem.quantity,
            )
            .join(HeaterType, HeaterType.id == Equipment.heater_type_id)
            .join(OrderItem, OrderItem.heater_type_id == HeaterType.id)
            .where(
                OrderItem.order_id == order_id,
                Equipment.equipment_status_id == rented_status_id,
            )
        )

        result: Result[Tuple[str, str, float, float, int]] = await session.execute(stmt)
        return [OrderItemDetailed(**row) for row in result.mappings().all()]

    async def get_total_amount(self, session: AsyncSession, order_id: UUID) -> Decimal:
        stmt: Select[Tuple[float]] = (
            select(func.sum(HeaterType.price * OrderItem.quantity))
            .select_from(OrderItem)
            .join(HeaterType, HeaterType.id == OrderItem.heater_type_id)
            .where(OrderItem.order_id == order_id)
        )

        total: float | None = await session.scalar(stmt)
        return Decimal(str(total or 0))

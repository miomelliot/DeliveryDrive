# src/repositories/tables/order.py

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Client, HeaterType, Order
from src.repositories.tables.base import CRUDRepository
from src.repositories.tables.client import ClientRepository
from src.repositories.tables.equipment import EquipmentRepository
from src.repositories.tables.heater_type import HeaterTypeRepository
from src.repositories.tables.invoice import InvoiceRepository
from src.repositories.tables.order_history import OrderHistoryRepository
from src.repositories.tables.order_item import OrderItemRepository
from src.repositories.tables.order_status import OrderStatusRepository
from src.schemas.order import OrderCreate, OrderCreateAPI, OrderUpdate
from src.schemas.order_history import OrderHistoryCreate
from src.schemas.order_item import OrderItemCreate


class OrderRepository(CRUDRepository[Order, OrderCreate, OrderUpdate]):
    def __init__(self) -> None:
        super().__init__(Order)

    async def create_raw(self, session: AsyncSession, raw_data: OrderCreateAPI) -> Order:
        client: Client = await ClientRepository().create_raw(session, raw_data)
        status_id: int = await OrderStatusRepository().get_id(session, "new")

        obj_in = OrderCreate(
            client_id=client.id,
            window_start=raw_data.window_start,
            window_end=raw_data.window_end,
            rent_start=raw_data.rent_start,
            rent_end=raw_data.rent_end,
            status_id=status_id,
            comment=raw_data.comment,
        )
        order: Order = await super().create(session, obj_in)

        for eq in raw_data.equipment:
            heater_type: HeaterType = await HeaterTypeRepository().get_all(session, eq.model)

            await EquipmentRepository().update_status_bulk(
                session=session,
                heater_type_id=heater_type.id,
                old_status_code="available",
                new_status_code="rented",
                limit=eq.quantity,
                model=heater_type.model,
            )

            await OrderItemRepository().create(
                session,
                OrderItemCreate(
                    order_id=order.id,
                    heater_type_id=heater_type.id,
                    quantity=eq.quantity,
                ),
            )

        await InvoiceRepository().create_from_order(session, order.id)

        return order

    async def update_status(
        self,
        session: AsyncSession,
        order_id: UUID,
        new_status_code: str,
    ) -> Order:
        order = await self.get(session, order_id)
        new_status_id = await self._repo(OrderStatusRepository).get_id(session, new_status_code)

        if order.status_id == new_status_id:
            return order

        prev_status_id = order.status_id
        order.status_id = new_status_id
        await session.flush()
        await session.refresh(order)

        await self._repo(OrderHistoryRepository).create(
            session,
            OrderHistoryCreate(
                order_id=order.id,
                previous_status_id=prev_status_id,
                new_status_id=new_status_id,
                user_id=self._user_id,
            ),
        )
        return order

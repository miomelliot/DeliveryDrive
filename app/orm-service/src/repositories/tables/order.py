# src/repositories/tables/order.py
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Client, Order
from src.repositories.tables.base import CRUDRepository
from src.repositories.tables.client import ClientRepository
from src.repositories.tables.heater_type import HeaterTypeRepository
from src.repositories.tables.order_item import OrderItemRepository
from src.repositories.tables.order_status import OrderStatusRepository
from src.schemas.order import OrderCreate, OrderCreateAPI, OrderUpdate
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

        for equip in raw_data.equipment:
            heater_type_id: int = await HeaterTypeRepository().get_id(session, equip.model)
            await OrderItemRepository().create(
                session,
                OrderItemCreate(
                    order_id=order.id,
                    heater_type_id=heater_type_id,
                    quantity=equip.quantity,
                ),
            )

        return order

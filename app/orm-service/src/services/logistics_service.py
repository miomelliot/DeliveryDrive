# src/services/logistics_service.py
from datetime import time as dt_time
from typing import Literal, Sequence, Tuple
from uuid import UUID

from loguru import logger
from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from src.db.models import (
    Address,
    Client,
    CourierSchedule,
    Order,
    OrderItem,
    Transport,
    User,
    Warehouse,
)
from src.schemas.logistics import (
    AddressRead,
    CreateSchema,
    Logistics,
    OrderSchema,
)
from src.schemas.logistics import (
    TransportType as TransportTypeSchema,
)
from src.utils.http_error import NotFoundError

DEFAULT_SERVICE_DURATION_SEC = 1_500  # ~25 минут
DEFAULT_COURIER_START: dt_time = dt_time(9)  # 09:00
DEFAULT_COURIER_END: dt_time = dt_time(18)  # 18:00


async def build_logistics(
    session: AsyncSession,
    order_ids: Sequence[UUID],
) -> Logistics:
    stmt_orders: Select[Tuple[Order]] = (
        select(Order)
        .where(Order.id.in_(order_ids))
        .options(
            joinedload(Order.client).joinedload(Client.address),
            selectinload(Order.items).joinedload(OrderItem.heater_type),
        )
    )
    orders_db: Sequence[Order] = (await session.scalars(stmt_orders)).all()
    if len(orders_db) != len(order_ids):
        missing: set[UUID] = set(order_ids) - {o.id for o in orders_db}
        raise ValueError(f"Orders not found: {', '.join(map(str, missing))}")

    orders: list[OrderSchema] = []
    for order in orders_db:
        addr: Address = order.client.address
        if addr is None:
            raise NotFoundError(f"Order {order.id} has no address")

        weight: float | Literal[0] = sum(item.quantity * item.heater_type.weight for item in order.items)

        orders.append(
            OrderSchema(
                order_id=order.id,
                address=AddressRead(
                    id=addr.id,
                    city=addr.city,
                    street=addr.street,
                    building=addr.building,
                    lat=addr.lat,
                    lon=addr.lon,
                ),
                weight=weight,
                service_duration=DEFAULT_SERVICE_DURATION_SEC,
                time_window=[order.window_start, order.window_end],
            )
        )

    warehouse_db: Warehouse | None = await session.scalar(
        select(Warehouse).options(joinedload(Warehouse.address)).limit(1)
    )
    if warehouse_db is None:
        raise NotFoundError("Склад не найден")

    warehouse = AddressRead(
        id=warehouse_db.address.id,
        city=warehouse_db.address.city,
        street=warehouse_db.address.street,
        building=warehouse_db.address.building,
        lat=warehouse_db.address.lat,
        lon=warehouse_db.address.lon,
    )

    stmt_transports: Select[Tuple[Transport]] = (
        select(Transport)
        .options(
            joinedload(Transport.transport_type),
            selectinload(Transport.courier).joinedload(User.schedules),
        )
        .order_by(Transport.id)
    )
    transports_db: Sequence[Transport] = (await session.scalars(stmt_transports)).all()

    creates: list[CreateSchema] = []
    for t in transports_db:
        schedule: CourierSchedule | None = next(iter(t.courier.schedules), None)

        creates.append(
            CreateSchema(
                courier_id=t.courier_id,
                time_window=[
                    schedule.start_time if schedule else DEFAULT_COURIER_START,
                    schedule.end_time if schedule else DEFAULT_COURIER_END,
                ],
                transport_type=TransportTypeSchema(
                    name=t.transport_type.name,
                    avg_speed=t.transport_type.avg_speed,
                    capacity=t.transport_type.capacity,
                ),
            )
        )

    return Logistics(
        warehouse=warehouse,
        orders=orders,
        creates=creates,
    )

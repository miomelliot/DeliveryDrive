from datetime import date, time
from typing import Sequence, Tuple
from uuid import UUID

from sqlalchemy import Result, Select, func, select
from sqlalchemy.engine.row import Row
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Address, Client, Order, OrderStatus, RoutingSelection
from src.schemas.routing_selection_chart import RoutingSelectionFilter, RoutingSelectionRead


class RoutingSelectionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session: AsyncSession = session

    async def get_chart(self, filters: RoutingSelectionFilter) -> list[RoutingSelectionRead]:
        stmt: Select[Tuple[UUID, date, date, time, time, str, str, str | None, str, str]] = (
            select(
                Order.id,
                Order.rent_start,
                Order.rent_end,
                Order.window_start,
                Order.window_end,
                Client.phone,
                Address.city,
                Address.street,
                Address.building,
                OrderStatus.description,
            )
            .join(RoutingSelection, RoutingSelection.order_id == Order.id)
            .join(Client, Client.id == Order.client_id)
            .join(Address, Address.id == Client.address_id)
            .join(OrderStatus, OrderStatus.id == Order.status_id)
        )

        if filters.search:
            like: str = f"%{filters.search.lower()}%"
            stmt = stmt.where(
                func.lower(Client.phone).like(like)
                | func.lower(Address.city).like(like)
                | func.lower(Address.street).like(like)
                | func.lower(Address.building).like(like)
                | func.lower(OrderStatus.description).like(like)
            )

        if filters.description:
            stmt = stmt.where(OrderStatus.description == filters.description)

        # Фильтры по имени курьера игнорируются — их нет в этой модели

        if filters.window_start_from:
            stmt = stmt.where(Order.window_start >= filters.window_start_from)
        if filters.window_end_to:
            stmt = stmt.where(Order.window_end <= filters.window_end_to)

        if filters.only_active:
            stmt = stmt.where(~OrderStatus.code.in_(["completed", "cancelled"]))

        field_map = {
            "id": Order.id,
            "rent_start": Order.rent_start,
            "rent_end": Order.rent_end,
            "window_start": Order.window_start,
            "window_end": Order.window_end,
            "phone": Client.phone,
            "city": Address.city,
            "street": Address.street,
            "building": Address.building,
            "description": OrderStatus.description,
        }

        order_column = field_map.get(filters.order_by, Order.id)
        stmt = stmt.order_by(order_column.desc() if filters.order_dir == "desc" else order_column.asc())
        stmt = stmt.limit(filters.limit).offset(filters.offset)

        result: Result[
            Tuple[UUID, date, date, time, time, str, str, str | None, str, str]
        ] = await self.session.execute(stmt)
        rows: Sequence[Row[Tuple[UUID, date, date, time, time, str, str, str | None, str, str]]] = result.fetchall()

        return [RoutingSelectionRead.model_validate(row._asdict()) for row in rows]

# src/repositories/routing_chart.py
from datetime import date, time
from typing import Any, Sequence, Tuple
from uuid import UUID

from sqlalchemy import Function, Result, func, select
from sqlalchemy.engine.row import Row
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from schemas.routing_chart import RoutingChartFilter, RoutingChartRead
from src.db.models import Address, Client, Order, OrderStatus


class RoutingChartRepository:
    """Читает данные заказов по списку UUID-ов (из Redis)."""

    def __init__(self, session: AsyncSession) -> None:
        self.session: AsyncSession = session

    async def get_chart(
        self,
        filters: RoutingChartFilter,
    ) -> list[RoutingChartRead]:
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
            .join(Client, Client.id == Order.client_id)
            .join(Address, Address.id == Client.address_id)
            .join(OrderStatus, OrderStatus.id == Order.status_id)
        )

        # 🔍 Поиск
        if filters.search:
            like: str = f"%{filters.search.lower()}%"
            full_addr: Function[Any] = func.lower(
                func.concat_ws(
                    ", ",
                    func.coalesce(Address.city, ""),
                    func.coalesce(Address.street, ""),
                    func.coalesce(Address.building, ""),
                )
            )
            stmt = stmt.where(
                func.lower(Client.phone).like(like)
                | func.lower(OrderStatus.description).like(like)
                | full_addr.like(like)
            )

        # 📋 Выпадающие фильтры
        if filters.description:
            stmt = stmt.where(OrderStatus.description == filters.description)

        # 🕒 Временные рамки
        if filters.window_start_from:
            stmt = stmt.where(Order.window_start >= filters.window_start_from)
        if filters.window_end_to:
            stmt = stmt.where(Order.window_end <= filters.window_end_to)
        if filters.only_active:
            stmt = stmt.where(~OrderStatus.code.in_(["completed", "cancelled"]))

        # --- сортировка ---
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
        col = field_map.get(filters.order_by, Order.id)
        stmt = stmt.order_by(col.desc() if filters.order_dir == "desc" else col.asc())
        stmt = stmt.limit(filters.limit).offset(filters.offset)

        # --- выполнение ---
        res: Result[Tuple[UUID, date, date, time, time, str, str, str | None, str, str]] = await self.session.execute(
            stmt
        )
        rows: Sequence[Row[Tuple[UUID, date, date, time, time, str, str, str | None, str, str]]] = res.fetchall()
        return [RoutingChartRead.model_validate(r._asdict()) for r in rows]

    async def get_unique_descriptions(self) -> list[str]:
        stmt: Select[Tuple[str]] = select(func.distinct(OrderStatus.description)).order_by(OrderStatus.description)
        result: Result[Tuple[str]] = await self.session.execute(stmt)
        return [row[0] for row in result.all() if row[0]]

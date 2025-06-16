# src/repositories/routing_chart.py
from datetime import date, time
from typing import Sequence, Tuple
from uuid import UUID

from sqlalchemy import Result, func, select
from sqlalchemy.engine.row import Row
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from src.db.models import Address, Client, Order, OrderStatus, RouteItem
from src.schemas.routing_chart import RoutingChartFilter, RoutingChartRead
from src.utils.formatters import format_time_range
from src.utils.sqlalchemy_expr import location_expr


class RoutingChartRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session: AsyncSession = session

    async def get_chart(self, filters: RoutingChartFilter) -> list[RoutingChartRead]:
        stmt: Select[Tuple[UUID, date, date, time, time, str, str, str]] = (
            select(
                Order.id,
                Order.rent_start,
                Order.rent_end,
                Order.window_start,
                Order.window_end,
                Client.phone,
                location_expr().label("location"),
                OrderStatus.description,
            )
            .join(Client, Client.id == Order.client_id)
            .join(Address, Address.id == Client.address_id)
            .join(OrderStatus, OrderStatus.id == Order.status_id)
        )

        if filters.route_id:
            stmt = stmt.join(RouteItem, RouteItem.order_id == Order.id)
            stmt = stmt.where(RouteItem.route_id == filters.route_id)

        if filters.search:
            like: str = f"%{filters.search.lower()}%"
            stmt = stmt.where(
                func.lower(Client.phone).like(like)
                | func.lower(OrderStatus.description).like(like)
                | func.lower(location_expr()).like(like)
            )

        if filters.description:
            stmt = stmt.where(OrderStatus.description == filters.description)

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
            "location": location_expr(),
            "description": OrderStatus.description,
        }
        sort_col = field_map.get(filters.order_by, Order.id)
        stmt = stmt.order_by(sort_col.desc() if filters.order_dir == "desc" else sort_col.asc())

        stmt = stmt.limit(filters.limit).offset(filters.offset)

        res: Result[Tuple[UUID, date, date, time, time, str, str, str]] = await self.session.execute(stmt)
        rows: Sequence[Row[Tuple[UUID, date, date, time, time, str, str, str]]] = res.fetchall()

        # 🔄 Преобразуем к нужному виду (с window)
        return [
            RoutingChartRead(
                id=r[0],
                rent_start=r[1],
                rent_end=r[2],
                window=format_time_range(r[3], r[4]),
                phone=r[5],
                location=r[6],
                description=r[7],
            )
            for r in rows
        ]

    async def get_unique_descriptions(self) -> list[str]:
        stmt: Select[Tuple[str]] = select(func.distinct(OrderStatus.description)).order_by(OrderStatus.description)
        result: Result[Tuple[str]] = await self.session.execute(stmt)
        return [row[0] for row in result.all() if row[0]]

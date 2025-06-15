# src/repositories/order_chart.py
from datetime import date, datetime, time
from typing import Any, Sequence, Tuple
from uuid import UUID

from sqlalchemy import Function, Result, Select, func, select
from sqlalchemy.engine.row import Row
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Address, Client, Order, OrderStatus, Route, RouteItem, User
from src.schemas.order_chart import OrderChartFilter, OrderChartRead
from src.utils.formatters import format_time_range
from src.utils.sqlalchemy_expr import full_name_expr, location_expr


class OrderChartRepository:
    async def get_chart(self, session: AsyncSession, filters: OrderChartFilter) -> list[OrderChartRead]:
        stmt: Select[Tuple[UUID, datetime, date, date, time, time, str, str, str, str]] = (
            select(
                Order.id,
                Order.created_at,
                Order.rent_start,
                Order.rent_end,
                Order.window_start,
                Order.window_end,
                Client.phone,
                location_expr().label("location"),
                OrderStatus.description.label("status"),
                full_name_expr().label("full_name"),
            )
            .join(Client, Client.id == Order.client_id)
            .join(Address, Address.id == Client.address_id)
            .join(OrderStatus, OrderStatus.id == Order.status_id)
            .outerjoin(RouteItem, RouteItem.order_id == Order.id)
            .outerjoin(Route, Route.id == RouteItem.route_id)
            .outerjoin(User, User.id == Route.courier_id)
        )

        if filters.search:
            like: str = f"%{filters.search.lower()}%"
            full_name: Function[Any] = func.lower(full_name_expr())
            stmt = stmt.where(
                func.lower(Client.phone).like(like) | func.lower(location_expr()).like(like) | full_name.like(like)
            )

        if filters.status:
            stmt = stmt.where(OrderStatus.description == filters.status)

        if filters.window_start_from:
            stmt = stmt.where(Order.window_start >= filters.window_start_from)
        if filters.window_end_to:
            stmt = stmt.where(Order.window_end <= filters.window_end_to)

        if filters.only_active:
            stmt = stmt.where(~OrderStatus.code.in_(["completed", "cancelled"]))

        field_map = {
            "id": Order.id,
            "created_at": Order.created_at,
            "rent_start": Order.rent_start,
            "rent_end": Order.rent_end,
            "phone": Client.phone,
            "location": location_expr(),
            "status": OrderStatus.description,
            "full_name": full_name_expr(),
        }
        col = field_map.get(filters.order_by, Order.id)
        stmt = stmt.order_by(col.desc() if filters.order_dir == "desc" else col.asc())
        stmt = stmt.limit(filters.limit).offset(filters.offset)

        result: Result[Tuple[UUID, datetime, date, date, time, time, str, str, str, str]] = await session.execute(stmt)
        rows: Sequence[Row[Tuple[UUID, datetime, date, date, time, time, str, str, str, str]]] = result.fetchall()

        return [
            OrderChartRead(
                id=r.id,
                created_at=r.created_at,
                rent_start=r.rent_start,
                rent_end=r.rent_end,
                window=format_time_range(r.window_start, r.window_end),
                phone=r.phone,
                location=r.location,
                status=r.status,
                full_name=r.full_name if r.full_name else None,
            )
            for r in rows
        ]

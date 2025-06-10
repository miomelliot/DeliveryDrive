# src/repositories/route_chart.py
from datetime import date
from typing import Sequence, Tuple
from uuid import UUID

from sqlalchemy import Result, func, select
from sqlalchemy.engine.row import Row
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from src.db.models import (
    EventType,
    Order,
    Route,
    RouteItem,
    Tracking,
    User,
)
from src.schemas.route_chart import RouteChart, RouteChartFilter
from src.utils.sqlalchemy_expr import full_name_expr


class RouteChartRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session: AsyncSession = session

    async def get_chart(self, filters: RouteChartFilter) -> list[RouteChart]:
        stmt: Select[Tuple[UUID, date, str, int, int]] = (
            select(
                Route.id,
                Route.date,
                full_name_expr().label("full_name"),
                func.count(RouteItem.id).label("count_orders"),
                func.count(
                    func.distinct(
                        func.case(
                            (
                                EventType.code.in_(["installed", "picked_up"]),
                                Tracking.route_item_id,
                            ),
                            else_=None,
                        )
                    )
                ).label("completed_orders"),
            )
            .join(User, User.id == Route.courier_id)
            .join(RouteItem, RouteItem.route_id == Route.id)
            .join(Order, Order.id == RouteItem.order_id)
            .outerjoin(Tracking, Tracking.route_item_id == RouteItem.id)
            .outerjoin(EventType, EventType.id == Tracking.event_type_id)
            .group_by(Route.id, Route.date, User.first_name, User.last_name)
        )

        # 🔍 Поиск по имени
        if filters.search:
            like: str = f"%{filters.search.lower()}%"
            stmt = stmt.where(func.lower(full_name_expr()).like(like))

        # ⏱️ Фильтрация по дате
        if filters.date_start:
            stmt = stmt.where(Route.date >= filters.date_start)
        if filters.date_end:
            stmt = stmt.where(Route.date <= filters.date_end)

        # ↕️ Сортировка
        field_map = {
            "id": Route.id,
            "date": Route.date,
            "full_name": full_name_expr(),
            "count_orders": func.count(RouteItem.id),
        }
        sort_col = field_map.get(filters.order_by, Route.id)
        stmt = stmt.order_by(sort_col.desc() if filters.order_dir == "desc" else sort_col.asc())

        stmt = stmt.limit(filters.limit).offset(filters.offset)

        # 🧾 Выполнение
        res: Result[Tuple[UUID, date, str, int, int]] = await self.session.execute(stmt)
        rows: Sequence[Row[Tuple[UUID, date, str, int, int]]] = res.fetchall()

        # 📦 Преобразование в Pydantic
        return [
            RouteChart(
                id=r[0],
                date=r[1],
                full_name=r[2],
                count_orders=r[3],
                status=round((r[4] or 0) / (r[3] or 1) * 100),  # safe division
            )
            for r in rows
        ]

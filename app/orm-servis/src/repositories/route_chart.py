# src/repositories/route_chart.py
from datetime import date
from typing import Any, Literal, Sequence, Tuple
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


class RouteChartRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session: AsyncSession = session

    async def get_chart(self, filters: RouteChartFilter) -> list[RouteChart]:
        stmt: Select[Tuple[UUID, date, str, int, int]] = (
            select(
                Route.id,
                Route.date,
                func.concat_ws(" ", User.first_name, User.last_name).label("full_name"),
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
            stmt = stmt.where(func.lower(func.concat_ws(" ", User.first_name, User.last_name)).like(like))

        # ⏱️ Фильтрация по дате
        if filters.date_start:
            stmt = stmt.where(Route.date >= filters.date_start)
        if filters.date_end:
            stmt = stmt.where(Route.date <= filters.date_end)

        # ↕️ Сортировка
        field_map = {
            "id": Route.id,
            "date": Route.date,
            "full_name": func.concat_ws(" ", User.first_name, User.last_name),
            "count_orders": func.count(RouteItem.id),
        }
        sort_col = field_map.get(filters.order_by, Route.id)
        stmt = stmt.order_by(sort_col.desc() if filters.order_dir == "desc" else sort_col.asc())

        stmt = stmt.limit(filters.limit).offset(filters.offset)

        # 🧾 Выполнение
        res: Result[Tuple[UUID, date, str, int, int]] = await self.session.execute(stmt)
        rows: Sequence[Row[Tuple[UUID, date, str, int, int]]] = res.fetchall()

        # 📦 Преобразование в Pydantic
        result: list[RouteChart] = []
        for row in rows:
            completed: Any | Literal[0] = row.completed_orders or 0
            total: Any | Literal[1] = row.count_orders or 1  # защита от деления на 0
            percent: int = round(completed / total * 100)

            result.append(
                RouteChart(
                    id=row.id,
                    date=row.date,
                    full_name=row.full_name,
                    count_orders=row.count_orders,
                    status=percent,
                )
            )

        return result

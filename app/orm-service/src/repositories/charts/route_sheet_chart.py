# src/repositories/charts/route_sheet_chart.py
from typing import Sequence, Tuple
from uuid import UUID

from sqlalchemy import Result, case, func, select
from sqlalchemy.engine.row import Row
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from src.db.models import EventType, Order, Route, RouteItem, Tracking, User
from src.schemas.route_sheet_chart import RouteSheetChart, RouteSheetChartFilter
from src.utils.sqlalchemy_expr import full_name_expr


class RouteSheetChartRepository:
    async def get_chart(self, session: AsyncSession, filters: RouteSheetChartFilter) -> list[RouteSheetChart]:
        stmt: Select[Tuple[UUID, str, int, int]] = (
            select(
                Route.id,
                full_name_expr().label("full_name"),
                func.count(RouteItem.id).label("count_orders"),
                func.count(
                    func.distinct(
                        case(
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
            .group_by(Route.id, User.first_name, User.last_name)
        )

        if filters.search:
            like = f"%{filters.search.lower()}%"
            stmt = stmt.where(func.lower(full_name_expr()).like(like))

        field_map = {
            "id": Route.id,
            "full_name": full_name_expr(),
            "count_orders": func.count(RouteItem.id),
        }
        sort_col = field_map.get(filters.order_by, Route.id)
        stmt = stmt.order_by(sort_col.desc() if filters.order_dir == "desc" else sort_col.asc())

        stmt = stmt.limit(filters.limit).offset(filters.offset)

        res: Result[Tuple[UUID, str, int, int]] = await session.execute(stmt)
        rows: Sequence[Row[Tuple[UUID, str, int, int]]] = res.fetchall()

        return [
            RouteSheetChart(
                id=r[0],
                full_name=r[1],
                count_orders=r[2],
                status=round((r[3] or 0) / (r[2] or 1) * 100),
            )
            for r in rows
        ]

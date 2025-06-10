# src/repositories/tracking_chart.py
from typing import Tuple
from uuid import UUID

from sqlalchemy import Result, Row, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from src.db.models import Route, User
from src.repositories.routing_chart import RoutingChartRepository
from src.schemas.routing_chart import RoutingChartFilter, RoutingChartRead
from src.schemas.tracking_chart import TrackingChart
from src.utils.sqlalchemy_expr import full_name_expr


class TrackingChartRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session: AsyncSession = session
        self.routing_repo = RoutingChartRepository(session)

    async def get_chart(
        self,
        route_id: UUID,
        filters: RoutingChartFilter,
    ) -> TrackingChart:
        # 🔎 Получаем имя курьера по route_id
        route_stmt: Select[Tuple[UUID, str]] = (
            select(
                Route.id,
                full_name_expr().label("full_name"),
            )
            .join(User, User.id == Route.courier_id)
            .where(Route.id == route_id)
        )

        res: Result[Tuple[UUID, str]] = await self.session.execute(route_stmt)
        row: Row[Tuple[UUID, str]] | None = res.first()
        if row is None:
            raise ValueError(f"Route with id={route_id} not found")

        # 📦 Применяем фильтр по маршруту и получаем заказы через RoutingChartRepository
        filters.route_id = route_id
        orders: list[RoutingChartRead] = list(await self.routing_repo.get_chart(filters))

        return TrackingChart(
            route_id=route_id,
            full_name=row.full_name,
            orders=orders,
        )

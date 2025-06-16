from datetime import date
from typing import Tuple
from uuid import UUID

from sqlalchemy import Result, and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from src.db.models import EventType, Route, RouteItem, Tracking
from src.repositories.tables.order import OrderRepository
from src.schemas.order_detail_read import OrderDetailRead
from src.schemas.route import RouteItemStatus, RouteRead
from src.utils.http_error import NotFoundError


class RouteRepository:
    async def list_by_courier(self, session: AsyncSession, courier_id: UUID) -> RouteRead:
        stmt: Select[Tuple[Route]] = select(Route).where(
            and_(
                Route.courier_id == courier_id,
                Route.date == date.today(),
            )
        )
        res: Result[Tuple[Route]] = await session.execute(stmt)
        routes: Route | None = res.scalars().first()
        if routes is None:
            NotFoundError("Маршрутный лист не найден")
        return RouteRead.model_validate(routes)

    async def list_items_with_status(self, session: AsyncSession, route_id: UUID) -> list[RouteItemStatus]:
        last_evt = (
            select(
                Tracking.route_item_id,
                func.max(Tracking.event_time).label("last_time"),
            )
            .group_by(Tracking.route_item_id)
            .subquery()
        )

        stmt = (
            select(
                RouteItem.id,
                RouteItem.order_id,
                RouteItem.sequence,
                EventType.description,
            )
            .select_from(RouteItem)
            .where(RouteItem.route_id == route_id)
            .outerjoin(last_evt, last_evt.c.route_item_id == RouteItem.id)
            .outerjoin(
                Tracking,
                (Tracking.route_item_id == RouteItem.id) & (Tracking.event_time == last_evt.c.last_time),
            )
            .outerjoin(EventType, EventType.id == Tracking.event_type_id)
            .order_by(RouteItem.sequence)
        )

        res = await session.execute(stmt)
        rows = res.fetchall()

        order_repo = OrderRepository()

        result = []
        for route_item_id, order_id, sequence, status in rows:
            order: OrderDetailRead = await order_repo.get_detail(session, order_id)
            result.append(
                RouteItemStatus(
                    id=route_item_id,
                    order=order,
                    sequence=sequence,
                    status=status,
                )
            )

        return result

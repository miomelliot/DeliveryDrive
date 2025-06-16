from typing import Sequence, Tuple
from uuid import UUID

from sqlalchemy import Result, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from src.db.models import EventType, Route, RouteItem, Tracking
from src.schemas.route import RouteItemStatus, RouteRead


class RouteRepository:
    async def list_by_courier(self, session: AsyncSession, courier_id: UUID) -> list[RouteRead]:
        stmt: Select[Tuple[Route]] = select(Route).where(Route.courier_id == courier_id).order_by(Route.date.desc())
        res: Result[Tuple[Route]] = await session.execute(stmt)
        routes: Sequence[Route] = res.scalars().all()
        return [RouteRead.model_validate(r) for r in routes]

    async def list_items_with_status(self, session: AsyncSession, route_id: UUID) -> list[RouteItemStatus]:
        last_evt = (
            select(
                Tracking.route_item_id,
                func.max(Tracking.event_time).label("last_time"),
            )
            .group_by(Tracking.route_item_id)
            .subquery()
        )

        stmt: Select[Tuple[UUID, UUID | None, int, str | None]] = (
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

        res: Result[Tuple[UUID, UUID | None, int, str | None]] = await session.execute(stmt)
        rows: Sequence[Tuple[UUID, UUID | None, int, str | None]] = res.fetchall()
        return [RouteItemStatus(id=r[0], order_id=r[1], sequence=r[2], status=r[3]) for r in rows]

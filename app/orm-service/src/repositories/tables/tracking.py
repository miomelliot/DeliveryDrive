from typing import Tuple
from uuid import UUID

from sqlalchemy import Result, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from src.db.models import EventType, RouteItem, Tracking
from src.repositories.tables.base import CRUDRepository
from src.schemas.tracking import TrackingCreate, TrackingUpdate


class TrackingRepository(CRUDRepository[Tracking, TrackingCreate, TrackingUpdate]):
    def __init__(self) -> None:
        super().__init__(Tracking)

    async def create_raw(self, session: AsyncSession, obj_in: TrackingCreate) -> Tracking:
        return await super().create(session, obj_in)

    async def get_last_event_description(self, session: AsyncSession, route_id: UUID) -> str | None:
        stmt: Select[Tuple[str]] = (
            select(EventType.description)
            .select_from(Tracking)
            .join(RouteItem, RouteItem.id == Tracking.route_item_id)
            .join(EventType, EventType.id == Tracking.event_type_id)
            .where(RouteItem.route_id == route_id)
            .order_by(Tracking.event_time.desc())
            .limit(1)
        )
        res: Result[Tuple[str]] = await session.execute(stmt)
        return res.scalars().first()

from datetime import datetime, timezone
from typing import Tuple
from uuid import UUID

from sqlalchemy import Result, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from src.db.models import EventType, RouteItem, Tracking
from src.repositories.tables.base import CRUDRepository
from src.repositories.tables.event_type import EventTypeRepository
from src.repositories.tables.order import OrderRepository
from src.schemas.tracking import TrackingCreate, TrackingCreateAPI, TrackingUpdate


class TrackingRepository(CRUDRepository[Tracking, TrackingCreate, TrackingUpdate]):
    def __init__(self) -> None:
        super().__init__(Tracking)

    async def create_raw(self, session: AsyncSession, raw_data: TrackingCreateAPI) -> Tracking:
        event_type_id: int = await EventTypeRepository().get_description_id(session, raw_data.event_type)
        obj_in = TrackingCreate(
            route_item_id=raw_data.route_item_id,
            event_type_id=event_type_id,
            event_time=datetime.now(tz=timezone.utc),
        )
        tracking: Tracking = await super().create(session, obj_in)

        status_map: dict[str, str] = {
            "Выезд": "on_delivery",
            "Прибытие": "on_delivery",
            "Монтаж завершён": "in_rent",
            "Демонтаж завершён": "completed",
        }
        new_status: str | None = status_map.get(raw_data.event_type)
        if new_status:
            route_item: RouteItem | None = await session.get(RouteItem, raw_data.route_item_id)
            if route_item and route_item.order_id:
                await OrderRepository().update_status(session, route_item.order_id, new_status)

        return tracking

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

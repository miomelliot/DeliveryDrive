from uuid import UUID

from sqlalchemy import Result, Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import EventType, RouteItem, Tracking
from src.repositories.tables.base import CRUDRepository
from src.schemas.tracking import TrackingCreate, TrackingUpdate


class TrackingRepository(CRUDRepository[Tracking, TrackingCreate, TrackingUpdate]):
    def __init__(self) -> None:
        super().__init__(Tracking)

    async def get_last_event_description(
        self, session: AsyncSession, order_id: UUID
    ) -> str | None:
        stmt: Select[tuple[str]] = (
            select(EventType.description)
            .select_from(Tracking)
            .join(RouteItem, RouteItem.id == Tracking.route_item_id)
            .join(EventType, EventType.id == Tracking.event_type_id)
            .where(RouteItem.order_id == order_id)
            .order_by(Tracking.event_time.desc())
            .limit(1)
        )
        res: Result[tuple[str]] = await session.execute(stmt)
        return res.scalars().first()

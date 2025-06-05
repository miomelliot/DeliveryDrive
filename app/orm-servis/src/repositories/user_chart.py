from datetime import time
from typing import Sequence, Tuple
from uuid import UUID

from sqlalchemy import Result, Select, func, select
from sqlalchemy.engine.row import Row
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import CourierSchedule, Transport, TransportType, User
from src.schemas.user_chart import UserChartFilter, UserChartRead


class UserChartRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session: AsyncSession = session

    async def get_chart(self, filters: UserChartFilter) -> list[UserChartRead]:
        stmt: Select[tuple[UUID, str, str | None, str, str, str, time, time]] = (
            select(
                User.id,
                User.first_name,
                User.last_name,
                User.phone,
                User.email,
                TransportType.name.label("transport_name"),
                CourierSchedule.start_time,
                CourierSchedule.end_time,
            )
            .join(Transport, Transport.courier_id == User.id)
            .join(CourierSchedule, CourierSchedule.courier_id == User.id)
            .join(TransportType, TransportType.id == Transport.transport_type_id)
        )

        if filters.search:
            search_like: str = f"%{filters.search.lower()}%"
            stmt = stmt.where(
                func.lower(User.first_name).like(search_like)
                | func.lower(User.last_name).like(search_like)
                | func.lower(User.phone).like(search_like)
                | func.lower(User.email).like(search_like)
                | func.lower(TransportType.name).like(search_like)
            )

        # Маппинг строковых имён в реальные поля
        field_map = {
            "id": User.id,
            "first_name": User.first_name,
            "last_name": User.last_name,
            "phone": User.phone,
            "email": User.email,
            "transport_name": TransportType.name,
            "start_time": CourierSchedule.start_time,
            "end_time": CourierSchedule.end_time,
        }

        order_field = field_map.get(filters.order_by, User.first_name)
        if filters.order_dir == "desc":
            stmt = stmt.order_by(order_field.desc())
        else:
            stmt = stmt.order_by(order_field.asc())

        stmt = stmt.limit(filters.limit).offset(filters.offset)

        result: Result[Tuple[UUID, str, str | None, str, str, str, time, time]] = await self.session.execute(stmt)
        rows: Sequence[Row[Tuple[UUID, str, str | None, str, str, str, time, time]]] = result.fetchall()

        return [UserChartRead.model_validate(row._asdict()) for row in rows]

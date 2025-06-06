# src/repositories/user_chart.py
from datetime import time
from typing import Any, Sequence, Tuple
from uuid import UUID

from sqlalchemy import Label, Result, Select, func, select
from sqlalchemy.engine.row import Row
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import CourierSchedule, Transport, TransportType, User
from src.schemas.user_chart import UserChartFilter, UserChartRead


class UserChartRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session: AsyncSession = session

    async def get_chart(self, filters: UserChartFilter) -> list[UserChartRead]:
        full_name_expr: Label[Any] = func.concat_ws(" ", User.first_name, User.last_name).label("full_name")

        stmt: Select[Tuple[UUID, str, str, str, str, time, time]] = (
            select(
                User.id,
                full_name_expr,
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

        # 🔍 Поиск
        if filters.search:
            search_like = f"%{filters.search.lower()}%"
            stmt = stmt.where(
                func.lower(User.first_name).like(search_like)
                | func.lower(User.last_name).like(search_like)
                | func.lower(User.phone).like(search_like)
                | func.lower(User.email).like(search_like)
                | func.lower(TransportType.name).like(search_like)
            )

        # ⏰ Фильтрация по рабочему времени
        if filters.start_time:
            stmt = stmt.where(CourierSchedule.start_time >= filters.start_time)
        if filters.end_time:
            stmt = stmt.where(CourierSchedule.end_time <= filters.end_time)

        # ↕️ Сортировка
        field_map = {
            "id": User.id,
            "full_name": full_name_expr,
            "phone": User.phone,
            "email": User.email,
            "transport_name": TransportType.name,
        }
        order_field = field_map.get(filters.order_by, User.id)
        stmt = stmt.order_by(order_field.desc() if filters.order_dir == "desc" else order_field.asc())

        # 🔢 Пагинация
        stmt = stmt.limit(filters.limit).offset(filters.offset)

        # 📥 Выполнение
        result: Result[Tuple[UUID, str, str, str, str, time, time]] = await self.session.execute(stmt)
        rows: Sequence[Row[Tuple[UUID, str, str, str, str, time, time]]] = result.fetchall()

        return [
            UserChartRead(
                id=r.id,
                full_name=r.full_name,
                phone=r.phone,
                email=r.email,
                transport_name=r.transport_name,
                work_schedule=f"{r.start_time.strftime('%H:%M')}–{r.end_time.strftime('%H:%M')}",
            )
            for r in rows
        ]

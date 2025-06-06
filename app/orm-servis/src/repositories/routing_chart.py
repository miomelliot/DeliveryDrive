# src/repositories/routing_chart.py
from datetime import date, time
from typing import Any, Dict, Sequence, Tuple
from uuid import UUID

from sqlalchemy import Result, func, select
from sqlalchemy.engine.row import Row
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from src.db.models import Address, Client, Order, OrderStatus, RouteItem
from src.schemas.routing_chart import RoutingChartFilter, RoutingChartRead
from src.utils.sqlalchemy_expr import location_expr


class RoutingChartRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session: AsyncSession = session

    async def get_chart(self, filters: RoutingChartFilter) -> list[RoutingChartRead]:
        # 🏗️ Базовый запрос
        stmt: Select[Tuple[UUID, date, date, time, time, str, str, str]] = (
            select(
                Order.id,
                Order.rent_start,
                Order.rent_end,
                Order.window_start,
                Order.window_end,
                Client.phone,
                location_expr().label("location"),
                OrderStatus.description,
            )
            .join(Client, Client.id == Order.client_id)
            .join(Address, Address.id == Client.address_id)
            .join(OrderStatus, OrderStatus.id == Order.status_id)
        )

        # 🔗 Фильтрация по маршруту
        if filters.route_id:
            stmt = stmt.join(RouteItem, RouteItem.order_id == Order.id)
            stmt = stmt.where(RouteItem.route_id == filters.route_id)

        # 🔍 Поиск
        if filters.search:
            like: str = f"%{filters.search.lower()}%"
            stmt = stmt.where(
                func.lower(Client.phone).like(like)
                | func.lower(OrderStatus.description).like(like)
                | func.lower(location_expr()).like(like)
            )

        # 📋 Фильтрация по статусу
        if filters.description:
            stmt = stmt.where(OrderStatus.description == filters.description)

        # 🕒 Временные окна
        if filters.window_start_from:
            stmt = stmt.where(Order.window_start >= filters.window_start_from)
        if filters.window_end_to:
            stmt = stmt.where(Order.window_end <= filters.window_end_to)

        # ✅ Только активные
        if filters.only_active:
            stmt = stmt.where(~OrderStatus.code.in_(["completed", "cancelled"]))

        # ↕️ Сортировка
        field_map = {
            "id": Order.id,
            "rent_start": Order.rent_start,
            "rent_end": Order.rent_end,
            "window_start": Order.window_start,
            "window_end": Order.window_end,
            "phone": Client.phone,
            "location": location_expr(),
            "description": OrderStatus.description,
        }
        col = field_map.get(filters.order_by, Order.id)
        stmt = stmt.order_by(col.desc() if filters.order_dir == "desc" else col.asc())

        # 📄 Пагинация
        stmt = stmt.limit(filters.limit).offset(filters.offset)

        # 🧾 Выполнение
        res: Result[Tuple[UUID, date, date, time, time, str, str, str]] = await self.session.execute(stmt)
        rows: Sequence[Row[Tuple[UUID, date, date, time, time, str, str, str]]] = res.fetchall()

        # 🧠 Формирование ответа
        result: list[RoutingChartRead] = []
        for row in rows:
            d: Dict[str, Any] = row._asdict()
            window_range: str = f"{d['window_start'].strftime('%H:%M')}–{d['window_end'].strftime('%H:%M')}"
            result.append(
                RoutingChartRead(
                    id=d["id"],
                    rent_start=d["rent_start"],
                    rent_end=d["rent_end"],
                    window=window_range,
                    phone=d["phone"],
                    location=d["location"],
                    description=d["description"],
                )
            )

        return result

    async def get_unique_descriptions(self) -> list[str]:
        stmt: Select[Tuple[str]] = select(func.distinct(OrderStatus.description)).order_by(OrderStatus.description)
        result: Result[Tuple[str]] = await self.session.execute(stmt)
        return [row[0] for row in result.all() if row[0]]

from typing import Any, Sequence, Tuple

from sqlalchemy import Function, Result, Select, func, select
from sqlalchemy.engine.row import Row
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Address, Client, Order, OrderStatus, Route, RouteItem, User
from src.schemas.order_chart import OrderChartFilter, OrderChartRead


class OrderChartRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session: AsyncSession = session

    async def get_chart(self, filters: OrderChartFilter) -> list[OrderChartRead]:
        stmt: Select[tuple[Any]] = (
            select(
                Order.id,
                Order.created_at,
                Order.rent_start,
                Order.rent_end,
                Order.window_start,
                Order.window_end,
                Client.phone,
                Address.city,
                Address.street,
                Address.building,
                OrderStatus.description,
                User.first_name,
                User.last_name,
            )
            .join(Client, Client.id == Order.client_id)
            .join(Address, Address.id == Client.address_id)
            .join(OrderStatus, OrderStatus.id == Order.status_id)
            .outerjoin(RouteItem, RouteItem.order_id == Order.id)
            .outerjoin(Route, Route.id == RouteItem.route_id)
            .outerjoin(User, User.id == Route.courier_id)
        )

        # 🔍 Поиск
        if filters.search:
            like: str = f"%{filters.search.lower()}%"
            full_name: Function[str] = func.lower(
                func.concat_ws(" ", func.coalesce(User.first_name, ""), func.coalesce(User.last_name, ""))
            )

            stmt = stmt.where(
                func.lower(Client.phone).like(like)
                | func.lower(Address.city).like(like)
                | func.lower(Address.street).like(like)
                | func.lower(Address.building).like(like)
                | func.lower(OrderStatus.description).like(like)
                | full_name.like(like)
            )

        # 📋 Выпадающие фильтры
        if filters.description:
            stmt = stmt.where(OrderStatus.description == filters.description)
        if filters.first_name:
            stmt = stmt.where(User.first_name == filters.first_name)
        if filters.last_name:
            stmt = stmt.where(User.last_name == filters.last_name)

        # 🕒 Временные рамки
        if filters.window_start_from:
            stmt = stmt.where(Order.window_start >= filters.window_start_from)
        if filters.window_end_to:
            stmt = stmt.where(Order.window_end <= filters.window_end_to)

        # ✅ Только активные (не завершённые и не отменённые)
        if filters.only_active:
            stmt = stmt.where(~OrderStatus.code.in_(["completed", "cancelled"]))

        # ↕️ Сортировка
        field_map = {
            "id": Order.id,
            "created_at": Order.created_at,
            "rent_start": Order.rent_start,
            "rent_end": Order.rent_end,
            "window_start": Order.window_start,
            "window_end": Order.window_end,
            "phone": Client.phone,
            "city": Address.city,
            "street": Address.street,
            "building": Address.building,
            "description": OrderStatus.description,
            "first_name": User.first_name,
            "last_name": User.last_name,
        }

        order_column = field_map.get(filters.order_by, Order.id)
        stmt = stmt.order_by(order_column.desc() if filters.order_dir == "desc" else order_column.asc())
        stmt = stmt.limit(filters.limit).offset(filters.offset)

        result: Result[tuple[Any]] = await self.session.execute(stmt)
        rows: Sequence[Row[tuple[Any]]] = result.fetchall()

        return [OrderChartRead.model_validate(row._asdict()) for row in rows]

    async def get_unique_descriptions(self) -> list[str]:
        stmt: Select[Tuple[str]] = select(func.distinct(OrderStatus.description)).order_by(OrderStatus.description)
        result: Result[Tuple[str]] = await self.session.execute(stmt)
        return [row[0] for row in result.all() if row[0]]

    async def get_unique_full_names(self) -> list[str]:
        stmt: Select[Tuple[str]] = (
            select(
                func.distinct(
                    func.concat_ws(" ", func.coalesce(User.first_name, ""), func.coalesce(User.last_name, ""))
                ).label("full_name")
            )
            .select_from(Order)
            .join(RouteItem, RouteItem.order_id == Order.id)
            .join(Route, Route.id == RouteItem.route_id)
            .join(User, User.id == Route.courier_id)
            .where((User.first_name.isnot(None)) | (User.last_name.isnot(None)))
            .order_by("full_name")
        )

        result: Result[Tuple[str]] = await self.session.execute(stmt)
        return [row[0] for row in result.all() if row[0].strip()]

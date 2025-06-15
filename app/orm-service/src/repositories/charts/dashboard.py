# src/repositories/charts/dashboard.py
from datetime import date
from typing import List, Sequence, Tuple

from sqlalchemy import Label, RowMapping, ScalarSelect, Select, Subquery, func, select
from sqlalchemy.engine.row import Row
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import (
    Equipment,
    EquipmentStatus,
    HeaterType,
    Order,
    OrderStatus,
)
from src.schemas.dashboard import (
    DayCount,
    EquipmentStockResponse,
    OrdersSummaryResponse,
    WarehouseSummaryResponse,
)


class DashboardRepository:
    async def orders_count_by_day(
        self,
        session: AsyncSession,
        start: date,
        end: date,
    ) -> List[DayCount]:
        created_date: Label[date] = func.date(Order.created_at).label("day")

        stmt: Select[Tuple[date, int]] = (
            select(created_date, func.count())
            .where(created_date.between(start, end))
            .group_by(created_date)
            .order_by(created_date)
        )

        rows: Sequence[Row[Tuple[date, int]]] = (await session.execute(stmt)).all()
        return [DayCount(date=row[0], count=row[1]) for row in rows]

    async def orders_summary_for_day(
        self,
        session: AsyncSession,
        day: date,
    ) -> OrdersSummaryResponse:
        orders_subq: Subquery = (select(Order.id, Order.status_id).where(func.date(Order.created_at) == day)).subquery()

        def count_with_status(code: str) -> ScalarSelect[int]:
            return (
                select(func.count())
                .select_from(orders_subq.join(OrderStatus, orders_subq.c.status_id == OrderStatus.id))
                .where(OrderStatus.code == code)
                .scalar_subquery()
            )

        stmt: Select[Tuple[int, int, int, int]] = select(
            select(func.count()).select_from(orders_subq).scalar_subquery().label("total"),
            count_with_status("completed").label("completed"),
            count_with_status("overdue").label("overdue"),
            count_with_status("recalled").label("recalled"),
        )

        row: RowMapping = (await session.execute(stmt)).mappings().one()
        return OrdersSummaryResponse(**row)

    async def warehouse_summary(
        self,
        session: AsyncSession,
    ) -> WarehouseSummaryResponse:
        def count_by_status(code: str) -> ScalarSelect[int]:
            return (
                select(func.count())
                .select_from(Equipment)
                .join(Equipment.status)
                .where(EquipmentStatus.code == code)
                .scalar_subquery()
            )

        stmt: Select[Tuple[int, int, int, int]] = select(
            select(func.count()).select_from(Equipment).scalar_subquery().label("total_equipment"),
            count_by_status("available").label("available"),
            count_by_status("in_rent").label("in_rent"),
            count_by_status("maintenance").label("maintenance"),
        )

        row: RowMapping = (await session.execute(stmt)).mappings().one()
        return WarehouseSummaryResponse(**row)

    async def equipment_stock(
        self,
        session: AsyncSession,
        offset: int,
        limit: int,
    ) -> List[EquipmentStockResponse]:
        quantity: Label[int] = func.count(Equipment.id).filter(EquipmentStatus.code == "available").label("quantity")

        stmt: Select[Tuple[str, int]] = (
            select(
                HeaterType.model,
                quantity,
            )
            .select_from(HeaterType)
            .outerjoin(HeaterType.equipment)
            .outerjoin(Equipment.status)
            .group_by(HeaterType.model)
            .order_by(quantity.desc())
            .offset(offset)
            .limit(limit)
        )

        rows: Sequence[Row[Tuple[str, int]]] = (await session.execute(stmt)).all()

        return [EquipmentStockResponse(model=row[0], quantity=row[1] or 0) for row in rows]

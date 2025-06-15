# src/repositories/charts/dashboard.py
from datetime import date
from typing import List, Sequence, Tuple

from sqlalchemy import (
    BinaryExpression,
    Label,
    RowMapping,
    ScalarSelect,
    Select,
    Subquery,
    True_,
    and_,
    func,
    select,
    true,
)
from sqlalchemy.engine.row import Row
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import (
    Equipment,
    EquipmentStatus,
    HeaterType,
    Invoice,
    Order,
    OrderStatus,
    Role,
    Route,
    RouteItem,
    User,
)
from src.schemas.dashboard import (
    CourierOrdersCount,
    DayCount,
    EquipmentStatusCount,
    EquipmentStockResponse,
    FinanceDaily,
    OrdersSummaryResponse,
    OrderStatusDaily,
    WarehouseSummaryResponse,
)


class DashboardRepository:
    async def orders_count_by_day(self, session: AsyncSession, start: date, end: date) -> List[DayCount]:
        created_date: Label[date] = func.date(Order.created_at).label("day")

        stmt: Select[Tuple[date, int]] = (
            select(created_date, func.count())
            .where(created_date.between(start, end))
            .group_by(created_date)
            .order_by(created_date)
        )

        rows: Sequence[Row[Tuple[date, int]]] = (await session.execute(stmt)).all()
        return [DayCount(date=row[0], count=row[1]) for row in rows]

    async def orders_summary_for_day(self, session: AsyncSession, day: date) -> OrdersSummaryResponse:
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

    async def warehouse_summary(self, session: AsyncSession) -> WarehouseSummaryResponse:
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

    async def equipment_stock(self, session: AsyncSession, offset: int, limit: int) -> List[EquipmentStockResponse]:
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

    async def orders_by_status_daily(self, session: AsyncSession, start: date, end: date) -> List[OrderStatusDaily]:
        created_date: Label[date] = func.date(Order.created_at).label("day")

        stmt: Select[Tuple[date, str, int]] = (
            select(
                created_date,
                OrderStatus.code,
                func.count(),
            )
            .join(Order.status)  # relationship
            .where(created_date.between(start, end))
            .group_by(created_date, OrderStatus.code)
            .order_by(created_date, OrderStatus.code)
        )

        rows: Sequence[Row[Tuple[date, str, int]]] = (await session.execute(stmt)).all()

        return [OrderStatusDaily(date=r[0], status_code=r[1], count=r[2]) for r in rows]

    async def orders_by_courier(
        self,
        session: AsyncSession,
        start: date | None = None,
        end: date | None = None,
    ) -> List[CourierOrdersCount]:
        courier_name: Label[str] = func.concat_ws(" ", User.last_name, User.first_name).label("courier")

        date_cond: BinaryExpression[bool] | True_ = (
            func.date(Route.date).between(start, end) if start and end else true()
        )

        stmt: Select[Tuple[str, int]] = (
            select(courier_name, func.coalesce(func.count(Order.id), 0).label("count"))
            .select_from(User)
            .where(User.role.has(Role.name == "courier"))
            .outerjoin(
                Route,
                and_(Route.courier_id == User.id, date_cond),
            )
            .outerjoin(RouteItem, RouteItem.route_id == Route.id)
            .outerjoin(Order, Order.id == RouteItem.order_id)
            .group_by(User.id, User.last_name, User.first_name)
            .order_by(func.count(Order.id).desc())
        )

        rows: Sequence[Row[Tuple[str, int]]] = (await session.execute(stmt)).all()

        return [CourierOrdersCount(courier_name=(r[0] or "").strip(), count=r[1]) for r in rows]

    async def equipment_status_counts(self, session: AsyncSession) -> List[EquipmentStatusCount]:
        stmt: Select[Tuple[str, int]] = (
            select(
                EquipmentStatus.code,
                func.count(Equipment.id),
            )
            .join(EquipmentStatus.equipment)
            .group_by(EquipmentStatus.code)
        )

        rows: Sequence[Row[Tuple[str, int]]] = (await session.execute(stmt)).all()
        return [EquipmentStatusCount(status_code=r[0], count=r[1]) for r in rows]

    async def finance_daily(self, session: AsyncSession, start: date, end: date) -> List[FinanceDaily]:
        issued_sum: Label[float] = func.sum(Invoice.amount).label("issued")
        paid_sum: Label[float] = func.sum(Invoice.amount).label("paid")

        issued_q: Subquery = (
            select(func.date(Invoice.issued_at).label("day"), issued_sum)
            .where(
                Invoice.issued_at.is_not(None),
                func.date(Invoice.issued_at).between(start, end),
            )
            .group_by("day")
        ).subquery()

        paid_q: Subquery = (
            select(func.date(Invoice.paid_at).label("day"), paid_sum)
            .where(
                Invoice.paid_at.is_not(None),
                func.date(Invoice.paid_at).between(start, end),
            )
            .group_by("day")
        ).subquery()

        stmt: Select[Tuple[date, float, float]] = (
            select(
                func.coalesce(issued_q.c.day, paid_q.c.day).label("day"),
                func.coalesce(issued_q.c.issued, 0).label("issued"),
                func.coalesce(paid_q.c.paid, 0).label("paid"),
            )
            .select_from(issued_q.outerjoin(paid_q, issued_q.c.day == paid_q.c.day))
            .order_by("day")
        )

        rows: Sequence[Row[Tuple[date, float, float]]] = (await session.execute(stmt)).all()
        return [FinanceDaily(date=r[0], issued=float(r[1]), paid=float(r[2])) for r in rows]

# src/repositories/invoice_chart.py

from datetime import date
from decimal import Decimal
from typing import Any, Sequence, Tuple
from uuid import UUID

from sqlalchemy import ColumnElement, Integer, Label, Numeric, Result, RowMapping, Select, String, cast, func, select
from sqlalchemy.engine.row import Row
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Client, HeaterType, Invoice, InvoiceStatus, Order, OrderItem
from src.schemas.invoice_chart import (
    InvoiceChartFilter,
    InvoiceChartRead,
    InvoiceWidgetRead,
)


class InvoiceChartRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session: AsyncSession = session

    async def get_chart(self, filters: InvoiceChartFilter) -> list[InvoiceChartRead]:
        # 📌 Выражения
        days_expr: ColumnElement[Any] = Order.rent_end - Order.rent_start
        days_rent_expr: Label[int] = cast(days_expr, Integer).label("days_rent")
        price_expr: Label[Decimal] = cast(
            func.sum(HeaterType.price * OrderItem.quantity * days_expr), Numeric(12, 2)
        ).label("price")

        stmt: Select[Tuple[UUID, date, str, int, Decimal, float, str]] = (
            select(
                Invoice.id,
                Order.rent_start,
                Client.phone,
                days_rent_expr,
                price_expr,
                Invoice.amount.label("total_income"),
                InvoiceStatus.description.label("status"),
            )
            .join(Order, Order.id == Invoice.order_id)
            .join(Client, Client.id == Order.client_id)
            .join(OrderItem, OrderItem.order_id == Order.id)
            .join(HeaterType, HeaterType.id == OrderItem.heater_type_id)
            .join(InvoiceStatus, Invoice.invoice_status_id == InvoiceStatus.id)
            .group_by(
                Invoice.id,
                Order.rent_start,
                Client.phone,
                Invoice.amount,
                InvoiceStatus.description,
                Order.rent_end,
            )
        )

        # 🔍 Поиск
        if filters.search:
            like: str = f"%{filters.search.lower()}%"
            stmt = stmt.where(
                func.lower(Client.phone).like(like)
                | cast(Invoice.amount, String).like(like)
                | func.lower(InvoiceStatus.description).like(like)
            )

        # 📋 Фильтрация по статусу
        if filters.status:
            stmt = stmt.where(InvoiceStatus.description == filters.status)

        # 📅 Диапазон дат
        if filters.rent_date_start:
            stmt = stmt.where(Order.rent_start >= filters.rent_date_start)
        if filters.rent_date_end:
            stmt = stmt.where(Order.rent_start <= filters.rent_date_end)

        # ✅ Только активные счета
        if filters.only_active:
            stmt = stmt.where(InvoiceStatus.code == "issued")

        # ↕️ Сортировка
        field_map = {
            "id": Invoice.id,
            "rent_start": Order.rent_start,
            "phone": Client.phone,
            "days_rent": days_rent_expr,
            "price": price_expr,
            "total_income": Invoice.amount,
            "status": InvoiceStatus.description,
        }
        sort_col = field_map.get(filters.order_by, Invoice.id)
        stmt = stmt.order_by(sort_col.desc() if filters.order_dir == "desc" else sort_col.asc())

        # 📄 Пагинация
        stmt = stmt.limit(filters.limit).offset(filters.offset)

        res: Result[Tuple[UUID, date, str, int, Decimal, float, str]] = await self.session.execute(stmt)
        rows: Sequence[Row[Tuple[UUID, date, str, int, Decimal, float, str]]] = res.fetchall()

        return [InvoiceChartRead.model_validate(dict(r)) for r in rows]

    async def get_widget(self) -> InvoiceWidgetRead:
        stmt: Select[Tuple[int, float, float]] = select(
            func.count().filter(InvoiceStatus.code == "issued").label("total_active_contracts"),
            func.coalesce(func.sum(Invoice.amount), 0).label("potential_income"),
            func.coalesce(func.avg(Invoice.amount), 0).label("monthly_average"),
        ).join(InvoiceStatus, Invoice.invoice_status_id == InvoiceStatus.id)

        res: Result[Tuple[int, float, float]] = await self.session.execute(stmt)
        row: RowMapping = res.one()._mapping

        return InvoiceWidgetRead(
            total_active_contracts=row["total_active_contracts"],
            potential_income=row["potential_income"],
            monthly_average=row["monthly_average"],
        )

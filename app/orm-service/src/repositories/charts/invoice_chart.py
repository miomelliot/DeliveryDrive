# src/repositories/invoice_chart.py

from datetime import date
from decimal import Decimal
from typing import Any, Sequence, Tuple
from uuid import UUID

from sqlalchemy import Date, Label, Numeric, Result, RowMapping, Select, String, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Client, HeaterType, Invoice, InvoiceStatus, Order, OrderItem
from src.schemas.invoice_chart import (
    InvoiceChartFilter,
    InvoiceChartRead,
    InvoiceWidgetRead,
)


class InvoiceChartRepository:
    async def get_chart(self, session: AsyncSession, filters: InvoiceChartFilter) -> list[InvoiceChartRead]:
        # 📌 Выражения
        days_expr: Label[Any] = (cast(Order.rent_end, Date) - cast(Order.rent_start, Date)).label("days_rent")

        base_price_expr: Label[float] = func.sum(HeaterType.price * OrderItem.quantity).label("price")
        total_income_expr: Label[Decimal] = (
            (
                func.sum(HeaterType.price * OrderItem.quantity)
                * (cast(Order.rent_end, Date) - cast(Order.rent_start, Date))
            )
            .cast(Numeric(12, 2))
            .label("total_income")
        )

        stmt: Select[Tuple[UUID, date, str, int, float, Decimal, str]] = (
            select(
                Order.id,
                Order.rent_start,
                Client.phone,
                days_expr,
                base_price_expr,
                total_income_expr,
                InvoiceStatus.description.label("status"),
            )
            .select_from(Invoice)
            .join(Order, Order.id == Invoice.order_id)
            .join(Client, Client.id == Order.client_id)
            .join(OrderItem, OrderItem.order_id == Order.id)
            .join(HeaterType, HeaterType.id == OrderItem.heater_type_id)
            .join(InvoiceStatus, Invoice.invoice_status_id == InvoiceStatus.id)
            .group_by(
                Invoice.id,
                Order.id,
                Order.rent_start,
                Order.rent_end,
                Client.phone,
                InvoiceStatus.description,
            )
        )

        # 🔍 Поиск
        if filters.search:
            like: str = f"%{filters.search.lower()}%"
            stmt = stmt.where(func.lower(Client.phone).like(like) | cast(Invoice.amount, String).like(like))

        # 📋 Фильтрация по статусу
        if filters.status:
            stmt = stmt.where(InvoiceStatus.description == filters.status)

        # 📅 Диапазон дат
        if filters.rent_date_start:
            stmt = stmt.where(Order.rent_start >= filters.rent_date_start)
        if filters.rent_date_end:
            stmt = stmt.where(Order.rent_start <= filters.rent_date_end)

        # ↕️ Сортировка
        field_map = {
            "id": Invoice.id,
            "rent_start": Order.rent_start,
            "phone": Client.phone,
            "days_rent": days_expr,
            "price": base_price_expr,
            "total_income": total_income_expr,
            "status": InvoiceStatus.description,
        }
        sort_col = field_map.get(filters.order_by, Invoice.id)
        stmt = stmt.order_by(sort_col.desc() if filters.order_dir == "desc" else sort_col.asc())

        # 📄 Пагинация
        stmt = stmt.limit(filters.limit).offset(filters.offset)

        res: Result[Tuple[UUID, date, str, int, float, Decimal, str]] = await session.execute(stmt)
        rows: Sequence[RowMapping] = res.mappings().all()

        return [InvoiceChartRead.model_validate(row) for row in rows]

    async def get_widget(self, session: AsyncSession) -> InvoiceWidgetRead:
        stmt: Select[Tuple[int, float, float]] = select(
            func.count().filter(InvoiceStatus.code == "issued").label("total_active_contracts"),
            func.coalesce(func.sum(Invoice.amount), 0).label("potential_income"),
            func.coalesce(func.avg(Invoice.amount), 0).label("monthly_average"),
        ).join(InvoiceStatus, Invoice.invoice_status_id == InvoiceStatus.id)

        res: Result[Tuple[int, float, float]] = await session.execute(stmt)
        row: RowMapping = res.one()._mapping

        return InvoiceWidgetRead(
            total_active_contracts=row["total_active_contracts"],
            potential_income=row["potential_income"],
            monthly_average=row["monthly_average"],
        )

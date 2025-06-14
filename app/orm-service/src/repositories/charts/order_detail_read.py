# src/repositories/order_detail_read.py
from datetime import datetime
from typing import Any, Tuple
from uuid import UUID

from sqlalchemy import Result, RowMapping, Select, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from src.db.models import (
    Address,
    BaseLookup,
    Client,
    Contract,
    HeaterType,
    Invoice,
    InvoiceStatus,
    Order,
    OrderHistory,
    OrderItem,
    Route,
    RouteItem,
    User,
)
from src.schemas.order_detail_read import (
    OrderDetailRead,
    OrderDetailUpdate,
    OrderHistoryChart,
    OrderItemChart,
)
from src.utils.formatters import format_time_range
from src.utils.sqlalchemy_expr import full_name_expr, location_expr


class OrderDetailRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session: AsyncSession = session

    async def get_detail(self, order_id: UUID) -> OrderDetailRead:
        stmt: Select[Any] = (
            select(
                Order.id,
                Order.created_at,
                Order.rent_start,
                Order.rent_end,
                Order.window_start,
                Order.window_end,
                Client.phone,
                Client.name.label("client_name"),
                location_expr().label("location"),
                BaseLookup.description.label("status"),
                InvoiceStatus.description.label("invoice_status"),
                Invoice.issued_at,
                Invoice.paid_at,
                Contract.file_path.label("contract_file_path"),
                Order.comment,
                full_name_expr().label("courier_name"),
            )
            .join(Client, Client.id == Order.client_id)
            .join(Address, Address.id == Client.address_id)
            .join(BaseLookup, BaseLookup.id == Order.status_id)
            .outerjoin(Invoice, Invoice.order_id == Order.id)
            .outerjoin(InvoiceStatus, InvoiceStatus.id == Invoice.invoice_status_id)
            .outerjoin(Contract, Contract.order_id == Order.id)
            .outerjoin(RouteItem, RouteItem.order_id == Order.id)
            .outerjoin(Route, Route.id == RouteItem.route_id)
            .outerjoin(User, User.id == Route.courier_id)
            .where(Order.id == order_id)
        )

        # 🧾 Выполнение
        result: Result[Any] = await self.session.execute(stmt)
        row: RowMapping = result.one()._mapping

        # 🤌 Состав заказа
        item_stmt: Select[Tuple[str, float, int]] = (
            select(
                HeaterType.model,
                HeaterType.weight,
                OrderItem.quantity,
            )
            .join(HeaterType, HeaterType.id == OrderItem.heater_type_id)
            .where(OrderItem.order_id == order_id)
        )
        item_result: Result[Tuple[str, float, int]] = await self.session.execute(item_stmt)
        items: list[OrderItemChart] = [OrderItemChart.model_validate(dict(r._mapping)) for r in item_result.fetchall()]

        # 🗓️ История заказа
        status_new: type[BaseLookup] = aliased(BaseLookup)
        status_prev: type[BaseLookup] = aliased(BaseLookup)

        history_stmt: Select[Tuple[datetime, str, str]] = (
            select(
                OrderHistory.timestamp,
                status_new.description.label("new_status"),
                status_prev.description.label("previous_status"),
            )
            .join(status_new, status_new.id == OrderHistory.new_status_id)
            .outerjoin(status_prev, status_prev.id == OrderHistory.previous_status_id)
            .where(OrderHistory.order_id == order_id)
            .order_by(OrderHistory.timestamp.desc())
        )
        history_result: Result[Tuple[datetime, str, str]] = await self.session.execute(history_stmt)
        history: list[OrderHistoryChart] = [
            OrderHistoryChart.model_validate(dict(r._mapping)) for r in history_result.fetchall()
        ]

        # 📦 Преобразование в Pydantic
        return OrderDetailRead(
            id=row["id"],
            created_at=row["created_at"],
            rent_start=row["rent_start"],
            rent_end=row["rent_end"],
            window=format_time_range(row["window_start"], row["window_end"]),
            phone=row["phone"],
            client_name=row["client_name"],
            courier_name=row["courier_name"],
            location=row["location"],
            status=row["status"],
            invoice_status=row["invoice_status"],
            invoice_issued_at=row["issued_at"],
            invoice_paid_at=row["paid_at"],
            contract_file_path=row["contract_file_path"],
            comment=row["comment"],
            items=items,
            history=history,
        )

    async def update_detail(self, order_id: UUID, data: OrderDetailUpdate) -> None:
        order: Order | None = await self.session.get(Order, order_id, populate_existing=True)
        if order is None:
            raise ValueError(f"Order {order_id} not found")

        await self._update_order(order, data)
        await self._update_client(order.client_id, data)
        await self._update_invoice(order.id, data)

        await self.session.commit()

    async def _update_order(self, order: Order, data: OrderDetailUpdate) -> None:
        if data.rent_start is not None:
            order.rent_start = data.rent_start
        if data.rent_end is not None:
            order.rent_end = data.rent_end
        if data.window is not None:
            try:
                start_str, end_str = data.window.split("–")
                order.window_start = datetime.strptime(start_str.strip(), "%H:%M").time()
                order.window_end = datetime.strptime(end_str.strip(), "%H:%M").time()
            except Exception as e:
                raise ValueError(f"Invalid time format: {data.window}") from e
        if data.comment is not None:
            order.comment = data.comment
        if data.status is not None:
            status: BaseLookup | None = await self.session.scalar(
                select(BaseLookup).where(BaseLookup.description == data.status)
            )
            if status is None:
                raise ValueError(f"Unknown order status: {data.status}")
            order.status_id = status.id

    async def _update_client(self, client_id: UUID, data: OrderDetailUpdate) -> None:
        if not (data.phone or data.client_name or data.location):
            return

        client: Client | None = await self.session.get(Client, client_id, populate_existing=True)
        if client is None:
            raise ValueError(f"Client {client_id} not found")

        if data.phone is not None:
            client.phone = data.phone
        if data.client_name is not None:
            client.name = data.client_name
        if data.location is not None:
            try:
                city, street, building = [x.strip() for x in data.location.split(",", 2)]
            except Exception as e:
                raise ValueError(f"Invalid location format: {data.location}") from e

            address: Address | None = await self.session.get(Address, client.address_id, populate_existing=True)
            if address is None:
                raise ValueError(f"Address {client.address_id} not found")
            address.city = city
            address.street = street
            address.building = building

    async def _update_invoice(self, order_id: UUID, data: OrderDetailUpdate) -> None:
        if not (data.invoice_status or data.invoice_issued_at or data.invoice_paid_at):
            return

        invoice: Invoice | None = await self.session.scalar(select(Invoice).where(Invoice.order_id == order_id))
        if invoice is None:
            invoice = Invoice(order_id=order_id)
            self.session.add(invoice)

        if data.invoice_status is not None:
            status: InvoiceStatus | None = await self.session.scalar(
                select(InvoiceStatus).where(InvoiceStatus.description == data.invoice_status)
            )
            if status is None:
                raise ValueError(f"Unknown invoice status: {data.invoice_status}")
            invoice.invoice_status_id = status.id
        if data.invoice_issued_at is not None:
            invoice.issued_at = data.invoice_issued_at
        if data.invoice_paid_at is not None:
            invoice.paid_at = data.invoice_paid_at

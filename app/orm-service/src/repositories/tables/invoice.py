# src/repositories/tables/invoice.py
from decimal import Decimal
from typing import Tuple
from uuid import UUID

from sqlalchemy import Result, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Invoice
from src.repositories.tables.base import CRUDRepository
from src.repositories.tables.invoice_status import InvoiceStatusRepository
from src.repositories.tables.order_item import OrderItemRepository
from src.schemas.invoice import InvoiceCreate, InvoiceUpdate
from src.schemas.order_detail_read import OrderDetailUpdate
from src.utils.http_error import NotFoundError


class InvoiceRepository(CRUDRepository[Invoice, InvoiceCreate, InvoiceUpdate]):
    def __init__(self) -> None:
        super().__init__(Invoice)

    async def create_from_order(self, session: AsyncSession, order_id: UUID) -> Invoice:
        invoice_status_id: int = await InvoiceStatusRepository().get_id(session, "not_paid")
        amount: Decimal = await OrderItemRepository().get_total_amount(session, order_id)

        obj_in = InvoiceCreate(
            order_id=order_id,
            invoice_status_id=invoice_status_id,
            amount=amount,
        )

        return await super().create(session, obj_in)

    async def update_raw(self, session: AsyncSession, order_id: UUID, raw_data: OrderDetailUpdate) -> Invoice:
        res: Result[Tuple[UUID]] = await session.execute(select(Invoice.id).where(Invoice.order_id == order_id))
        instance_id: UUID | None = res.scalars().first()

        if instance_id is None:
            raise NotFoundError()

        invoice_status_id = None
        if raw_data.invoice_status:
            invoice_status_id = await InvoiceStatusRepository().get_id(session, raw_data.invoice_status)
        obj_in = InvoiceUpdate(
            invoice_status_id=invoice_status_id,
            issued_at=raw_data.invoice_issued_at,
            paid_at=raw_data.invoice_paid_at,
        )
        return await super().update_by_id(session, instance_id, obj_in)

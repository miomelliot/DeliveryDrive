# src/repositories/tables/invoice.py
from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Invoice
from src.repositories.tables.base import CRUDRepository
from src.repositories.tables.invoice_status import InvoiceStatusRepository
from src.repositories.tables.order_item import OrderItemRepository
from src.schemas.invoice import InvoiceCreate, InvoiceUpdate


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
    
    

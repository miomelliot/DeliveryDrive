# src/schemas/invoice.py
from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class _InvoiceBase(BaseModel):
    order_id: UUID
    invoice_status_id: int


class InvoiceCreate(_InvoiceBase):
    amount: Decimal


class InvoiceCreateRaw(_InvoiceBase):
    pass


class InvoiceUpdate(BaseModel):
    invoice_status_id: int | None = None
    issued_at: date | None = None
    paid_at: date | None = None


class InvoiceRead(_InvoiceBase):
    id: UUID
    amount: Decimal
    model_config = ConfigDict(from_attributes=True)

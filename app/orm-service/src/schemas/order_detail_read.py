# src/schemas/order_detail_read.py
from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, FilePath


class OrderItemChart(BaseModel):
    model: str
    weight: float
    quantity: int


class OrderHistoryChart(BaseModel):
    timestamp: datetime
    previous_status: str | None
    new_status: str


class OrderDetailRead(BaseModel):
    id: UUID
    created_at: datetime
    rent_start: date
    rent_end: date
    window: str
    phone: str
    client_name: str
    courier_name: str | None
    location: str
    status: str
    invoice_status: str
    invoice_issued_at: date | None
    invoice_paid_at: date | None
    contract_file_path: FilePath | None
    comment: str | None
    items: list[OrderItemChart]
    history: list[OrderHistoryChart]
    model_config = ConfigDict(from_attributes=True)


class OrderDetailUpdate(BaseModel):
    phone: str | None = None
    client_name: str | None = None
    rent_start: date | None = None
    rent_end: date | None = None
    window: str | None = None
    location: str | None = None
    status: str | None = None
    invoice_status: str | None = None
    invoice_issued_at: date | None = None
    invoice_paid_at: date | None = None
    comment: str | None = None

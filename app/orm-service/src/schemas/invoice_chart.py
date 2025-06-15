# src/schemas/invoice_chart.py
from datetime import date
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class InvoiceChartRead(BaseModel):
    # Invoice
    id: UUID
    # Order
    rent_start: date
    # Client
    phone: str
    # SQL
    days_rent: int
    total_income: float
    # HeaterType
    price: float
    # InvoiceStatus
    status: str  # description
    model_config = ConfigDict(from_attributes=True)


class InvoiceChartFilter(BaseModel):
    search: str | None = None
    order_by: Literal[
        "id",
        "rent_start",
        "phone",
        "days_rent",
        "total_income",
        "price",
        "status",
    ] = "id"
    order_dir: Literal["asc", "desc"] = "asc"

    # 🔽 Выпадающий фильтр по имени и описанию статуса
    status: Literal["Выставлен", "Оплачен", "Не оплачен"] | None = None

    # 🔽 Фильтрация по диапазону дат
    rent_date_start: date | None = None
    rent_date_end: date | None = None

    limit: int = Field(default=10, le=100)
    offset: int = 0


class InvoiceWidgetRead(BaseModel):
    total_active_contracts: int
    potential_income: float
    monthly_average: float

    model_config = ConfigDict(from_attributes=True)

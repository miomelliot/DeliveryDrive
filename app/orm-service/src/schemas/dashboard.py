# src/schemas/dashboard.py
from datetime import date

from pydantic import BaseModel


class DayCount(BaseModel):
    date: date
    count: int


class OrdersDailyResponse(BaseModel):
    items: list[DayCount]


class OrdersSummaryResponse(BaseModel):
    total: int
    completed: int
    overdue: int
    recalled: int


class WarehouseSummaryResponse(BaseModel):
    total_equipment: int
    available: int
    in_rent: int
    maintenance: int


class HeaterStock(BaseModel):
    heater_type_id: int
    model: str
    quantity: int


class EquipmentStockResponse(BaseModel):
    items: list[HeaterStock]
    page: int
    size: int
    total_pages: int

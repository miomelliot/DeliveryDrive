# src/schemas/dashboard.py
from datetime import date

from pydantic import BaseModel


class DayCount(BaseModel):
    date: date
    count: int


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


class EquipmentStockResponse(BaseModel):
    model: str
    quantity: int


class OrderStatusDaily(BaseModel):
    date: date
    status_code: str
    count: int


class CourierOrdersCount(BaseModel):
    courier_name: str
    count: int


class EquipmentStatusCount(BaseModel):
    status_code: str
    count: int


class FinanceDaily(BaseModel):
    date: date
    issued: float
    paid: float

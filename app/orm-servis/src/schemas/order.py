# src/schemas/order.py
from datetime import date, time

from pydantic import BaseModel, Field


class EquipmentList(BaseModel):
    # HeaterType
    model: str = Field(..., gt=0, description="Количество, не меньше 1")
    quantity: int = Field(..., gt=0, description="Количество, не меньше 1")


class OrderCreate(BaseModel):
    phone: str = Field(
        ...,
        min_length=10,
        max_length=12,
        description="Номер телефона: 10–12 цифр, может начинаться с +",
    )
    name: str | None = Field(None, description="Имя клиента (опционально)")
    location: str = Field(
        min_length=5, description="Адрес клиента: Город, Улица, Дом"
    )  # объединённый адрес: city, street, building распарсить по , макс 3 элемента
    window_start: time = Field(default=time(9), description="Начало окна доставки")
    window_end: time = Field(default=time(18), description="Конец окна доставки")
    rent_start: date = Field(..., description="Дата начала аренды")
    rent_end: date = Field(..., description="Дата окончания аренды")
    comment: str | None = Field(None, description="Комментарий к заказу (необязательно)")

    equipment: list[EquipmentList] = Field(..., description="Список моделей и количества оборудования")

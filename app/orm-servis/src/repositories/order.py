# src/repositories/order.py
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid6 import uuid7

from src.db.models import Address, Client, HeaterType, Order, OrderItem
from src.schemas.order import OrderCreate


class OrderRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session: AsyncSession = session

    async def create_order(self, data: OrderCreate) -> Order:
        # 📍 Парсинг адреса
        try:
            city, street, building = [x.strip() for x in data.location.split(",", 2)]
        except Exception as e:
            raise ValueError("Адрес должен быть в формате: Город, Улица, Дом") from e

        address = Address(
            id=uuid7(),
            city=city,
            street=street,
            building=building,
            lat=0.0,
            lon=0.0,  # Шаблон
        )
        self.session.add(address)

        # 👨️🛋️ Клиент
        client = Client(
            id=uuid7(),
            name=data.name or "Без имени",
            phone=data.phone,
            address_id=address.id,
        )
        self.session.add(client)

        # 📝 Заказ
        order = Order(
            id=uuid7(),
            client_id=client.id,
            rent_start=data.rent_start,
            rent_end=data.rent_end,
            window_start=data.window_start,
            window_end=data.window_end,
            status_id=1,  # например, "Новый"
            comment=data.comment,
        )
        self.session.add(order)

        # ➕ Оборудование
        for eq in data.equipment:
            heater_type: HeaterType | None = await self.session.scalar(
                select(HeaterType).where(HeaterType.model == eq.model)
            )
            if not heater_type:
                raise ValueError(f"Оборудование с моделью '{eq.model}' не найдено")

            item = OrderItem(
                id=uuid7(),
                order_id=order.id,
                heater_type_id=heater_type.id,
                quantity=eq.quantity,
            )
            self.session.add(item)

        await self.session.commit()
        await self.session.refresh(order)
        return order

    async def delete_order(self, order_id: UUID) -> None:
        await self.session.execute(delete(Order).where(Order.id == order_id))
        await self.session.commit()

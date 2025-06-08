# src/repositories/order.py
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid6 import uuid7

from src.db.models import Address, Client, Equipment, EquipmentStatus, HeaterType, Order, OrderItem, OrderStatus
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
            lon=0.0,
        )
        self.session.add(address)

        # 👨️🛋️ Клиент
        client = Client(
            id=uuid7(),
            name=data.name or "-",
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
            status_id=await self.session.scalar(
                select(OrderStatus.id).where(OrderStatus.code == "new"),
            ),
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

            # Найти конкретные свободные экземпляры оборудования
            equipment_items = list(
                await self.session.scalars(
                    select(Equipment)
                    .where(
                        Equipment.heater_type_id == heater_type.id,
                        Equipment.status.has(code="in_stock"),
                    )
                    .limit(eq.quantity)
                )
            )

            if len(equipment_items) < eq.quantity:
                raise ValueError(f"Недостаточно оборудования модели '{eq.model}' на складе")

            # Обновить адрес и статус
            reserved_status_id: int | None = await self.session.scalar(
                select(EquipmentStatus.id).where(EquipmentStatus.code == "rented")
            )
            if reserved_status_id is None:
                raise ValueError("Статус 'rented' не найден в справочнике")

            for equip in equipment_items:
                equip.current_address_id = client.address_id
                equip.equipment_status_id = reserved_status_id
                self.session.add(equip)

            # Добавить заказанную позицию (всё равно по HeaterType)
            item = OrderItem(
                id=uuid7(),
                order_id=order.id,
                heater_type_id=heater_type.id,
                quantity=eq.quantity,
            )
            self.session.add(item)
        return order

    async def delete_order(self, order_id: UUID) -> None:
        await self.session.execute(delete(Order).where(Order.id == order_id))
        await self.session.commit()

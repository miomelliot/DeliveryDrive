# src/repositories/order.py
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Address, Client, Equipment, EquipmentStatus, HeaterType, Order, OrderItem, OrderStatus
from src.schemas.order import OrderCreate
from src.utils.history import add_order_history
from src.utils.http_error import _raise_404, _raise_409, _raise_422, _raise_500


class OrderRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session: AsyncSession = session

    async def create_order(self, data: OrderCreate, uid: UUID) -> Order:
        # 📍 Парсинг адреса
        try:
            city, street, building = [x.strip() for x in data.location.split(",", 2)]
        except Exception:
            _raise_422("Адрес должен быть в формате: Город, Улица, Дом")

        address = Address(
            city=city,
            street=street,
            building=building,
            lat=0.0,
            lon=0.0,
        )
        self.session.add(address)
        await self.session.flush()

        client = Client(
            name=data.name or "-",
            phone=data.phone,
            address_id=address.id,
        )
        self.session.add(client)
        await self.session.flush()

        status_id: int | None = await self.session.scalar(
            select(OrderStatus.id).where(OrderStatus.code == "new"),
        )
        if status_id is None:
            _raise_500("Статус 'new' не найден в справочнике")

        order = Order(
            client_id=client.id,
            rent_start=data.rent_start,
            rent_end=data.rent_end,
            window_start=data.window_start,
            window_end=data.window_end,
            status_id=status_id,
            comment=data.comment,
        )
        self.session.add(order)
        await self.session.flush()

        await add_order_history(
            self.session,
            order_id=order.id,
            previous_status_id=None,
            new_status_id=status_id,
            user_id=uid,
        )

        for eq in data.equipment:
            heater_type: HeaterType | None = await self.session.scalar(
                select(HeaterType).where(HeaterType.model == eq.model)
            )
            if not heater_type:
                _raise_404(f"Оборудование с моделью '{eq.model}' не найдено")

            equipment_items = list(
                await self.session.scalars(
                    select(Equipment)
                    .where(
                        Equipment.heater_type_id == heater_type.id,
                        Equipment.status.has(code="available"),
                    )
                    .limit(eq.quantity)
                )
            )
            if len(equipment_items) < eq.quantity:
                _raise_409(f"Недостаточно оборудования модели '{eq.model}' на складе")

            reserved_status_id: int | None = await self.session.scalar(
                select(EquipmentStatus.id).where(EquipmentStatus.code == "rented")
            )
            if reserved_status_id is None:
                _raise_500("Статус 'rented' не найден в справочнике")

            for equip in equipment_items:
                equip.current_address_id = client.address_id
                equip.equipment_status_id = reserved_status_id
                self.session.add(equip)

            item = OrderItem(
                order_id=order.id,
                heater_type_id=heater_type.id,
                quantity=eq.quantity,
            )
            self.session.add(item)

        return order

    async def delete_order(self, order_id: UUID) -> None:
        await self.session.execute(delete(Order).where(Order.id == order_id))
        await self.session.commit()

# src/repositories/order.py
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import (
    Address,
    BaseLookup,
    Client,
    Equipment,
    EquipmentStatus,
    HeaterType,
    Invoice,
    InvoiceStatus,
    Order,
    OrderItem,
    OrderStatus,
)
from src.schemas.fastapi.order import EquipmentList, OrderCreate
from src.utils.history import add_order_history
from src.utils.http_error import ConflictError, InternalServerError, NotFoundError, UnprocessableEntityError


class OrderRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session: AsyncSession = session

    async def create_order(self, data: OrderCreate, uid: UUID) -> Order:
        address: Address = await self._create_address(data.location)
        client: Client = await self._create_client(data, address.id)
        status_id: int = await self._get_status_id(OrderStatus, "new", "Статус 'new' не найден")
        order: Order = await self._create_order_entity(data, client.id, status_id)
        invoice_status_id: int = await self._get_status_id(InvoiceStatus, "not_paid", "Статус 'not_paid' не найден")
        await self._create_invoice(order.id, invoice_status_id)
        await self._add_order_history(order.id, status_id, uid)
        await self._reserve_equipment_and_add_items(data.equipment, order.id, client.address_id)

        return order

    async def _create_address(self, location: str) -> Address:
        try:
            city, street, building = [x.strip() for x in location.split(",", 2)]
        except Exception as exc:
            raise UnprocessableEntityError("Адрес должен быть в формате: Город, Улица, Дом") from exc

        address = Address(city=city, street=street, building=building, lat=0.0, lon=0.0)
        self.session.add(address)
        await self.session.flush()
        return address

    async def _create_client(self, data: OrderCreate, address_id: UUID) -> Client:
        client = Client(name=data.name or "-", phone=data.phone, address_id=address_id)
        self.session.add(client)
        await self.session.flush()
        return client

    async def _create_order_entity(self, data: OrderCreate, client_id: UUID, status_id: int) -> Order:
        order = Order(
            client_id=client_id,
            rent_start=data.rent_start,
            rent_end=data.rent_end,
            window_start=data.window_start,
            window_end=data.window_end,
            status_id=status_id,
            comment=data.comment,
        )
        self.session.add(order)
        await self.session.flush()
        return order

    async def _create_invoice(self, order_id: UUID, status_id: int) -> None:
        invoice = Invoice(order_id=order_id, invoice_status_id=status_id)
        self.session.add(invoice)

    async def _add_order_history(self, order_id: UUID, new_status_id: int, user_id: UUID) -> None:
        await add_order_history(
            self.session,
            order_id=order_id,
            previous_status_id=None,
            new_status_id=new_status_id,
            user_id=user_id,
        )

    async def _get_status_id[T: BaseLookup](
        self,
        model: type[T],
        code: str,
        err_msg: str,
    ) -> int:
        status_id: int | None = await self.session.scalar(select(model.id).where(model.code == code))
        if status_id is None:
            raise InternalServerError(err_msg)
        return status_id

    async def _reserve_equipment_and_add_items(
        self,
        equipment_list: list[EquipmentList],
        order_id: UUID,
        address_id: UUID,
    ) -> None:
        for eq in equipment_list:
            heater_type: HeaterType | None = await self.session.scalar(
                select(HeaterType).where(HeaterType.model == eq.model)
            )
            if not heater_type:
                raise NotFoundError(f"Оборудование с моделью '{eq.model}' не найдено")

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
                raise ConflictError(f"Недостаточно оборудования модели '{eq.model}' на складе")

            reserved_status_id: int = await self._get_status_id(EquipmentStatus, "rented", "Статус 'rented' не найден")

            for equip in equipment_items:
                equip.current_address_id = address_id
                equip.equipment_status_id = reserved_status_id
                self.session.add(equip)

            item = OrderItem(order_id=order_id, heater_type_id=heater_type.id, quantity=eq.quantity)
            self.session.add(item)

    async def delete_order(self, order_id: UUID) -> None:
        await self.session.execute(delete(Order).where(Order.id == order_id))
        await self.session.commit()

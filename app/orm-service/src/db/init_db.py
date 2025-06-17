# src/db/init_db.py
import asyncio
from typing import Any, Sequence, Tuple

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import hash_password
from src.db.models import (
    Address,
    Base,
    EquipmentStatus,
    EventType,
    InvoiceStatus,
    OrderStatus,
    Role,
    TransportType,
    User,
    Warehouse,
)
from src.db.session import AsyncSessionFactory, engine

#  справочные наборы 
ROLES: Sequence[tuple[int, str]] = [
    (1, "admin"),
    (2, "manager"),
    (3, "courier"),
]
ORDER_STATUSES: list[tuple[int, str, str]] = [
    (1, "new", "Новый"),
    (2, "scheduled", "Запланирован"),
    (3, "on_delivery", "В доставке"),
    (4, "in_rent", "В аренде"),
    (5, "completed", "Завершён"),
    (6, "cancelled", "Отменён"),
    (7, "in_processing", "В обработке"),
]
EQUIPMENT_STATUSES: list[tuple[int, str, str]] = [
    (1, "rented", "В аренде"),
    (2, "maintenance", "На обслуживании"),
    (3, "available", "Доступно"),
    (4, "decommissioned", "Списано"),
]
INVOICE_STATUSES: list[tuple[int, str, str]] = [
    (1, "issued", "Выставлен"),
    (2, "paid", "Оплачен"),
    (3, "not_paid", "Не оплачен"),
]
EVENT_TYPES: list[tuple[int, str, str]] = [
    (1, "route_assigned", "Маршрут назначен"),
    (2, "departed", "Выезд"),
    (3, "arrived", "Прибытие"),
    (4, "installed", "Монтаж завершён"),
    (5, "picked_up", "Демонтаж завершён"),
]
TRANSPORT_TYPES: list[tuple[int, str, float, float]] = [
    (1, "walk", 5.0, 10.0),
    (2, "bike", 15.0, 15.0),
    (3, "scooter", 25.0, 25.0),
    (4, "car", 40.0, 300.0),
    (5, "van", 35.0, 800.0),
]


#  универсальные апсерты 
async def _upsert_simple(session: AsyncSession, model: Any, items: list[Any]) -> None:
    for item in items:
        stmt: Select[Tuple[Any]] = select(model).where(model.id == item[0])
        if not await session.scalar(stmt):
            session.add(model(id=item[0], code=item[1], description=item[2]))


async def _upsert_roles(session: AsyncSession) -> None:
    for role_id, name in ROLES:
        if not await session.scalar(select(Role).where(Role.id == role_id)):
            session.add(Role(id=role_id, name=name))


async def _upsert_transport(session: AsyncSession) -> None:
    for i, name, speed, capacity in TRANSPORT_TYPES:
        if not await session.scalar(select(TransportType).where(TransportType.id == i)):
            session.add(TransportType(id=i, name=name, avg_speed=speed, capacity=capacity))


async def _create_admin(session: AsyncSession) -> None:
    admin_email = "admin@example.com"
    if await session.scalar(select(User).where(User.email == admin_email)):
        return
    session.add(
        User(
            first_name="Админ",
            last_name="Системы",
            phone="+70000000000",
            email=admin_email,
            password_hash=hash_password("admin12345678"),
            role_id=1,
        )
    )


async def _create_first_address(session: AsyncSession) -> Address:
    """Создаём адрес №1, если его ещё нет, и возвращаем объект."""
    stmt: Select[Tuple[Any]] = select(Address).limit(1)
    addr: Address | None = await session.scalar(stmt)
    if addr:  # уже есть хоть один адрес — считаем его первым
        return addr

    addr = Address(
        street="Курчатова",
        building="1А",
        city="Москва",
        lat=55.7558,
        lon=37.6173,
    )
    session.add(addr)
    await session.flush()
    return addr


async def _create_warehouse(session: AsyncSession, addr: Address) -> None:
    """Создаём склад, если складов ещё нет (по-простому)."""
    if await session.scalar(select(Warehouse).limit(1)):
        return
    session.add(Warehouse(address_id=addr.id))


#  точка входа 
async def init_db() -> None:
    # создаём таблицы (если ещё нет)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # наполняем справочники, создаём адрес+склад и админа
    async with AsyncSessionFactory() as session:
        await _upsert_roles(session)
        await _upsert_simple(session, OrderStatus, ORDER_STATUSES)
        await _upsert_simple(session, EquipmentStatus, EQUIPMENT_STATUSES)
        await _upsert_simple(session, InvoiceStatus, INVOICE_STATUSES)
        await _upsert_simple(session, EventType, EVENT_TYPES)
        await _upsert_transport(session)

        # вставляем адрес и склад
        first_addr: Address = await _create_first_address(session)
        await _create_warehouse(session, first_addr)

        await _create_admin(session)
        await session.commit()


if __name__ == "__main__":
    asyncio.run(init_db())

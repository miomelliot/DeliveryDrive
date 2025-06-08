# src/repositories/equipment.py
from datetime import date
from typing import Any, Tuple
from uuid import UUID

from sqlalchemy import Result, Row, ScalarResult, Select, delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Address, Equipment, EquipmentStatus, HeaterType, Maintenance, Warehouse
from src.schemas.equipment import EquipmentCreate, EquipmentFilter
from src.schemas.equipment_chart import EquipmentChartRead
from src.utils.http_error import _raise_404, _raise_409, _raise_500
from src.utils.sqlalchemy_expr import location_expr


class EquipmentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session: AsyncSession = session

    async def add_equipment(self, data: EquipmentCreate) -> Equipment:
        async with self.session.begin():
            dup: UUID | None = await self.session.scalar(
                select(Equipment.id).where(Equipment.serial_number == data.serial_number)
            )
            if dup:
                _raise_409("Серийный номер уже существует")

            # 1. HeaterType (создаём при необходимости)
            heater_type: HeaterType | None = await self.session.scalar(
                select(HeaterType).where(HeaterType.model == data.model)
            )
            if not heater_type:
                heater_type = HeaterType(
                    model=data.model,
                    price=data.price,
                    weight=data.weight,
                )
                self.session.add(heater_type)
                await self.session.flush()

            # 2. «Available» статус
            status_id: int | None = await self.session.scalar(
                select(EquipmentStatus.id).where(EquipmentStatus.code == "available")
            )
            if status_id is None:
                _raise_500("Статус 'available' не найден в справочнике EquipmentStatus")

            # 3. Первый склад + его адрес
            warehouse: Warehouse | None = await self.session.scalar(select(Warehouse).limit(1))
            if warehouse is None:
                _raise_500("Не найдено ни одного склада – база не инициализирована")

            # 4. Сам объект оборудования
            equipment = Equipment(
                heater_type_id=heater_type.id,
                serial_number=data.serial_number,
                equipment_status_id=status_id,
                warehouse_id=warehouse.id,
                current_address_id=warehouse.address_id,
            )
            self.session.add(equipment)
            await self.session.flush()

            first_maintenance = Maintenance(
                equipment_id=equipment.id,
                date=date.today(),
            )
            self.session.add(first_maintenance)

        # вне контекста транзакции можно обновить объект
        await self.session.refresh(equipment)
        return equipment

    async def list_models_by_status(self, filter: EquipmentFilter) -> list[str]:
        stmt: Select[Tuple[str]] = select(HeaterType.model).join(Equipment).join(EquipmentStatus)

        if filter.status:
            stmt = stmt.where(EquipmentStatus.code == filter.status)

        stmt = stmt.distinct()
        result: ScalarResult[str] = await self.session.scalars(stmt)
        return list(result)

    async def delete_equipment(self, equipment_id: UUID) -> None:
        await self.session.execute(delete(Equipment).where(Equipment.id == equipment_id))
        await self.session.commit()

    async def decommission_equipment(self, equipment_id: UUID) -> EquipmentChartRead:
        # Получаем ID статуса "decommissioned"
        status_id: int | None = await self.session.scalar(
            select(EquipmentStatus.id).where(EquipmentStatus.code == "decommissioned")
        )
        if status_id is None:
            _raise_500("Статус 'decommissioned' не найден")

        # Обновляем статус оборудования
        await self.session.execute(
            update(Equipment).where(Equipment.id == equipment_id).values(equipment_status_id=status_id)
        )
        await self.session.commit()

        # Получаем актуальные данные по оборудованию
        row: Result[Tuple[UUID, date | None, str, float, float, str, str]] = await self.session.execute(
            select(
                Equipment.id,
                Maintenance.date,
                HeaterType.model,
                HeaterType.weight,
                HeaterType.price,
                location_expr().label("location"),
                EquipmentStatus.description.label("status"),
            )
            .join(Maintenance, Maintenance.equipment_id == Equipment.id)
            .join(HeaterType, HeaterType.id == Equipment.heater_type_id)
            .join(Address, Address.id == Equipment.current_address_id)
            .join(EquipmentStatus, EquipmentStatus.id == Equipment.equipment_status_id)
            .where(Equipment.id == equipment_id)
        )

        result: Row[Tuple[UUID, date | None, str, float, float, str, str]] | None = row.first()
        if result is None:
            _raise_404("Не удалось собрать информацию об оборудовании")

        return EquipmentChartRead.model_validate(result._asdict())

    async def send_to_service(self, equipment_id: UUID) -> EquipmentChartRead:
        # Получаем ID нужных статусов
        available_id: int | None = await self.session.scalar(
            select(EquipmentStatus.id).where(EquipmentStatus.code == "available")
        )
        maintenance_id: int | None = await self.session.scalar(
            select(EquipmentStatus.id).where(EquipmentStatus.code == "maintenance")
        )

        if available_id is None or maintenance_id is None:
            _raise_500("Не найдены необходимые статусы оборудования")

        # Получаем текущий статус оборудования
        current_status_id: int | None = await self.session.scalar(
            select(Equipment.equipment_status_id).where(Equipment.id == equipment_id)
        )
        if current_status_id is None:
            _raise_404("Оборудование не найдено")

        # Решаем, на какой статус переключить
        if current_status_id == available_id:
            new_status_id = maintenance_id
        elif current_status_id == maintenance_id:
            new_status_id = available_id
        else:
            _raise_409("Оборудование должно быть в статусе 'available' или 'maintenance'")

        # Обновляем статус
        await self.session.execute(
            update(Equipment).where(Equipment.id == equipment_id).values(equipment_status_id=new_status_id)
        )

        # Обновляем дату обслуживания только при возвращении из сервиса
        if new_status_id == available_id:
            await self.session.execute(
                update(Maintenance).where(Maintenance.equipment_id == equipment_id).values(date=date.today())
            )

        await self.session.commit()

        # Получаем актуальные данные для возврата
        row: Result[Tuple[UUID, date | None, str, float, float, Any, str]] = await self.session.execute(
            select(
                Equipment.id,
                Maintenance.date,
                HeaterType.model,
                HeaterType.weight,
                HeaterType.price,
                location_expr().label("location"),
                EquipmentStatus.description.label("status"),
            )
            .join(Maintenance, Maintenance.equipment_id == Equipment.id)
            .join(HeaterType, HeaterType.id == Equipment.heater_type_id)
            .join(Address, Address.id == Equipment.current_address_id)
            .join(EquipmentStatus, EquipmentStatus.id == Equipment.equipment_status_id)
            .where(Equipment.id == equipment_id)
        )

        result: Row[Tuple[UUID, date | None, str, float, float, Any, str]] | None = row.first()
        if result is None:
            _raise_404("Не удалось собрать информацию об оборудовании")

        return EquipmentChartRead.model_validate(result._asdict())

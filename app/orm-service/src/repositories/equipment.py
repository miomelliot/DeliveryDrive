# src/repositories/equipment.py
from datetime import date
from typing import Any, Tuple
from uuid import UUID

from sqlalchemy import Result, Row, ScalarResult, Select, case, delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Address, Equipment, EquipmentStatus, HeaterType, Maintenance, Warehouse
from src.schemas.equipment import EquipmentCreateAPI, EquipmentFilter, EquipmentReadAPI
from src.schemas.equipment_chart import EquipmentChartRead
from src.utils.http_error import ConflictError, InternalServerError, NotFoundError
from src.utils.sqlalchemy_expr import location_expr


class EquipmentRepository:
    async def add_equipment(self, session: AsyncSession, data: EquipmentCreateAPI) -> Equipment:
        dup: UUID | None = await session.scalar(
            select(Equipment.id).where(Equipment.serial_number == data.serial_number)
        )
        if dup:
            raise ConflictError("Серийный номер уже существует")

        # 1. HeaterType (создаём при необходимости)
        heater_type: HeaterType | None = await session.scalar(select(HeaterType).where(HeaterType.model == data.model))
        if not heater_type:
            heater_type = HeaterType(
                model=data.model,
                price=data.price,
                weight=data.weight,
            )
            session.add(heater_type)
            await session.flush()

        status_id: int | None = await session.scalar(
            select(EquipmentStatus.id).where(EquipmentStatus.code == "available")
        )
        if status_id is None:
            raise InternalServerError("Статус 'available' не найден в справочнике EquipmentStatus")

        warehouse: Warehouse | None = await session.scalar(select(Warehouse).limit(1))
        if warehouse is None:
            raise InternalServerError("Не найдено ни одного склада – база не инициализирована")

        equipment = Equipment(
            heater_type_id=heater_type.id,
            serial_number=data.serial_number,
            equipment_status_id=status_id,
            warehouse_id=warehouse.id,
            current_address_id=warehouse.address_id,
        )
        session.add(equipment)
        await session.flush()

        first_maintenance = Maintenance(
            equipment_id=equipment.id,
            date=date.today(),
        )
        session.add(first_maintenance)

        await session.refresh(equipment)
        return equipment

    async def list_all_models(self, session: AsyncSession) -> list[str]:
        stmt: Select[Tuple[str]] = select(HeaterType.model).distinct()
        result: ScalarResult[str] = await session.scalars(stmt)
        return list(result)

    async def list_models_with_count(self, session: AsyncSession, filter: EquipmentFilter) -> list[EquipmentReadAPI]:
        stmt: Select[Tuple[str, float, float, int, int]] = (
            select(
                HeaterType.model,
                HeaterType.price,
                HeaterType.weight,
                func.count(Equipment.id).label("count"),
                func.count(case((EquipmentStatus.code == "available", 1))).label("count_available"),
            )
            .join(Equipment, HeaterType.id == Equipment.heater_type_id)
            .join(EquipmentStatus, EquipmentStatus.id == Equipment.equipment_status_id)
            .group_by(HeaterType.model, HeaterType.price, HeaterType.weight)
        )

        if filter.status:
            stmt = stmt.where(EquipmentStatus.code == filter.status)

        result: Result[Tuple[str, float, float, int, int]] = await session.execute(stmt)
        return [EquipmentReadAPI.model_validate(row._asdict()) for row in result.all()]

    async def delete_equipment(self, session: AsyncSession, equipment_id: UUID) -> None:
        await session.execute(delete(Equipment).where(Equipment.id == equipment_id))

    async def decommission_equipment(self, session: AsyncSession, equipment_id: UUID) -> EquipmentChartRead:
        # Получаем ID статуса "decommissioned"
        status_id: int | None = await session.scalar(
            select(EquipmentStatus.id).where(EquipmentStatus.code == "decommissioned")
        )
        if status_id is None:
            raise InternalServerError("Статус 'decommissioned' не найден")

        # Обновляем статус оборудования
        await session.execute(
            update(Equipment).where(Equipment.id == equipment_id).values(equipment_status_id=status_id)
        )

        # Получаем актуальные данные по оборудованию
        row: Result[Tuple[UUID, date | None, str, float, float, str, str]] = await session.execute(
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
            raise NotFoundError("Не удалось собрать информацию об оборудовании")

        return EquipmentChartRead.model_validate(result._asdict())

    async def send_to_service(self, session: AsyncSession, equipment_id: UUID) -> EquipmentChartRead:
        # Получаем ID нужных статусов
        available_id: int | None = await session.scalar(
            select(EquipmentStatus.id).where(EquipmentStatus.code == "available")
        )
        maintenance_id: int | None = await session.scalar(
            select(EquipmentStatus.id).where(EquipmentStatus.code == "maintenance")
        )

        if available_id is None or maintenance_id is None:
            raise InternalServerError("Не найдены необходимые статусы оборудования")

        # Получаем текущий статус оборудования
        current_status_id: int | None = await session.scalar(
            select(Equipment.equipment_status_id).where(Equipment.id == equipment_id)
        )
        if current_status_id is None:
            raise NotFoundError("Оборудование не найдено")

        # Решаем, на какой статус переключить
        if current_status_id == available_id:
            new_status_id = maintenance_id
        elif current_status_id == maintenance_id:
            new_status_id = available_id
        else:
            raise ConflictError("Оборудование должно быть в статусе 'available' или 'maintenance'")

        # Обновляем статус
        await session.execute(
            update(Equipment).where(Equipment.id == equipment_id).values(equipment_status_id=new_status_id)
        )

        # Обновляем дату обслуживания только при возвращении из сервиса
        if new_status_id == available_id:
            await session.execute(
                update(Maintenance).where(Maintenance.equipment_id == equipment_id).values(date=date.today())
            )

        # Получаем актуальные данные для возврата
        row: Result[Tuple[UUID, date | None, str, float, float, Any, str]] = await session.execute(
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
            raise NotFoundError("Не удалось собрать информацию об оборудовании")

        return EquipmentChartRead.model_validate(result._asdict())

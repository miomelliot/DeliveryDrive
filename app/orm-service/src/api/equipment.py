# src/api/equipment.py
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.dependencies.db import get_session_with_user
from src.repositories.equipment import EquipmentRepository
from src.schemas.equipment import EquipmentCreateAPI, EquipmentFilter, EquipmentReadAPI
from src.schemas.equipment_chart import EquipmentChartRead

router = APIRouter(prefix="/equipment", tags=["Equipment"])


@router.post("/", response_model=None)
async def add_equipment(
    data: EquipmentCreateAPI,
    session: AsyncSession = Depends(get_session_with_user),
) -> dict[str, str]:
    await EquipmentRepository().add_equipment(session, data)
    return {"detail": "Оборудование добавлено на склад"}


@router.get("/models/distinct", response_model=list[str])
async def get_all_models(
    session: AsyncSession = Depends(get_session_with_user),
) -> list[str]:
    return await EquipmentRepository().list_all_models(session)


@router.get("/models/info", response_model=list[EquipmentReadAPI])
async def get_models_by_status(
    filter: EquipmentFilter = Depends(),
    session: AsyncSession = Depends(get_session_with_user),
) -> list[EquipmentReadAPI]:
    return await EquipmentRepository().list_models_with_count(session, filter)


@router.delete("/{equipment_id}", response_model=dict[str, str])
async def delete_equipment(
    equipment_id: UUID,
    session: AsyncSession = Depends(get_session_with_user),
) -> dict[str, str]:
    await EquipmentRepository().delete_equipment(session, equipment_id)
    return {"detail": "Оборудование удалено"}


@router.patch("/{equipment_id}/decommission", response_model=EquipmentChartRead)
async def decommission_equipment(
    equipment_id: UUID,
    session: AsyncSession = Depends(get_session_with_user),
) -> EquipmentChartRead:
    return await EquipmentRepository().decommission_equipment(session, equipment_id)


@router.patch("/{equipment_id}/toggle-maintenance", response_model=EquipmentChartRead)
async def toggle_equipment_maintenance(
    equipment_id: UUID,
    session: AsyncSession = Depends(get_session_with_user),
) -> EquipmentChartRead:
    return await EquipmentRepository().send_to_service(session, equipment_id)

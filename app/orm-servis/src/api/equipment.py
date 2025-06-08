# src/api/equipment.py
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_session
from src.repositories.equipment import EquipmentRepository
from src.schemas.equipment import EquipmentCreate, EquipmentFilter
from src.schemas.equipment_chart import EquipmentChartRead
from src.utils.http_error import _raise_400

router = APIRouter(prefix="/equipment", tags=["Equipment"])


@router.post("/", response_model=None)
async def add_equipment(
    data: EquipmentCreate,
    session: AsyncSession = Depends(get_session),
) -> dict[str, str]:
    repo = EquipmentRepository(session)
    try:
        await repo.add_equipment(data)
        return {"detail": "Оборудование добавлено на склад"}
    except ValueError as e:
        _raise_400(e)


@router.get("/models/", response_model=list[str])
async def list_models_by_status(
    filter: EquipmentFilter = Depends(),
    session: AsyncSession = Depends(get_session),
) -> list[str]:
    repo = EquipmentRepository(session)
    try:
        return await repo.list_models_by_status(filter)
    except ValueError as e:
        _raise_400(e)


@router.delete("/{equipment_id}", response_model=dict[str, str])
async def delete_equipment(
    equipment_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> dict[str, str]:
    repo = EquipmentRepository(session)
    try:
        await repo.delete_equipment(equipment_id)
        return {"detail": "Оборудование удалено"}
    except ValueError as e:
        _raise_400(e)


@router.patch("/{equipment_id}/decommission", response_model=EquipmentChartRead)
async def decommission_equipment(
    equipment_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> EquipmentChartRead:
    repo = EquipmentRepository(session)
    try:
        return await repo.decommission_equipment(equipment_id)
    except ValueError as e:
        _raise_400(e)


@router.patch("/{equipment_id}/toggle-maintenance", response_model=EquipmentChartRead)
async def toggle_equipment_maintenance(
    equipment_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> EquipmentChartRead:
    repo = EquipmentRepository(session)
    try:
        return await repo.send_to_service(equipment_id)
    except ValueError as e:
        _raise_400(e)

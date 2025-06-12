# src/api/equipment.py
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_session
from src.dependencies.auth import get_current_user
from src.repositories.equipment import EquipmentRepository
from src.schemas.fastapi.auth import CurrentUser
from src.schemas.fastapi.equipment import EquipmentCreate, EquipmentFilter, EquipmentRead
from src.schemas.fastapi.equipment_chart import EquipmentChartRead

router = APIRouter(prefix="/equipment", tags=["Equipment"])


@router.post("/", response_model=None)
async def add_equipment(
    data: EquipmentCreate,
    session: AsyncSession = Depends(get_session),
    current_user: CurrentUser = Depends(get_current_user),
) -> dict[str, str]:
    repo = EquipmentRepository(session)
    await repo.add_equipment(data)
    return {"detail": "Оборудование добавлено на склад"}


@router.get("/models/distinct", response_model=list[str])
async def get_all_models(
    session: AsyncSession = Depends(get_session),
    current_user: CurrentUser = Depends(get_current_user),
) -> list[str]:
    repo = EquipmentRepository(session)
    return await repo.list_all_models()


@router.get("/models/info", response_model=list[EquipmentRead])
async def get_models_by_status(
    filter: EquipmentFilter = Depends(),
    session: AsyncSession = Depends(get_session),
    current_user: CurrentUser = Depends(get_current_user),
) -> list[EquipmentRead]:
    repo = EquipmentRepository(session)
    return await repo.list_models_with_count(filter)


@router.delete("/{equipment_id}", response_model=dict[str, str])
async def delete_equipment(
    equipment_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: CurrentUser = Depends(get_current_user),
) -> dict[str, str]:
    repo = EquipmentRepository(session)
    await repo.delete_equipment(equipment_id)
    return {"detail": "Оборудование удалено"}


@router.patch("/{equipment_id}/decommission", response_model=EquipmentChartRead)
async def decommission_equipment(
    equipment_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: CurrentUser = Depends(get_current_user),
) -> EquipmentChartRead:
    repo = EquipmentRepository(session)
    return await repo.decommission_equipment(equipment_id)


@router.patch("/{equipment_id}/toggle-maintenance", response_model=EquipmentChartRead)
async def toggle_equipment_maintenance(
    equipment_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: CurrentUser = Depends(get_current_user),
) -> EquipmentChartRead:
    repo = EquipmentRepository(session)
    return await repo.send_to_service(equipment_id)

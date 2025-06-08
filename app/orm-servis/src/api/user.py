# src/api/user.py
from typing import NoReturn
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_session
from src.repositories.user import UserCourierRepository, UserManagerRepository
from src.schemas.user import (
    UserCourierCreate,
    UserCourierRead,
    UserCourierUpdate,
    UserManagerCreate,
    UserManagerRead,
    UserManagerUpdate,
)

router = APIRouter(prefix="/user", tags=["User"])


# ────────────────────────── helpers ──────────────────────────
def _raise_400(exc: ValueError) -> NoReturn:
    """Преобразуем ValueError → HTTP 400 (никогда не возвращает)."""
    raise HTTPException(status_code=400, detail=str(exc)) from exc


# ─────────────────────────── MANAGER ───────────────────────────
@router.post(
    "/manager",
    response_model=UserManagerRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_manager_user(
    data: UserManagerCreate = Depends(),
    icon: UploadFile | None = None,
    session: AsyncSession = Depends(get_session),
) -> UserManagerRead:
    repo = UserManagerRepository(session)
    try:
        return await repo.create(data, icon)
    except ValueError as e:
        _raise_400(e)


@router.patch("/manager/{user_id}", response_model=UserManagerRead)
async def update_manager_user(
    user_id: UUID,
    data: UserManagerUpdate = Depends(),
    icon: UploadFile | None = None,
    session: AsyncSession = Depends(get_session),
) -> UserManagerRead:
    repo = UserManagerRepository(session)
    try:
        result: UserManagerRead | None = await repo.update(user_id, data, icon)
    except ValueError as e:
        _raise_400(e)
    if result is None:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return result


@router.get("/manager", response_model=list[UserManagerRead])
async def list_managers(session: AsyncSession = Depends(get_session)) -> list[UserManagerRead]:
    return await UserManagerRepository(session).list()


@router.get("/manager/{user_id}", response_model=UserManagerRead)
async def get_manager(user_id: UUID, session: AsyncSession = Depends(get_session)) -> UserManagerRead:
    result: UserManagerRead | None = await UserManagerRepository(session).get(user_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return result


# ─────────────────────────── COURIER ───────────────────────────
@router.post(
    "/courier",
    response_model=UserCourierRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_courier_user(
    data: UserCourierCreate = Depends(),
    icon: UploadFile | None = None,
    session: AsyncSession = Depends(get_session),
) -> UserCourierRead:
    repo = UserCourierRepository(session)
    try:
        return await repo.create(data, icon)
    except ValueError as e:
        _raise_400(e)


@router.patch("/courier/{user_id}", response_model=UserCourierRead)
async def update_courier_user(
    user_id: UUID,
    data: UserCourierUpdate = Depends(),
    icon: UploadFile | None = None,
    session: AsyncSession = Depends(get_session),
) -> UserCourierRead:
    repo = UserCourierRepository(session)
    try:
        result: UserCourierRead | None = await repo.update(user_id, data, icon)
    except ValueError as e:
        _raise_400(e)
    if result is None:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return result


@router.get("/courier", response_model=list[UserCourierRead])
async def list_couriers(session: AsyncSession = Depends(get_session)) -> list[UserCourierRead]:
    return await UserCourierRepository(session).list()


@router.get("/courier/{user_id}", response_model=UserCourierRead)
async def get_courier(user_id: UUID, session: AsyncSession = Depends(get_session)) -> UserCourierRead:
    result: UserCourierRead | None = await UserCourierRepository(session).get(user_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return result


# ─────────────────────────── DELETE ───────────────────────────
@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: UUID, session: AsyncSession = Depends(get_session)) -> None:
    """Удалить любого пользователя по ID."""
    await UserManagerRepository(session).delete(user_id)

# src/api/user.py
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.dependencies.auth import get_current_user
from src.dependencies.db import get_session_with_user
from src.repositories.user import UserBaseRepository, UserCourierRepository, UserManagerRepository
from src.schemas.auth import CurrentUser
from src.schemas.user import (
    UserCourierCreate,
    UserCourierRead,
    UserCourierUpdate,
    UserManagerCreate,
    UserManagerRead,
    UserManagerUpdate,
)

router = APIRouter(prefix="/user", tags=["User"])


# ─────────────────────────── MANAGER ───────────────────────────
@router.post(
    "/manager",
    response_model=UserManagerRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_manager_user(
    data: UserManagerCreate = Depends(),
    icon: UploadFile | None = None,
    session: AsyncSession = Depends(get_session_with_user),
    current_user: CurrentUser = Depends(get_current_user),
) -> UserManagerRead:
    repo = UserManagerRepository(session)
    return await repo.create(data, icon)


@router.patch("/manager/{user_id}", response_model=UserManagerRead)
async def update_manager_user(
    user_id: UUID,
    data: UserManagerUpdate = Depends(),
    icon: UploadFile | None = None,
    session: AsyncSession = Depends(get_session_with_user),
    current_user: CurrentUser = Depends(get_current_user),
) -> UserManagerRead:
    repo = UserManagerRepository(session)
    result: UserManagerRead | None = await repo.update(user_id, data, icon)
    if result is None:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return result


@router.get("/manager", response_model=list[UserManagerRead])
async def list_managers(
    session: AsyncSession = Depends(get_session_with_user),
    current_user: CurrentUser = Depends(get_current_user),
) -> list[UserManagerRead]:
    return await UserManagerRepository(session).list()


@router.get("/manager/{user_id}", response_model=UserManagerRead)
async def get_manager(
    user_id: UUID,
    session: AsyncSession = Depends(get_session_with_user),
    current_user: CurrentUser = Depends(get_current_user),
) -> UserManagerRead:
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
    session: AsyncSession = Depends(get_session_with_user),
    current_user: CurrentUser = Depends(get_current_user),
) -> UserCourierRead:
    repo = UserCourierRepository(session)
    return await repo.create(data, icon)


@router.patch("/courier/{user_id}", response_model=UserCourierRead)
async def update_courier_user(
    user_id: UUID,
    data: UserCourierUpdate = Depends(),
    icon: UploadFile | None = None,
    session: AsyncSession = Depends(get_session_with_user),
    current_user: CurrentUser = Depends(get_current_user),
) -> UserCourierRead:
    repo = UserCourierRepository(session)
    result: UserCourierRead | None = await repo.update(user_id, data, icon)
    if result is None:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return result


@router.get("/courier", response_model=list[UserCourierRead])
async def list_couriers(
    session: AsyncSession = Depends(get_session_with_user),
    current_user: CurrentUser = Depends(get_current_user),
) -> list[UserCourierRead]:
    return await UserCourierRepository(session).list()


@router.get("/courier/{user_id}", response_model=UserCourierRead)
async def get_courier(
    user_id: UUID,
    session: AsyncSession = Depends(get_session_with_user),
    current_user: CurrentUser = Depends(get_current_user),
) -> UserCourierRead:
    result: UserCourierRead | None = await UserCourierRepository(session).get(user_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return result


# ─────────────────────────── DELETE ───────────────────────────
@router.delete("/{user_id}", status_code=200)
async def delete_user(
    user_id: UUID,
    session: AsyncSession = Depends(get_session_with_user),
    current_user: CurrentUser = Depends(get_current_user),
) -> JSONResponse:
    """Удалить любого пользователя по ID (404, если не найден)."""
    deleted: bool = await UserBaseRepository(session).delete(user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    return JSONResponse(content={"message": "Пользователь успешно удалён"})

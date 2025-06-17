# src/api/user.py
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.dependencies.db import get_session_with_user
from src.repositories.user import UserBaseRepository, UserCourierRepository, UserManagerRepository
from src.schemas.user import (
    UserCourierCreate,
    UserCourierRead,
    UserCourierUpdate,
    UserManagerCreate,
    UserManagerRead,
    UserManagerUpdate,
)

router = APIRouter(prefix="/user", tags=["User"])


#  MANAGER 
@router.post(
    "/manager",
    response_model=UserManagerRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_manager_user(
    data: UserManagerCreate = Depends(),
    icon: UploadFile | None = None,
    session: AsyncSession = Depends(get_session_with_user),
) -> UserManagerRead:
    repo: UserManagerRead = await UserManagerRepository().create(session, data, icon)
    return repo


@router.patch("/manager/{user_id}", response_model=UserManagerRead)
async def update_manager_user(
    user_id: UUID,
    data: UserManagerUpdate = Depends(),
    icon: UploadFile | None = None,
    session: AsyncSession = Depends(get_session_with_user),
) -> UserManagerRead:
    repo = UserManagerRepository()
    result: UserManagerRead | None = await repo.update(session, user_id, data, icon)
    if result is None:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return result


@router.get("/manager", response_model=list[UserManagerRead])
async def list_managers(
    session: AsyncSession = Depends(get_session_with_user),
) -> list[UserManagerRead]:
    return await UserManagerRepository().list(session)


@router.get("/manager/{user_id}", response_model=UserManagerRead)
async def get_manager(
    user_id: UUID,
    session: AsyncSession = Depends(get_session_with_user),
) -> UserManagerRead:
    result: UserManagerRead | None = await UserManagerRepository().get(session, user_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return result


#  COURIER 
@router.post(
    "/courier",
    response_model=UserCourierRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_courier_user(
    data: UserCourierCreate = Depends(),
    icon: UploadFile | None = None,
    session: AsyncSession = Depends(get_session_with_user),
) -> UserCourierRead:
    repo = UserCourierRepository()
    return await repo.create(session, data, icon)


@router.patch("/courier/{user_id}", response_model=UserCourierRead)
async def update_courier_user(
    user_id: UUID,
    data: UserCourierUpdate = Depends(),
    icon: UploadFile | None = None,
    session: AsyncSession = Depends(get_session_with_user),
) -> UserCourierRead:
    repo = UserCourierRepository()
    result: UserCourierRead | None = await repo.update(session, user_id, data, icon)
    if result is None:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return result


@router.get("/courier", response_model=list[UserCourierRead])
async def list_couriers(
    session: AsyncSession = Depends(get_session_with_user),
) -> list[UserCourierRead]:
    return await UserCourierRepository().list(session)


@router.get("/courier/{user_id}", response_model=UserCourierRead)
async def get_courier(
    user_id: UUID,
    session: AsyncSession = Depends(get_session_with_user),
) -> UserCourierRead:
    result: UserCourierRead | None = await UserCourierRepository().get(session, user_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return result


#  DELETE 
@router.delete("/{user_id}", status_code=200)
async def delete_user(
    user_id: UUID,
    session: AsyncSession = Depends(get_session_with_user),
) -> JSONResponse:
    """Удалить любого пользователя по ID (404, если не найден)."""
    deleted: bool = await UserBaseRepository().delete(session, user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    return JSONResponse(content={"message": "Пользователь успешно удалён"})

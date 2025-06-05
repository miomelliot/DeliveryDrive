# src/api/user.py
from typing import Sequence
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import User
from src.db.session import get_session
from src.repositories.user import UserRepository
from src.schemas.user import UserCreate, UserRead, UserUpdate

router = APIRouter(prefix="/users", tags=["Users"])


def get_user_repo(session: AsyncSession = Depends(get_session)) -> UserRepository:
    return UserRepository(session)


@router.get("/", response_model=list[UserRead])
async def list_users(repo: UserRepository = Depends(get_user_repo)) -> list[UserRead]:
    users: Sequence[User] = await repo.get_all()
    return [UserRead.model_validate(user) for user in users]


@router.get("/{user_id}", response_model=UserRead)
async def get_user(user_id: UUID, repo: UserRepository = Depends(get_user_repo)) -> UserRead:
    user: User | None = await repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return UserRead.model_validate(user)


@router.post("/", response_model=UserRead)
async def create_user(data: UserCreate, repo: UserRepository = Depends(get_user_repo)) -> UserRead:
    existing: User | None = await repo.get_by_email(data.email)
    if existing:
        raise HTTPException(status_code=409, detail="Пользователь с таким email уже существует")
    user: User = await repo.create(data)
    return UserRead.model_validate(user)


@router.patch("/{user_id}", response_model=UserRead)
async def update_user(user_id: UUID, data: UserUpdate, repo: UserRepository = Depends(get_user_repo)) -> UserRead:
    updated: User | None = await repo.update(user_id, data)
    if not updated:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return UserRead.model_validate(updated)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: UUID, repo: UserRepository = Depends(get_user_repo)) -> None:
    user: User | None = await repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    await repo.delete(user_id)

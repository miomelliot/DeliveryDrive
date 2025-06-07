# src/repositories/user.py
from typing import Any, Tuple
from uuid import UUID

import aiofiles
from fastapi import UploadFile
from sqlalchemy import ScalarResult, select
from sqlalchemy import delete as sa_delete
from sqlalchemy import update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.dml import ReturningUpdate
from uuid6 import uuid7

from src.core.security import hash_password
from src.db.models import Role, User
from src.schemas.user import UserCourierCreate, UserCourierUpdate, UserManagerCreate, UserManagerUpdate


class UserBaseRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session: AsyncSession = session

    async def get_all(self) -> list[User]:
        result: ScalarResult[User] = await self.session.scalars(select(User))
        return list(result.all())

    async def get_by_id(self, user_id: UUID) -> User | None:
        return await self.session.get(User, user_id)

    async def delete(self, user_id: UUID) -> None:
        await self.session.execute(sa_delete(User).where(User.id == user_id))
        await self.session.commit()

    async def _get_role(self, name: str) -> Role:
        role: Role | None = await self.session.scalar(select(Role).where(Role.name == name))
        if not role:
            raise ValueError(f"Role '{name}' not found")
        return role

    async def _save_icon(self, user_id: UUID, icon: UploadFile) -> str:
        path: str = f"/static/icons/{user_id}.png"
        async with aiofiles.open(path, "wb") as f:
            await f.write(await icon.read())
        return path


class UserManagerRepository(UserBaseRepository):
    async def create(self, data: UserManagerCreate, icon: UploadFile | None) -> User:
        role: Role = await self._get_role("manager")
        user = User(
            id=uuid7(),
            first_name=data.first_name,
            last_name=data.last_name,
            phone=data.phone,
            email=data.email,
            password_hash=hash_password(data.password),
            role_id=role.id,
            icon=await self._save_icon(uuid7(), icon) if icon else None,
        )
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def update(self, user_id: UUID, data: UserManagerUpdate, icon: UploadFile | None) -> User | None:
        values: dict[str, Any] = data.model_dump(exclude_unset=True, exclude_none=True)
        if "password" in values:
            values["password_hash"] = hash_password(values.pop("password"))
        if icon:
            values["icon"] = await self._save_icon(user_id, icon)
        stmt: ReturningUpdate[Tuple[User]] = sa_update(User).where(User.id == user_id).values(**values).returning(User)
        user: User | None = await self.session.scalar(stmt)
        await self.session.commit()
        return user


class UserCourierRepository(UserBaseRepository):
    async def create(self, data: UserCourierCreate, icon: UploadFile | None) -> User:
        role: Role = await self._get_role("courier")
        user = User(
            id=uuid7(),
            first_name=data.first_name,
            last_name=data.last_name,
            phone=data.phone,
            email=data.email,
            password_hash=hash_password(data.password),
            role_id=role.id,
            start_time=data.start_time,
            end_time=data.end_time,
            transport_name=data.transport_name,
            icon=await self._save_icon(uuid7(), icon) if icon else None,
        )
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def update(self, user_id: UUID, data: UserCourierUpdate, icon: UploadFile | None) -> User | None:
        values: dict[str, Any] = data.model_dump(exclude_unset=True, exclude_none=True)
        if "password" in values:
            values["password_hash"] = hash_password(values.pop("password"))
        if icon:
            values["icon"] = await self._save_icon(user_id, icon)
        stmt: ReturningUpdate[Tuple[User]] = sa_update(User).where(User.id == user_id).values(**values).returning(User)
        user: User | None = await self.session.scalar(stmt)
        await self.session.commit()
        return user

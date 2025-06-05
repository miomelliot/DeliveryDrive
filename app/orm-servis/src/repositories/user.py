# src/repositories/user.py
from typing import Any, Tuple
from uuid import UUID

from sqlalchemy import ScalarResult, Select, select
from sqlalchemy import delete as sa_delete
from sqlalchemy import update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.dml import ReturningUpdate
from uuid6 import uuid7

from src.core.security import hash_password
from src.db.models import Role, User
from src.schemas.user import UserCreate, UserUpdate


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session: AsyncSession = session

    async def get_all(self) -> list[User]:
        result: ScalarResult[User] = await self.session.scalars(select(User))
        return list(result.all())

    async def get_by_id(self, user_id: UUID) -> User | None:
        return await self.session.get(User, user_id)

    async def get_by_email(self, email: str) -> User | None:
        stmt: Select[Tuple[User]] = select(User).where(User.email == email)
        result: ScalarResult[User] = await self.session.scalars(stmt)
        return result.first()

    async def create(self, data: UserCreate) -> User:
        role: Role | None = await self._get_role_by_name(data.role_name)
        if role is None:
            raise ValueError(f"Роль '{data.role_name}' не найдена")

        user = User(
            id=uuid7(),
            first_name=data.first_name,
            last_name=data.last_name,
            email=data.email,
            phone=data.phone,
            password_hash=hash_password(data.password),
            role_id=role.id,
        )

        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def update(self, user_id: UUID, data: UserUpdate) -> User | None:
        values: dict[str, Any] = data.model_dump(exclude_unset=True, exclude_none=True)

        if "role_name" in values:
            role: Role | None = await self._get_role_by_name(values.pop("role_name"))
            if role is None:
                raise ValueError("Указанная роль не существует")
            values["role_id"] = role.id

        if "password" in values:
            values["password_hash"] = hash_password(values.pop("password"))

        stmt: ReturningUpdate[Tuple[User]] = sa_update(User).where(User.id == user_id).values(**values).returning(User)

        result: User | None = await self.session.scalar(stmt)
        await self.session.commit()
        return result

    async def delete(self, user_id: UUID) -> None:
        await self.session.execute(sa_delete(User).where(User.id == user_id))
        await self.session.commit()

    async def _get_role_by_name(self, role_name: str) -> Role | None:
        result: ScalarResult[Role] = await self.session.scalars(select(Role).where(Role.name == role_name))
        return result.first()

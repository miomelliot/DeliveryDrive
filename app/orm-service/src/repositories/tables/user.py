# src/repositories/tables/user.py
from datetime import time
from pathlib import Path
from sqlite3 import IntegrityError
from typing import Tuple
from uuid import UUID

import aiofiles
from fastapi import UploadFile
from sqlalchemy import Select, select
from sqlalchemy import update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import hash_password
from src.db.models import CourierSchedule, Role, Transport, TransportType, User
from src.repositories.tables.base import CRUDRepository
from src.schemas.user import (
    UserCourierCreateAPI,
    UserCourierRead,
    UserCreate,
    UserCreateAPI,
    UserManagerRead,
    UserUpdate,
    UserUpdateAPI,
)
from src.utils.http_error import ConflictError, InternalServerError, NotFoundError

SAVE_DIR = Path("/app/static/icons")


class UserBaseRepository:
    async def _get_role(self, session: AsyncSession, name: str) -> Role:
        role: Role | None = await session.scalar(select(Role).where(Role.name == name))
        if role is None:
            raise NotFoundError()
        return role

    async def _save_icon(self, user_id: UUID, avatar_path: UploadFile) -> str:
        """Сохраняем файл /app/static/icons/<id>.png и возвращаем URL."""
        SAVE_DIR.mkdir(parents=True, exist_ok=True)
        file_path: Path = SAVE_DIR / f"{user_id}.png"
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(await avatar_path.read())
        return f"/static/icons/{user_id}.png"


class UserRepository(UserBaseRepository, CRUDRepository[User, UserCreate, UserUpdate]):
    def __init__(self) -> None:
        super().__init__(User)

    async def create_extended(
        self,
        session: AsyncSession,
        raw_data: UserCreateAPI | UserCourierCreateAPI,
        avatar_path: UploadFile | None,
        role_name: str,
    ) -> User:
        role: Role = await super()._get_role(session, role_name)

        obj_in = UserCreate(
            first_name=raw_data.first_name,
            last_name=raw_data.last_name,
            phone=raw_data.phone,
            email=raw_data.email,
            password_hash=hash_password(raw_data.password),
            role_id=role.id,
        )

        try:
            user: User = await super().create(session, obj_in)
        except IntegrityError as err:
            if "email" in str(err):
                raise ConflictError(f"Email уже используется: {obj_in.email}") from err
            raise InternalServerError() from err

        if avatar_path:
            await super()._save_icon(user.id, avatar_path)

        if isinstance(raw_data, UserCourierCreateAPI):
            pass

        return user

    async def update_by_id_extended(
        self, session: AsyncSession, id: UUID, raw_data: UserUpdateAPI, avatar_path: UploadFile | None
    ) -> User:
        if raw_data.password:
            raw_data.password = hash_password(raw_data.password)

        obj_in = UserUpdate(
            first_name=raw_data.first_name,
            last_name=raw_data.last_name,
            phone=raw_data.phone,
            email=raw_data.email,
            password_hash=raw_data.password,
        )

        if avatar_path:
            await super()._save_icon(id, avatar_path)
        return await super().update_by_id(session, id, obj_in)

    async def _get_transport_type(self, session: AsyncSession, name: str) -> TransportType:
        tt: TransportType | None = await session.scalar(select(TransportType).where(TransportType.name == name))
        if tt is None:
            raise NotFoundError(f"Тип транспорта «{name}» не найден")
        return tt

    async def _upsert_schedule(
        self, session: AsyncSession, user_id: UUID, start: time | None, end: time | None
    ) -> None:
        sched_vals: dict[str, time] = {k: v for k, v in {"start_time": start, "end_time": end}.items() if v is not None}

        if sched_vals:
            await session.execute(
                sa_update(CourierSchedule).where(CourierSchedule.courier_id == user_id).values(**sched_vals)
            )

    async def _upsert_transport(self, session: AsyncSession, user_id: UUID, transport_name: str | None) -> str:
        if transport_name:
            tt: TransportType = await self._get_transport_type(session, transport_name)
            await session.execute(
                sa_update(Transport).where(Transport.courier_id == user_id).values(transport_type_id=tt.id)
            )
            return tt.name
        else:
            tt_existing: TransportType | None = await session.scalar(
                select(TransportType)
                .join(Transport, Transport.transport_type_id == TransportType.id)
                .where(Transport.courier_id == user_id)
            )
            if tt_existing is None:
                raise NotFoundError(f"Тип транспорта не найден для курьера {user_id}")
            return tt_existing.name

    async def get_user(self, session: AsyncSession, user_id: UUID) -> UserManagerRead | UserCourierRead | None:
        stmt: Select[Tuple[User, str]] = (
            select(User, Role.name).join(Role, Role.id == User.role_id).where(User.id == user_id)
        )
        result = await session.scalar(stmt)
        if result is None:
            return None

        user, role_name = result

        if role_name == "manager":
            return UserManagerRead(
                id=user.id,
                first_name=user.first_name,
                last_name=user.last_name,
                phone=user.phone,
                email=user.email,
                avatar_path=user.avatar_path,
            )

        elif role_name == "courier":
            sched: CourierSchedule | None = await session.scalar(
                select(CourierSchedule).where(CourierSchedule.courier_id == user.id)
            )
            tt_name: str | None = await session.scalar(
                select(TransportType.name)
                .join(Transport, Transport.transport_type_id == TransportType.id)
                .where(Transport.courier_id == user.id)
            )

            if sched is None or tt_name is None:
                raise ValueError(f"Данные по курьеру {user.id} неполные")

            return UserCourierRead(
                id=user.id,
                first_name=user.first_name,
                last_name=user.last_name,
                phone=user.phone,
                email=user.email,
                avatar_path=user.avatar_path,
                start_time=sched.start_time,
                end_time=sched.end_time,
                transport_name=tt_name,
            )

        else:
            raise ValueError(f"Неизвестная роль: {role_name}")

    async def list_users(self, session: AsyncSession) -> list[UserManagerRead | UserCourierRead]:
        stmt = select(User, Role.name).join(Role, Role.id == User.role_id)
        result = await session.execute(stmt)

        output: list[UserManagerRead | UserCourierRead] = []

        for user, role_name in result:
            if role_name == "manager":
                output.append(
                    UserManagerRead(
                        id=user.id,
                        first_name=user.first_name,
                        last_name=user.last_name,
                        phone=user.phone,
                        email=user.email,
                        avatar_path=user.avatar_path,
                    )
                )
            elif role_name == "courier":
                sched: CourierSchedule | None = await session.scalar(
                    select(CourierSchedule).where(CourierSchedule.courier_id == user.id)
                )
                tt_name: str | None = await session.scalar(
                    select(TransportType.name)
                    .join(Transport, Transport.transport_type_id == TransportType.id)
                    .where(Transport.courier_id == user.id)
                )

                if sched and tt_name:
                    output.append(
                        UserCourierRead(
                            id=user.id,
                            first_name=user.first_name,
                            last_name=user.last_name,
                            phone=user.phone,
                            email=user.email,
                            avatar_path=user.avatar_path,
                            start_time=sched.start_time,
                            end_time=sched.end_time,
                            transport_name=tt_name,
                        )
                    )
            else:
                continue

        return output

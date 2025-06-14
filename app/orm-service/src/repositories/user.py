from datetime import time
from pathlib import Path
from typing import Any, Tuple
from uuid import UUID

import aiofiles
from fastapi import UploadFile
from sqlalchemy import Result, ScalarResult, Select, select
from sqlalchemy import delete as sa_delete
from sqlalchemy import update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.dml import ReturningDelete
from uuid6 import uuid7

from src.core.security import hash_password
from src.db.models import CourierSchedule, Role, Transport, TransportType, User
from src.schemas.user import (
    UserCourierCreate,
    UserCourierRead,
    UserCourierUpdate,
    UserManagerCreate,
    UserManagerRead,
    UserManagerUpdate,
)
from src.utils.http_error import ConflictError, NotFoundError

# где физически храним png
SAVE_DIR = Path("/app/static/icons")


# ─────────────────────────── Base ───────────────────────────
class UserBaseRepository:
    # ---------- CRUD ----------
    async def delete(self, session: AsyncSession, user_id: UUID) -> bool:
        """
        Удаляет пользователя и возвращает True, если запись действительно была,
        иначе False.
        """
        stmt: ReturningDelete[Tuple[UUID]] = sa_delete(User).where(User.id == user_id).returning(User.id)
        res: Result[Tuple[UUID]] = await session.execute(stmt)
        return res.scalar_one_or_none() is not None

    # ---------- helpers ----------
    async def _get_role(self, session: AsyncSession, name: str) -> Role:
        role: Role | None = await session.scalar(select(Role).where(Role.name == name))
        if role is None:
            raise NotFoundError(f"Роль '{name}' не найдена")
        return role

    async def _get_transport_type(self, session: AsyncSession, name: str) -> TransportType:
        tt: TransportType | None = await session.scalar(select(TransportType).where(TransportType.name == name))
        if tt is None:
            raise NotFoundError(f"Транспорт тип '{name}' не найдена")
        return tt

    async def _save_icon(self, user_id: UUID, icon: UploadFile) -> str:
        """Сохраняем файл /app/static/icons/<id>.png и возвращаем URL."""
        SAVE_DIR.mkdir(parents=True, exist_ok=True)
        file_path: Path = SAVE_DIR / f"{user_id}.png"
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(await icon.read())
        return f"/static/icons/{user_id}.png"


# ───────────────────────── Manager ─────────────────────────
class UserManagerRepository(UserBaseRepository):
    async def create(self, session: AsyncSession, data: UserManagerCreate, icon: UploadFile | None) -> UserManagerRead:
        role: Role = await self._get_role(session, "manager")
        user_id: UUID = uuid7()
        avatar: str | None = await self._save_icon(user_id, icon) if icon else None

        user = User(
            id=user_id,
            first_name=data.first_name,
            last_name=data.last_name,
            phone=data.phone,
            email=data.email,
            password_hash=hash_password(data.password),
            role_id=role.id,
            avatar_path=avatar,
        )
        session.add(user)
        try:
            await session.flush()
        except Exception as e:
            if "user_email_key" in str(e):
                raise ConflictError("Пользователь с таким email уже существует") from e
            raise

        return UserManagerRead(
            id=user.id,
            first_name=user.first_name,
            last_name=user.last_name,
            phone=user.phone,
            email=user.email,
            avatar_path=user.avatar_path,
        )

    async def update(
        self, session: AsyncSession, user_id: UUID, data: UserManagerUpdate, icon: UploadFile | None
    ) -> UserManagerRead | None:
        values: dict[str, Any] = data.model_dump(exclude_unset=True, exclude_none=True)
        if "password" in values:
            values["password_hash"] = hash_password(values.pop("password"))
        if icon:
            values["avatar_path"] = await self._save_icon(user_id, icon)

        if values:
            await session.execute(sa_update(User).where(User.id == user_id).values(**values))

        user: User | None = await session.get(User, user_id)
        if user is None:
            return None

        return UserManagerRead(
            id=user.id,
            first_name=user.first_name,
            last_name=user.last_name,
            phone=user.phone,
            email=user.email,
            avatar_path=user.avatar_path,
        )

    async def list(self, session: AsyncSession) -> list[UserManagerRead]:
        stmt: Select[Tuple[User]] = select(User).join(Role, User.role_id == Role.id).where(Role.name == "manager")
        rows: ScalarResult[User] = await session.scalars(stmt)
        return [
            UserManagerRead(
                id=user.id,
                first_name=user.first_name,
                last_name=user.last_name,
                phone=user.phone,
                email=user.email,
                avatar_path=user.avatar_path,
            )
            for user in rows
        ]

    async def get(self, session: AsyncSession, user_id: UUID) -> UserManagerRead | None:
        user: User | None = await session.get(User, user_id)
        if user is None:
            return None
        return UserManagerRead(
            id=user.id,
            first_name=user.first_name,
            last_name=user.last_name,
            phone=user.phone,
            email=user.email,
            avatar_path=user.avatar_path,
        )


# ───────────────────────── Courier ─────────────────────────
class UserCourierRepository(UserBaseRepository):
    async def create(self, session: AsyncSession, data: UserCourierCreate, icon: UploadFile | None) -> UserCourierRead:
        role: Role = await self._get_role(session, "courier")
        user_id: UUID = uuid7()
        avatar: str | None = await self._save_icon(user_id, icon) if icon else None

        user = User(
            id=user_id,
            first_name=data.first_name,
            last_name=data.last_name,
            phone=data.phone,
            email=data.email,
            password_hash=hash_password(data.password),
            role_id=role.id,
            avatar_path=avatar,
        )
        session.add(user)

        try:
            await session.flush()
            session.add(
                CourierSchedule(
                    courier_id=user_id,
                    start_time=data.start_time,
                    end_time=data.end_time,
                )
            )
            tt: TransportType = await self._get_transport_type(session, data.transport_name)
            session.add(Transport(courier_id=user_id, transport_type_id=tt.id))

        except Exception as e:
            if "user_email_key" in str(e):
                raise ConflictError("Курьер с таким email уже существует") from e
            raise

        return UserCourierRead(
            id=user.id,
            first_name=user.first_name,
            last_name=user.last_name,
            phone=user.phone,
            email=user.email,
            avatar_path=user.avatar_path,
            start_time=data.start_time,
            end_time=data.end_time,
            transport_name=tt.name,  # type: ignore
        )

    async def update(  # noqa: C901
        self, session: AsyncSession, user_id: UUID, data: UserCourierUpdate, icon: UploadFile | None
    ) -> UserCourierRead | None:
        values: dict[str, Any] = data.model_dump(
            exclude_unset=True,
            exclude_none=True,
            exclude={"start_time", "end_time", "transport_name"},
        )
        if "password" in values:
            values["password_hash"] = hash_password(values.pop("password"))
        if icon:
            values["avatar_path"] = await self._save_icon(user_id, icon)

        if values:
            await session.execute(sa_update(User).where(User.id == user_id).values(**values))

        # расписание
        if data.start_time is not None or data.end_time is not None:
            sched_vals: dict[str, time] = {
                k: v
                for k, v in {
                    "start_time": data.start_time,
                    "end_time": data.end_time,
                }.items()
                if v is not None
            }
            await session.execute(
                sa_update(CourierSchedule).where(CourierSchedule.courier_id == user_id).values(**sched_vals)
            )

        # транспорт
        if data.transport_name:
            tt: TransportType = await self._get_transport_type(session, data.transport_name)
            await session.execute(
                sa_update(Transport).where(Transport.courier_id == user_id).values(transport_type_id=tt.id)
            )
            transport_name: str = tt.name
        else:
            tt_existing: TransportType | None = await session.scalar(
                select(TransportType)
                .join(Transport, Transport.transport_type_id == TransportType.id)
                .where(Transport.courier_id == user_id)
            )
            if tt_existing is None:
                raise NotFoundError(f"Тип транспорта не найден для курьера {user_id}")
            transport_name = tt_existing.name

        user: User | None = await session.get(User, user_id)
        if user is None:
            return None

        sched: CourierSchedule | None = await session.scalar(
            select(CourierSchedule).where(CourierSchedule.courier_id == user_id)
        )
        if sched is None:
            raise NotFoundError(f"Не найдено расписание курьера {user_id}")

        return UserCourierRead(
            id=user.id,
            first_name=user.first_name,
            last_name=user.last_name,
            phone=user.phone,
            email=user.email,
            avatar_path=user.avatar_path,
            start_time=sched.start_time,
            end_time=sched.end_time,
            transport_name=transport_name,  # type: ignore
        )

    async def list(self, session: AsyncSession) -> list[UserCourierRead]:
        stmt: Select[Tuple[User, CourierSchedule, str]] = (
            select(User, CourierSchedule, TransportType.name)
            .join(CourierSchedule, CourierSchedule.courier_id == User.id)
            .join(Transport, Transport.courier_id == User.id)
            .join(TransportType, Transport.transport_type_id == TransportType.id)
        )
        rows: Result[Tuple[User, CourierSchedule, str]] = await session.execute(stmt)

        result: list[UserCourierRead] = []
        for user, sched, tt_name in rows:
            result.append(
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
        return result

    async def get(self, session: AsyncSession, user_id: UUID) -> UserCourierRead | None:
        user: User | None = await session.get(User, user_id)
        if user is None:
            return None

        sched: CourierSchedule | None = await session.scalar(
            select(CourierSchedule).where(CourierSchedule.courier_id == user_id)
        )
        tt_name: str | None = await session.scalar(
            select(TransportType.name)
            .join(Transport, Transport.transport_type_id == TransportType.id)
            .where(Transport.courier_id == user_id)
        )
        return UserCourierRead(
            id=user.id,
            first_name=user.first_name,
            last_name=user.last_name,
            phone=user.phone,
            email=user.email,
            avatar_path=user.avatar_path,
            start_time=sched.start_time,  # type: ignore
            end_time=sched.end_time,  # type: ignore
            transport_name=tt_name,  # type: ignore
        )

# app/orm-server/src/services/user_service.py
from pathlib import Path
from typing import Sequence, Tuple
from uuid import UUID

import aiofiles
from sqlalchemy import Select, delete, select

import shared.grpc_stubs.user_pb2 as user_pb2
import shared.grpc_stubs.user_pb2_grpc as user_pb2_grpc
from db.core import get_session
from db.models import User

AVATAR_DIR = Path("/data/avatars")  # смонтирован из avatars-pvc


class UserService(user_pb2_grpc.UserServiceServicer):
    # ---------- helpers ----------
    @staticmethod
    def _to_proto(obj: User) -> user_pb2.User:
        return user_pb2.User(
            id=str(obj.id),
            first_name=obj.first_name,
            last_name=obj.last_name,
            phone=obj.phone,
            email=obj.email,
            avatar_url=obj.avatar_path or "",
            role_id=obj.role_id or 0,
        )

    # ---------- CRUD ----------
    async def CreateUser(self, request, context) -> user_pb2.User:
        async with get_session() as s:
            u = User(
                first_name=request.user.first_name,
                last_name=request.user.last_name,
                phone=request.user.phone,
                email=request.user.email,
                role_id=request.user.role_id,
            )
            s.add(u)
            await s.commit()
            await s.refresh(u)
            return self._to_proto(u)

    async def GetUser(self, request, context):
        async with get_session() as s:
            stmt: Select[Tuple[User]] = select(User).where(User.id == UUID(request.id))
            u: User = (await s.scalars(stmt)).one()
            return self._to_proto(u)

    async def UpdateUser(self, request, context):
        async with get_session() as s:
            u = (await s.scalars(select(User).where(User.id == UUID(request.user.id)))).one()
            for field in ("first_name", "last_name", "phone", "email", "role_id"):
                setattr(u, field, getattr(request.user, field))
            await s.commit()
            return self._to_proto(u)

    async def DeleteUser(self, request, context):
        async with get_session() as s:
            await s.execute(delete(User).where(User.id == UUID(request.id)))
            await s.commit()
        return user_pb2.google_dot_protobuf_dot_empty__pb2.Empty()

    async def ListUsers(self, request, context):
        async with get_session() as s:
            users: Sequence[User] = (await s.scalars(select(User))).all()
            return user_pb2.ListUsersResponse(users=[self._to_proto(u) for u in users])

    # ---------- avatar upload ----------
    async def UploadAvatar(self, request_iterator, context):
        first = await request_iterator.read()
        user_id = UUID(first.user_id)
        file_path: Path = AVATAR_DIR / f"{user_id}.png"

        async with aiofiles.open(file_path, "wb") as f:
            await f.write(first.content)
            async for chunk in request_iterator:
                await f.write(chunk.content)

        async with get_session() as s:
            u: User = (await s.scalars(select(User).where(User.id == user_id))).one()
            u.avatar_path = f"avatars/{user_id}.png"
            await s.commit()
            await s.refresh(u)
            return self._to_proto(u)

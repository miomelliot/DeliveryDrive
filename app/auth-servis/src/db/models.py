# src/db/models.py
from uuid import UUID

from sqlalchemy import ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from uuid6 import uuid7


class Base(DeclarativeBase):
    """Declarative base for all models."""


def uuid_pk() -> Mapped[UUID]:
    return mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid7,
        nullable=False,
    )


class Role(Base):
    __tablename__ = "role"

    id: Mapped[int] = mapped_column("role_id", Integer, primary_key=True)
    name: Mapped[str] = mapped_column(Text, unique=True, nullable=False)


class User(Base):
    __tablename__ = "user"

    id: Mapped[UUID] = uuid_pk()
    first_name: Mapped[str] = mapped_column(Text)
    last_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    phone: Mapped[str] = mapped_column(Text)
    email: Mapped[str] = mapped_column(Text, unique=True)
    avatar_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    password_hash: Mapped[str] = mapped_column(Text)

    role_id: Mapped[int] = mapped_column(
        ForeignKey(Role.id, ondelete="RESTRICT"),
    )
    role: Mapped[Role] = relationship()

# app/orm-server/src/db/models.py
from datetime import date as dt_date
from datetime import datetime
from datetime import datetime as dt_datetime
from datetime import time as dt_time
from datetime import timezone as tz
from typing import Any
from uuid import UUID

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    Text,
    Time,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from uuid6 import uuid7


class Base(DeclarativeBase):
    """Declarative base for all models."""


# единый столбец-шаблон для UUID v7
def uuid_pk() -> Mapped[UUID]:
    return mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid7,
        nullable=False,
    )


# ──────────────── Reference / Lookup ────────────────
class Role(Base):
    __tablename__ = "role"

    id: Mapped[int] = mapped_column("role_id", Integer, primary_key=True)
    name: Mapped[str] = mapped_column(Text, unique=True, nullable=False)


class OrderStatus(Base):
    __tablename__ = "order_status"

    id: Mapped[int] = mapped_column("status_id", Integer, primary_key=True)
    code: Mapped[str] = mapped_column(Text, unique=True)
    description: Mapped[str] = mapped_column(Text)


class EquipmentStatus(Base):
    __tablename__ = "equipment_status"

    id: Mapped[int] = mapped_column("equipment_status_id", Integer, primary_key=True)
    code: Mapped[str] = mapped_column(Text, unique=True)
    description: Mapped[str] = mapped_column(Text)


class InvoiceStatus(Base):
    __tablename__ = "invoice_status"

    id: Mapped[int] = mapped_column("invoice_status_id", Integer, primary_key=True)
    code: Mapped[str] = mapped_column(Text, unique=True)
    description: Mapped[str] = mapped_column(Text)


class EventType(Base):
    __tablename__ = "event_type"

    id: Mapped[int] = mapped_column("event_type_id", Integer, primary_key=True)
    code: Mapped[str] = mapped_column(Text, unique=True)
    description: Mapped[str] = mapped_column(Text)


class HeaterType(Base):
    __tablename__ = "heater_type"

    id: Mapped[int] = mapped_column("heater_type_id", Integer, primary_key=True)
    model: Mapped[str] = mapped_column(Text)
    price: Mapped[float] = mapped_column(Float)
    weight: Mapped[float] = mapped_column(Float)


class TransportType(Base):
    __tablename__ = "transport_type"

    id: Mapped[int] = mapped_column("transport_type_id", Integer, primary_key=True)
    name: Mapped[str] = mapped_column(Text)
    avg_speed: Mapped[float] = mapped_column(Float)
    capacity: Mapped[float] = mapped_column(Float)


# ──────────────── Users & Locations ────────────────
class User(Base):
    __tablename__ = "user"

    id: Mapped[UUID] = uuid_pk()
    first_name: Mapped[str] = mapped_column(Text)
    last_name: Mapped[str] = mapped_column(Text)
    phone: Mapped[str] = mapped_column(Text)
    email: Mapped[str] = mapped_column(Text, unique=True)
    avatar_path: Mapped[str] = mapped_column(Text)
    password_hash: Mapped[str] = mapped_column(Text)
    role_id: Mapped[int] = mapped_column(ForeignKey(Role.id, ondelete="RESTRICT"))
    role: Mapped[Role] = relationship()

    # удобная связь для колокольчика
    notifications: Mapped[list["Notification"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class Address(Base):
    __tablename__ = "address"

    id: Mapped[UUID] = uuid_pk()
    street: Mapped[str] = mapped_column(Text)
    building: Mapped[str] = mapped_column(Text)
    city: Mapped[str] = mapped_column(Text)
    lat: Mapped[float] = mapped_column(Float)
    lon: Mapped[float] = mapped_column(Float)


class Warehouse(Base):
    __tablename__ = "warehouse"

    id: Mapped[UUID] = uuid_pk()
    address_id: Mapped[UUID] = mapped_column(ForeignKey(Address.id, ondelete="RESTRICT"))
    address: Mapped[Address] = relationship()


# ────────────────── Clients & Orders ──────────────────
class Client(Base):
    __tablename__ = "client"

    id: Mapped[UUID] = uuid_pk()
    name: Mapped[str] = mapped_column(Text)
    phone: Mapped[str] = mapped_column(Text)
    address_id: Mapped[UUID] = mapped_column(ForeignKey(Address.id))
    address: Mapped[Address] = relationship()


class Order(Base):
    __tablename__ = "order"

    id: Mapped[UUID] = uuid_pk()
    client_id: Mapped[UUID] = mapped_column(ForeignKey(Client.id))
    created_at: Mapped[dt_datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(tz.utc),
    )
    window_start: Mapped[dt_time] = mapped_column(Time)
    window_end: Mapped[dt_time] = mapped_column(Time)
    rent_start: Mapped[dt_date] = mapped_column(Date)
    rent_end: Mapped[dt_date] = mapped_column(Date)
    status_id: Mapped[int] = mapped_column(ForeignKey(OrderStatus.id))
    comment: Mapped[str] = mapped_column(Text)

    client: Mapped[Client] = relationship()
    status: Mapped[OrderStatus] = relationship()


class Contract(Base):
    __tablename__ = "contract"

    id: Mapped[UUID] = uuid_pk()
    order_id: Mapped[UUID] = mapped_column(ForeignKey(Order.id, ondelete="CASCADE"), unique=True)
    file_path: Mapped[str] = mapped_column(Text)
    order: Mapped[Order] = relationship()


# ─────────────────── Equipment ───────────────────
class Equipment(Base):
    __tablename__ = "equipment"

    id: Mapped[UUID] = uuid_pk()
    heater_type_id: Mapped[int] = mapped_column(ForeignKey(HeaterType.id))
    serial_number: Mapped[str] = mapped_column(Text, unique=True)
    equipment_status_id: Mapped[int] = mapped_column(ForeignKey(EquipmentStatus.id))
    warehouse_id: Mapped[UUID] = mapped_column(ForeignKey(Warehouse.id))
    current_address_id: Mapped[UUID] = mapped_column(ForeignKey(Address.id))

    heater_type: Mapped[HeaterType] = relationship()
    status: Mapped[EquipmentStatus] = relationship()
    warehouse: Mapped[Warehouse] = relationship()
    current_address: Mapped[Address] = relationship()


class Maintenance(Base):
    __tablename__ = "maintenance"

    id: Mapped[UUID] = uuid_pk()
    equipment_id: Mapped[UUID] = mapped_column(ForeignKey(Equipment.id))
    date: Mapped[dt_date] = mapped_column(Date)


# ───────────── Order Composition ─────────────
class OrderItem(Base):
    __tablename__ = "order_item"

    id: Mapped[UUID] = uuid_pk()
    order_id: Mapped[UUID] = mapped_column(ForeignKey(Order.id, ondelete="CASCADE"))
    heater_type_id: Mapped[int] = mapped_column(ForeignKey(HeaterType.id))
    quantity: Mapped[int] = mapped_column(Integer)


# ─────────────── Logistics ───────────────
class Route(Base):
    __tablename__ = "route"

    id: Mapped[UUID] = uuid_pk()
    courier_id: Mapped[UUID] = mapped_column(ForeignKey(User.id))
    date: Mapped[dt_date] = mapped_column(Date)
    planned_start: Mapped[dt_datetime] = mapped_column(DateTime(timezone=True))
    planned_end: Mapped[dt_datetime] = mapped_column(DateTime(timezone=True))


class RouteItem(Base):
    __tablename__ = "route_item"
    __table_args__ = (UniqueConstraint("route_id", "sequence", name="uq_route_sequence"),)

    id: Mapped[UUID] = uuid_pk()
    route_id: Mapped[UUID] = mapped_column(ForeignKey(Route.id, ondelete="CASCADE"))
    order_id: Mapped[UUID] = mapped_column(ForeignKey(Order.id))
    sequence: Mapped[int] = mapped_column(Integer)


class Tracking(Base):
    __tablename__ = "tracking"

    id: Mapped[UUID] = uuid_pk()
    route_item_id: Mapped[UUID] = mapped_column(ForeignKey(RouteItem.id))
    event_type_id: Mapped[int] = mapped_column(ForeignKey(EventType.id))
    event_time: Mapped[dt_datetime] = mapped_column(DateTime(timezone=True))


class Transport(Base):
    __tablename__ = "transport"

    id: Mapped[UUID] = uuid_pk()
    courier_id: Mapped[UUID] = mapped_column(ForeignKey(User.id))
    transport_type_id: Mapped[int] = mapped_column(ForeignKey(TransportType.id))


# ─────────────── Finance ───────────────
class Invoice(Base):
    __tablename__ = "invoice"

    id: Mapped[UUID] = uuid_pk()
    order_id: Mapped[UUID] = mapped_column(ForeignKey(Order.id))
    amount: Mapped[float] = mapped_column(Numeric(12, 2))
    invoice_status_id: Mapped[int] = mapped_column(ForeignKey(InvoiceStatus.id))
    issued_at: Mapped[dt_date] = mapped_column(Date)
    paid_at: Mapped[dt_date] = mapped_column(Date)


# ─────────── History & Audit ───────────
class OrderHistory(Base):
    __tablename__ = "order_history"
    __table_args__ = (UniqueConstraint("order_id", "timestamp"),)

    id: Mapped[UUID] = uuid_pk()
    order_id: Mapped[UUID] = mapped_column(ForeignKey(Order.id))
    timestamp: Mapped[dt_datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(tz.utc))
    previous_status_id: Mapped[int] = mapped_column(ForeignKey(OrderStatus.id))
    new_status_id: Mapped[int] = mapped_column(ForeignKey(OrderStatus.id))
    user_id: Mapped[UUID] = mapped_column(ForeignKey(User.id))


class CourierSchedule(Base):
    __tablename__ = "courier_schedule"

    id: Mapped[UUID] = uuid_pk()
    courier_id: Mapped[UUID] = mapped_column(ForeignKey(User.id))
    start_time: Mapped[dt_time] = mapped_column(Time)
    end_time: Mapped[dt_time] = mapped_column(Time)


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[UUID] = uuid_pk()
    user_id: Mapped[UUID] = mapped_column(ForeignKey(User.id))
    event: Mapped[str] = mapped_column(Text)
    target_table: Mapped[str] = mapped_column(Text)
    timestamp: Mapped[dt_datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(tz.utc))
    old_values: Mapped[dict[str, Any]] = mapped_column(JSONB)
    new_values: Mapped[dict[str, Any]] = mapped_column(JSONB)


# ─────────────── Notifications ───────────────
class Notification(Base):
    __tablename__ = "notification"

    id: Mapped[UUID] = uuid_pk()
    user_id: Mapped[UUID] = mapped_column(ForeignKey(User.id, ondelete="CASCADE"))
    text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[dt_datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(tz.utc))
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)

    user: Mapped[User] = relationship(back_populates="notifications")

    __table_args__ = (UniqueConstraint("user_id", "id", name="uq_user_notification"),)

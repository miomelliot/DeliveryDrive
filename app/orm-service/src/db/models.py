# src/db/models.py
from datetime import date as dt_date
from datetime import datetime, time
from datetime import time as dt_time
from datetime import timezone as tz
from decimal import Decimal
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


class Base(DeclarativeBase): ...


# единый столбец-шаблон для UUID v7
def uuid_pk() -> Mapped[UUID]:
    return mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid7,
        nullable=False,
    )


# ---------------- Reference ----------------
class BaseLookup(Base):
    __abstract__ = True

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    code: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text)


class OrderStatus(BaseLookup):
    __tablename__ = "order_status"
    id: Mapped[int] = mapped_column("status_id", Integer, primary_key=True, autoincrement=True)

    orders: Mapped[list["Order"]] = relationship(
        back_populates="status",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class EquipmentStatus(BaseLookup):
    __tablename__ = "equipment_status"
    id: Mapped[int] = mapped_column("equipment_status_id", Integer, primary_key=True, autoincrement=True)

    equipment: Mapped[list["Equipment"]] = relationship(
        back_populates="status",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class InvoiceStatus(BaseLookup):
    __tablename__ = "invoice_status"
    id: Mapped[int] = mapped_column("invoice_status_id", Integer, primary_key=True, autoincrement=True)

    invoices: Mapped[list["Invoice"]] = relationship(
        back_populates="status",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class EventType(BaseLookup):
    __tablename__ = "event_type"
    id: Mapped[int] = mapped_column("event_type_id", Integer, primary_key=True, autoincrement=True)

    trackings: Mapped[list["Tracking"]] = relationship(
        back_populates="event_type",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class Role(Base):
    __tablename__ = "role"
    id: Mapped[int] = mapped_column(
        "role_id",
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    name: Mapped[str] = mapped_column(Text, unique=True, nullable=False)


class HeaterType(Base):
    __tablename__ = "heater_type"
    id: Mapped[int] = mapped_column(
        "heater_type_id",
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    model: Mapped[str] = mapped_column(Text)
    price: Mapped[float] = mapped_column(Float)
    weight: Mapped[float] = mapped_column(Float)

    equipment: Mapped[list["Equipment"]] = relationship(
        back_populates="heater_type",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class TransportType(Base):
    __tablename__ = "transport_type"
    id: Mapped[int] = mapped_column("transport_type_id", Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(Text)
    avg_speed: Mapped[float] = mapped_column(Float)
    capacity: Mapped[float] = mapped_column(Float)


# ---------------- Users ----------------
class User(Base):
    __tablename__ = "user"

    id: Mapped[UUID] = uuid_pk()
    first_name: Mapped[str] = mapped_column(Text)
    last_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    phone: Mapped[str] = mapped_column(Text)
    email: Mapped[str] = mapped_column(Text, unique=True)
    avatar_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    password_hash: Mapped[str] = mapped_column(Text)
    role_id: Mapped[int] = mapped_column(ForeignKey(Role.id, ondelete="RESTRICT"))

    role: Mapped[Role] = relationship()

    notifications: Mapped[list["Notification"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    transports: Mapped[list["Transport"]] = relationship(
        back_populates="courier",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    schedules: Mapped[list["CourierSchedule"]] = relationship(
        back_populates="courier",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    routes: Mapped[list["Route"]] = relationship(
        back_populates="courier",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


# --------------- Address / Warehouse ---------------
class Address(Base):
    __tablename__ = "address"
    id: Mapped[UUID] = uuid_pk()
    street: Mapped[str | None] = mapped_column(Text, nullable=True)
    building: Mapped[str] = mapped_column(Text)
    city: Mapped[str] = mapped_column(Text)
    lat: Mapped[float] = mapped_column(Float)
    lon: Mapped[float] = mapped_column(Float)


class Warehouse(Base):
    __tablename__ = "warehouse"
    id: Mapped[UUID] = uuid_pk()
    address_id: Mapped[UUID] = mapped_column(ForeignKey(Address.id, ondelete="CASCADE"))

    address: Mapped[Address] = relationship()


# --------------- Client / Order ---------------
class Client(Base):
    __tablename__ = "client"
    id: Mapped[UUID] = uuid_pk()
    name: Mapped[str | None] = mapped_column(Text, nullable=True)
    phone: Mapped[str] = mapped_column(Text)
    address_id: Mapped[UUID] = mapped_column(ForeignKey(Address.id, ondelete="SET NULL"))

    address: Mapped[Address] = relationship()


class Order(Base):
    __tablename__ = "order"
    id: Mapped[UUID] = uuid_pk()
    client_id: Mapped[UUID] = mapped_column(ForeignKey(Client.id, ondelete="CASCADE"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(tz.utc))
    window_start: Mapped[dt_time] = mapped_column(Time, default=time(9, 0))
    window_end: Mapped[dt_time] = mapped_column(Time, default=time(21, 0))
    rent_start: Mapped[dt_date] = mapped_column(Date)
    rent_end: Mapped[dt_date] = mapped_column(Date)
    status_id: Mapped[int] = mapped_column(ForeignKey(OrderStatus.id))
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    client: Mapped[Client] = relationship()
    status: Mapped[OrderStatus] = relationship(back_populates="orders")

    items: Mapped[list["OrderItem"]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    contract: Mapped["Contract"] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
        passive_deletes=True,
        uselist=False,
    )
    invoices: Mapped[list["Invoice"]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    route_items: Mapped[list["RouteItem"]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class Contract(Base):
    __tablename__ = "contract"
    id: Mapped[UUID] = uuid_pk()
    order_id: Mapped[UUID] = mapped_column(ForeignKey(Order.id, ondelete="CASCADE"), unique=True)
    file_path: Mapped[str] = mapped_column(Text)

    order: Mapped[Order] = relationship(back_populates="contract")


# --------------- Equipment ---------------
class Equipment(Base):
    __tablename__ = "equipment"
    id: Mapped[UUID] = uuid_pk()
    heater_type_id: Mapped[int] = mapped_column(ForeignKey(HeaterType.id))
    serial_number: Mapped[str] = mapped_column(Text, unique=True)
    equipment_status_id: Mapped[int] = mapped_column(ForeignKey(EquipmentStatus.id))
    warehouse_id: Mapped[UUID] = mapped_column(ForeignKey(Warehouse.id, ondelete="SET NULL"))
    current_address_id: Mapped[UUID] = mapped_column(ForeignKey(Address.id, ondelete="SET NULL"))

    heater_type: Mapped[HeaterType] = relationship(back_populates="equipment")
    status: Mapped[EquipmentStatus] = relationship(back_populates="equipment")
    warehouse: Mapped[Warehouse] = relationship()
    current_address: Mapped[Address] = relationship()

    maintenance: Mapped[list["Maintenance"]] = relationship(
        back_populates="equipment",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class Maintenance(Base):
    __tablename__ = "maintenance"
    id: Mapped[UUID] = uuid_pk()
    equipment_id: Mapped[UUID] = mapped_column(ForeignKey(Equipment.id, ondelete="CASCADE"))
    date: Mapped[dt_date | None] = mapped_column(Date, nullable=True)

    equipment: Mapped[Equipment] = relationship(back_populates="maintenance")


# ------------- OrderItem -------------
class OrderItem(Base):
    __tablename__ = "order_item"
    id: Mapped[UUID] = uuid_pk()
    order_id: Mapped[UUID] = mapped_column(ForeignKey(Order.id, ondelete="CASCADE"))
    heater_type_id: Mapped[int] = mapped_column(ForeignKey(HeaterType.id))
    quantity: Mapped[int] = mapped_column(Integer)

    order: Mapped[Order] = relationship(back_populates="items")
    heater_type: Mapped[HeaterType] = relationship()


# --------------- Logistics ---------------
class Route(Base):
    __tablename__ = "route"
    id: Mapped[UUID] = uuid_pk()
    courier_id: Mapped[UUID] = mapped_column(ForeignKey(User.id, ondelete="CASCADE"))
    date: Mapped[dt_date] = mapped_column(Date)
    planned_start: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    planned_end: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    courier: Mapped[User] = relationship(back_populates="routes")
    items: Mapped[list["RouteItem"]] = relationship(
        back_populates="route",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class RouteItem(Base):
    __tablename__ = "route_item"
    __table_args__ = (UniqueConstraint("route_id", "sequence", name="uq_route_sequence"),)
    id: Mapped[UUID] = uuid_pk()
    route_id: Mapped[UUID] = mapped_column(ForeignKey(Route.id, ondelete="CASCADE"))
    order_id: Mapped[UUID] = mapped_column(ForeignKey(Order.id, ondelete="SET NULL"))
    sequence: Mapped[int] = mapped_column(Integer)

    route: Mapped[Route] = relationship(back_populates="items")
    order: Mapped[Order] = relationship(back_populates="route_items")


class Tracking(Base):
    __tablename__ = "tracking"
    id: Mapped[UUID] = uuid_pk()
    route_item_id: Mapped[UUID] = mapped_column(ForeignKey(RouteItem.id, ondelete="CASCADE"))
    event_type_id: Mapped[int] = mapped_column(ForeignKey(EventType.id))
    event_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    event_type: Mapped[EventType] = relationship(back_populates="trackings")


class Transport(Base):
    __tablename__ = "transport"
    id: Mapped[UUID] = uuid_pk()
    courier_id: Mapped[UUID] = mapped_column(ForeignKey(User.id, ondelete="CASCADE"))
    transport_type_id: Mapped[int] = mapped_column(ForeignKey(TransportType.id))

    courier: Mapped[User] = relationship(back_populates="transports")
    transport_type: Mapped[TransportType] = relationship()


# --------------- Finance ---------------
class Invoice(Base):
    __tablename__ = "invoice"
    id: Mapped[UUID] = uuid_pk()
    order_id: Mapped[UUID] = mapped_column(ForeignKey(Order.id, ondelete="CASCADE"))
    amount: Mapped[float] = mapped_column(Numeric(12, 2), default=Decimal("0.00"))
    invoice_status_id: Mapped[int] = mapped_column(ForeignKey(InvoiceStatus.id))
    issued_at: Mapped[dt_date | None] = mapped_column(Date, nullable=True)
    paid_at: Mapped[dt_date | None] = mapped_column(Date, nullable=True)

    order: Mapped[Order] = relationship(back_populates="invoices")
    status: Mapped[InvoiceStatus] = relationship(back_populates="invoices")


# ----------- History / Audit -----------
class OrderHistory(Base):
    __tablename__ = "order_history"
    __table_args__ = (UniqueConstraint("order_id", "timestamp"),)
    id: Mapped[UUID] = uuid_pk()
    order_id: Mapped[UUID] = mapped_column(ForeignKey(Order.id, ondelete="CASCADE"))
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(tz.utc))
    previous_status_id: Mapped[int | None] = mapped_column(ForeignKey(OrderStatus.id), nullable=True)
    new_status_id: Mapped[int] = mapped_column(ForeignKey(OrderStatus.id))
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey(User.id, ondelete="SET NULL"),
    )


class CourierSchedule(Base):
    __tablename__ = "courier_schedule"
    id: Mapped[UUID] = uuid_pk()
    courier_id: Mapped[UUID] = mapped_column(ForeignKey(User.id, ondelete="CASCADE"))
    start_time: Mapped[dt_time] = mapped_column(Time, default=time(9, 0))
    end_time: Mapped[dt_time] = mapped_column(Time, default=time(18, 0))

    courier: Mapped[User] = relationship(back_populates="schedules")


class AuditLog(Base):
    __tablename__ = "audit_log"
    id: Mapped[UUID] = uuid_pk()
    user_id: Mapped[UUID] = mapped_column(ForeignKey(User.id, ondelete="SET NULL"))
    event: Mapped[str] = mapped_column(Text)
    target_table: Mapped[str] = mapped_column(Text)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(tz.utc))
    old_values: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    new_values: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)


# --------------- Notifications ---------------
class Notification(Base):
    __tablename__ = "notification"
    id: Mapped[UUID] = uuid_pk()
    user_id: Mapped[UUID] = mapped_column(ForeignKey(User.id, ondelete="CASCADE"))
    text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(tz.utc))
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)

    user: Mapped[User] = relationship(back_populates="notifications")
    __table_args__ = (UniqueConstraint("user_id", "id", name="uq_user_notification"),)

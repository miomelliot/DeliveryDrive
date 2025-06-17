# src/repositories/tables/order.py
import math
import secrets
from datetime import date, datetime, time
from pathlib import Path
from typing import Tuple
from uuid import UUID

import aiofiles
import pandas as pd
from fastapi import UploadFile
from loguru import logger
from sqlalchemy import RowMapping, Select, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from src.db.models import (
    Address,
    Client,
    Contract,
    Equipment,
    HeaterType,
    Invoice,
    InvoiceStatus,
    Order,
    OrderHistory,
    OrderItem,
    OrderStatus,
    Route,
    RouteItem,
    User,
    Warehouse,
)
from src.repositories.tables.base import CRUDRepository
from src.repositories.tables.client import ClientRepository
from src.repositories.tables.equipment import EquipmentRepository
from src.repositories.tables.heater_type import HeaterTypeRepository
from src.repositories.tables.invoice import InvoiceRepository
from src.repositories.tables.order_history import OrderHistoryRepository
from src.repositories.tables.order_item import OrderItemRepository
from src.repositories.tables.order_status import OrderStatusRepository
from src.schemas.order import EquipmentList, OrderCreate, OrderCreateAPI, OrderUpdate
from src.schemas.order_detail_read import OrderDetailRead, OrderDetailUpdate, OrderHistoryChart, OrderItemChart
from src.schemas.order_history import OrderHistoryCreate
from src.schemas.order_item import OrderItemCreate
from src.utils.http_error import BadRequestError, UnprocessableEntityError
from src.utils.sqlalchemy_expr import full_name_expr, location_expr

# IMPORT_DIR = Path("/app/static/imports")
ALLOWED_EXT: set[str] = {".xlsx", ".csv", ".json"}
ROOT_DIR: Path = Path(__file__).resolve().parent.parent.parent.parent
STATIC_DIR: Path = ROOT_DIR / "static"
IMPORT_DIR: Path = STATIC_DIR / "imports"


class OrderRepository(CRUDRepository[Order, OrderCreate, OrderUpdate]):
    def __init__(self) -> None:
        super().__init__(Order)

    async def create_raw(self, session: AsyncSession, raw_data: OrderCreateAPI) -> Order:
        client: Client = await ClientRepository().create_raw(session, raw_data)
        status_id: int = await OrderStatusRepository().get_code_id(session, "new")

        obj_in = OrderCreate(
            client_id=client.id,
            window_start=raw_data.window_start,
            window_end=raw_data.window_end,
            rent_start=raw_data.rent_start,
            rent_end=raw_data.rent_end,
            status_id=status_id,
            comment=raw_data.comment,
        )
        order: Order = await super().create(session, obj_in)

        for eq in raw_data.equipment:
            heater_type: HeaterType = await HeaterTypeRepository().get_all(session, eq.model)

            await EquipmentRepository().update_status_bulk(
                session=session,
                heater_type_id=heater_type.id,
                old_status_code="available",
                new_status_code="rented",
                limit=eq.quantity,
                model=heater_type.model,
                new_address_id=client.address_id,
            )

            await OrderItemRepository().create(
                session,
                OrderItemCreate(
                    order_id=order.id,
                    heater_type_id=heater_type.id,
                    quantity=eq.quantity,
                ),
            )

        await InvoiceRepository().create_from_order(session, order.id)

        await OrderHistoryRepository().create(
            session,
            OrderHistoryCreate(
                order_id=order.id,
                previous_status_id=None,
                new_status_id=status_id,
                user_id=session.info.get("user_id"),
            ),
        )
        return order

    async def update_status(
        self,
        session: AsyncSession,
        order_id: UUID,
        new_status_code: str | None,
    ) -> int:
        order: Order = await self.get(session, order_id)
        if new_status_code is None:
            return order.status_id

        new_status_id: int = await OrderStatusRepository().get_code_id(session, new_status_code)

        if order.status_id == new_status_id:
            return order.status_id

        prev_status_id: int = order.status_id
        order.status_id = new_status_id
        await session.flush()
        await session.refresh(order)

        if new_status_code in ("completed", "cancelled"):
            equipment_list: list[Equipment] = await OrderItemRepository().get_item_from_order_id(session, order.id)
            for equipment in equipment_list:
                await EquipmentRepository().update_status(session, equipment.id, "available")

        await OrderHistoryRepository().create(
            session,
            OrderHistoryCreate(
                order_id=order.id,
                previous_status_id=prev_status_id,
                new_status_id=new_status_id,
                user_id=session.info.get("user_id"),
            ),
        )
        return order.status_id

    async def import_file(self, session: AsyncSession, upload: UploadFile) -> list[Order]:
        ext, filename = self._validate_upload(upload)
        file_path: Path = await self._save_upload(upload, filename)

        try:
            df: pd.DataFrame = self._load_dataframe(file_path, ext)
            self._ensure_columns(df, {"phone", "address", "rent_period", "heater_model", "qty"})

            created: list[Order] = []

            for i, (_, row) in enumerate(df.iterrows(), start=1):
                try:
                    api: OrderCreateAPI = self._row_to_api(row)
                    created.append(await self.create_raw(session, api))
                except Exception as exc:
                    logger.warning("[Импорт заказов] строка {} — {}", i, exc)

            return created

        finally:
            try:
                file_path.unlink(missing_ok=True)
                logger.debug("[Импорт заказов] временный файл удалён: {}", file_path)
            except Exception as exc:
                logger.warning("[Импорт заказов] не удалось удалить {} — {}", file_path, exc)

    async def update_detail(
        self,
        session: AsyncSession,
        order_id: UUID,
        data: OrderDetailUpdate,
    ) -> Order:
        order: Order = await self.get(session, order_id)

        await ClientRepository().update_raw(session, order.client_id, data)
        await InvoiceRepository().update_raw(session, order.id, data)
        status_id: int = await self.update_status(session, order.id, data.status)
        if data.window:
            try:
                ws, we = map(str.strip, data.window.split("-"))
                order.window_start = time.fromisoformat(ws)
                order.window_end = time.fromisoformat(we)
            except Exception as e:
                raise UnprocessableEntityError(f"Недопустимый формат времени: {data.window}") from e

        obj_in = OrderUpdate(
            rent_start=order.rent_start,
            rent_end=order.rent_end,
            comment=order.comment,
            status_id=status_id,
            window_start=order.window_start,
            window_end=order.window_end,
        )

        return await super().update_by_id(session, order_id, obj_in)

    @staticmethod
    def _clean_str(val: object) -> str | None:
        """Возвращает None для NaN/None/пустых строк, иначе str(val)."""
        if val is None:
            return None
        if isinstance(val, float) and pd.isna(val):  # ловим NaN
            return None
        val_str: str = str(val).strip()
        return val_str or None

    @staticmethod
    def _validate_upload(upload: UploadFile) -> tuple[str, str]:
        if not upload.filename:
            raise BadRequestError("Файл без имени")
        ext: str = Path(upload.filename).suffix.lower()
        if ext not in ALLOWED_EXT:
            raise BadRequestError("Разрешены .xlsx, .csv, .json")
        return ext, upload.filename

    @staticmethod
    async def _save_upload(upload: UploadFile, filename: str) -> Path:
        IMPORT_DIR.mkdir(parents=True, exist_ok=True)
        dest: Path = IMPORT_DIR / f"{secrets.token_hex(8)}{Path(filename).suffix.lower()}"
        async with aiofiles.open(dest, "wb") as f:
            while chunk := await upload.read(8192):
                await f.write(chunk)
        return dest

    @staticmethod
    def _load_dataframe(path: Path, ext: str) -> pd.DataFrame:
        if ext == ".xlsx":
            return pd.read_excel(path)
        if ext == ".csv":
            return pd.read_csv(path)
        return pd.read_json(path)  # .json

    @staticmethod
    def _ensure_columns(df: pd.DataFrame, required: set[str]) -> None:
        missing: set[str] = required - set(df.columns)
        if missing:
            raise BadRequestError(f"Отсутствуют колонки: {', '.join(sorted(missing))}")

    @staticmethod
    def _parse_dates(period: str) -> tuple[date, date]:
        # формат "YYYY-MM-DD-YYYY-MM-DD"
        if len(period) != 21 or period.count("-") != 5:
            raise BadRequestError(f"rent_period неверный формат: {period}")
        start_str, end_str = period[:10], period[11:]
        return date.fromisoformat(start_str), date.fromisoformat(end_str)

    @staticmethod
    def _parse_window(value: object) -> tuple[time, time]:
        """Возвращает (start, end) либо дефолты 09-18."""
        if value is None or (isinstance(value, float) and math.isnan(value)) or value == "":
            return time(9), time(18)

        if isinstance(value, time):  # ячейка Excel = время
            return value, time(18)

        try:
            ws, we = str(value).strip().split("-")
            return time.fromisoformat(ws), time.fromisoformat(we)
        except ValueError as exc:
            raise BadRequestError(f"delivery_window неверный формат: {value}") from exc

    def _row_to_api(self, row: pd.Series) -> OrderCreateAPI:
        phone: str = "".join(filter(str.isdigit, str(row["phone"])))
        rent_start, rent_end = self._parse_dates(str(row["rent_period"]))
        window_start, window_end = self._parse_window(row.get("delivery_window"))

        return OrderCreateAPI(
            phone=phone,
            name=self._clean_str(row.get("name")),
            location=str(row["address"]).strip(),
            window_start=window_start,
            window_end=window_end,
            rent_start=rent_start,
            rent_end=rent_end,
            comment=self._clean_str(row.get("comment")),
            equipment=[
                EquipmentList(
                    model=str(row["heater_model"]).strip(),
                    quantity=int(row["qty"]),
                )
            ],
        )

    async def get_detail(self, session: AsyncSession, order_id: UUID) -> OrderDetailRead:
        stmt = (
            select(
                Order.id,
                Order.created_at,
                Order.rent_start,
                Order.rent_end,
                Order.window_start,
                Order.window_end,
                Client.phone,
                Client.name.label("client_name"),
                location_expr().label("location"),
                OrderStatus.description.label("status"),
                InvoiceStatus.description.label("invoice_status"),
                Invoice.issued_at,
                Invoice.paid_at,
                Contract.file_path.label("contract_file_path"),
                Order.comment,
                full_name_expr().label("courier_name"),
            )
            .join(Client, Client.id == Order.client_id)
            .join(Address, Address.id == Client.address_id)
            .join(OrderStatus, OrderStatus.id == Order.status_id)
            .outerjoin(Invoice, Invoice.order_id == Order.id)
            .outerjoin(InvoiceStatus, InvoiceStatus.id == Invoice.invoice_status_id)
            .outerjoin(Contract, Contract.order_id == Order.id)
            .outerjoin(RouteItem, RouteItem.order_id == Order.id)
            .outerjoin(Route, Route.id == RouteItem.route_id)
            .outerjoin(User, User.id == Route.courier_id)
            .where(Order.id == order_id)
        )
        row: RowMapping = (await session.execute(stmt)).mappings().one()

        item_stmt: Select[Tuple[str, float, int]] = (
            select(
                HeaterType.model,
                HeaterType.weight,
                OrderItem.quantity,
            )
            .join(HeaterType, HeaterType.id == OrderItem.heater_type_id)
            .where(OrderItem.order_id == order_id)
        )
        items: list[OrderItemChart] = [
            OrderItemChart.model_validate(dict(r._mapping)) for r in (await session.execute(item_stmt)).all()
        ]

        status_new: type[OrderStatus] = aliased(OrderStatus)
        status_prev: type[OrderStatus] = aliased(OrderStatus)

        hist_stmt: Select[Tuple[datetime, str, str]] = (
            select(
                OrderHistory.timestamp,
                status_new.description.label("new_status"),
                status_prev.description.label("previous_status"),
            )
            .join(status_new, status_new.id == OrderHistory.new_status_id)
            .outerjoin(status_prev, status_prev.id == OrderHistory.previous_status_id)
            .where(OrderHistory.order_id == order_id)
            .order_by(OrderHistory.timestamp.desc())
        )
        history: list[OrderHistoryChart] = [
            OrderHistoryChart.model_validate(dict(r._mapping)) for r in (await session.execute(hist_stmt)).all()
        ]

        return OrderDetailRead(
            id=row["id"],
            created_at=row["created_at"],
            rent_start=row["rent_start"],
            rent_end=row["rent_end"],
            window=f"{row['window_start'].strftime('%H:%M')}–{row['window_end'].strftime('%H:%M')}",
            phone=row["phone"],
            client_name=row["client_name"],
            courier_name=row["courier_name"],
            location=row["location"],
            status=row["status"],
            invoice_status=row["invoice_status"],
            invoice_issued_at=row["issued_at"],
            invoice_paid_at=row["paid_at"],
            contract_file_path=row["contract_file_path"],
            comment=row["comment"],
            items=items,
            history=history,
        )

    async def delete(self, session: AsyncSession, id: UUID | int) -> None:
        equipment_list: list[Equipment] = await OrderItemRepository().get_item_from_order_id(session, id)
        for equipment in equipment_list:
            warehouse_address_id: UUID | None = await session.scalar(
                select(Warehouse.address_id).where(Warehouse.id == equipment.warehouse_id)
            )
            await EquipmentRepository().update_status(
                session,
                equipment.id,
                "available",
                address_id=warehouse_address_id,
            )

        return await super().delete(session, id)

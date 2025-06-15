# src/repositories/tables/order.py
import secrets
from datetime import date, time
from pathlib import Path
from uuid import UUID

import aiofiles
import pandas as pd
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Client, HeaterType, Order
from src.repositories.tables.base import CRUDRepository
from src.repositories.tables.client import ClientRepository
from src.repositories.tables.equipment import EquipmentRepository
from src.repositories.tables.heater_type import HeaterTypeRepository
from src.repositories.tables.invoice import InvoiceRepository
from src.repositories.tables.order_history import OrderHistoryRepository
from src.repositories.tables.order_item import OrderItemRepository
from src.repositories.tables.order_status import OrderStatusRepository
from src.schemas.order import EquipmentList, OrderCreate, OrderCreateAPI, OrderUpdate
from src.schemas.order_history import OrderHistoryCreate
from src.schemas.order_item import OrderItemCreate
from src.utils.http_error import BadRequestError

IMPORT_DIR = Path("/app/static/imports")
ALLOWED_EXT: set[str] = {".xlsx", ".csv", ".json"}


class OrderRepository(CRUDRepository[Order, OrderCreate, OrderUpdate]):
    def __init__(self) -> None:
        super().__init__(Order)

    async def create_raw(self, session: AsyncSession, raw_data: OrderCreateAPI) -> Order:
        client: Client = await ClientRepository().create_raw(session, raw_data)
        status_id: int = await OrderStatusRepository().get_id(session, "new")

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
        new_status_code: str,
    ) -> Order:
        order: Order = await self.get(session, order_id)
        new_status_id: int = await OrderStatusRepository().get_id(session, new_status_code)

        if order.status_id == new_status_id:
            return order

        prev_status_id: int = order.status_id
        order.status_id = new_status_id
        await session.flush()
        await session.refresh(order)

        await OrderHistoryRepository().create(
            session,
            OrderHistoryCreate(
                order_id=order.id,
                previous_status_id=prev_status_id,
                new_status_id=new_status_id,
                user_id=session.info.get("user_id"),
            ),
        )
        return order

    async def import_file(self, session: AsyncSession, upload: UploadFile) -> list[Order]:
        ext, filename = self._validate_upload(upload)
        file_path: Path = await self._save_upload(upload, filename)
        df: pd.DataFrame = self._load_dataframe(file_path, ext)
        self._ensure_columns(df, {"phone", "address", "rent_period", "heater_model", "qty"})

        orders_api: list[OrderCreateAPI] = [self._row_to_api(row) for _, row in df.iterrows()]
        created: list[Order] = []

        async with session.begin():
            for order_api in orders_api:
                created.append(await self.create_raw(session, order_api))
        return created

    # ─────────────────────────── helpers ───────────────────────────
    @staticmethod
    def _validate_upload(upload: UploadFile) -> tuple[str, str]:
        if not upload.filename:
            raise BadRequestError("Файл без имени")
        ext: str = Path(upload.filename).suffix.lower()
        if ext not in ALLOWED_EXT:
            raise BadRequestError("Разрешены .xlsx, .csv, .json")
        return ext, upload.filename  # type: ignore[return-value]

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
    def _parse_window(window: str | None) -> tuple[time | None, time | None]:
        if not window:
            return None, None
        try:
            start_s, end_s = window.split("-")
            return time.fromisoformat(start_s), time.fromisoformat(end_s)
        except ValueError as exc:
            raise BadRequestError(f"delivery_window неверный формат: {window}") from exc

    def _row_to_api(self, row: pd.Series) -> OrderCreateAPI:
        phone = "".join(filter(str.isdigit, str(row["phone"])))
        rent_start, rent_end = self._parse_dates(str(row["rent_period"]))

        window = str(row.get("delivery_window") or "")
        if window:
            try:
                ws_str, we_str = window.split("-")
                window_start: time = time.fromisoformat(ws_str)
                window_end: time = time.fromisoformat(we_str)
            except ValueError as exc:
                raise BadRequestError(f"delivery_window неверный формат: {window}") from exc
        else:
            window_start, window_end = time(9), time(18)

        return OrderCreateAPI(
            phone=phone,
            name=row.get("name") or None,
            location=str(row["address"]).strip(),
            window_start=window_start,
            window_end=window_end,
            rent_start=rent_start,
            rent_end=rent_end,
            comment=row.get("comment") or None,
            equipment=[
                EquipmentList(
                    model=str(row["heater_model"]).strip(),
                    quantity=int(row["qty"]),
                )
            ],
        )

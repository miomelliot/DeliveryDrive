# src/repositories/tables/invoice_status.py
from src.db.models import InvoiceStatus
from src.repositories.tables.base_status import BaseStatusRepository


class InvoiceStatusRepository(BaseStatusRepository[InvoiceStatus]):
    def __init__(self) -> None:
        super().__init__(InvoiceStatus)

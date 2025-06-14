# src/repositories/tables/order_history.py


from src.db.models import Invoice
from src.repositories.tables.base import CRUDRepository
from src.schemas.invoice import InvoiceCreate, InvoiceUpdate


class InvoiceRepository(CRUDRepository[Invoice, InvoiceCreate, InvoiceUpdate]):
    def __init__(self) -> None:
        super().__init__(Invoice)

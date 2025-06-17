from src.db.models import Route
from src.repositories.tables.base import CRUDRepository
from src.schemas.route import RouteCreate, RouteUpdate


class RouteRepository(CRUDRepository[Route, RouteCreate, RouteUpdate]):
    def __init__(self) -> None:
        super().__init__(Route)

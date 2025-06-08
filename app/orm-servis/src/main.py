from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from src.api import (
    equipment,
    equipment_chart,
    invoice_chart,
    order,
    order_chart,
    order_detail_read,
    routing_chart,
    tracking_chart,
    user,
    user_chart,
)

app = FastAPI(title="orm-servis")
# static path
BASE_DIR: Path = Path(__file__).resolve().parent.parent
STATIC_DIR: Path = BASE_DIR / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# entities
app.include_router(user.router)
app.include_router(order.router)
app.include_router(order_detail_read.router)
app.include_router(equipment.router)
# chart
app.include_router(user_chart.router)
app.include_router(order_chart.router)
app.include_router(routing_chart.router)
app.include_router(tracking_chart.router)
app.include_router(equipment_chart.router)
app.include_router(invoice_chart.router)

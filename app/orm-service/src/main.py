from pathlib import Path

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from src.api import (
    contract,
    dashboard,
    equipment,
    equipment_chart,
    invoice_chart,
    logistics,
    order,
    order_chart,
    route_sheet_chart,
    routing_chart,
    tracking_chart,
    user,
    user_chart,
    widget,
)

app = FastAPI(title="orm-service")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Или ["*"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    errors = [{"field": ".".join(map(str, err["loc"][1:])), "msg": err["msg"]} for err in exc.errors()]
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"success": False, "errors": errors},
    )


# static path
BASE_DIR: Path = Path(__file__).resolve().parent.parent
STATIC_DIR: Path = BASE_DIR / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# logistics
app.include_router(logistics.router)
# entities
app.include_router(user.router)
app.include_router(order.router)
app.include_router(equipment.router)
app.include_router(contract.router)
# widget
app.include_router(widget.router)
# dashboard
app.include_router(dashboard.router)
# chart
app.include_router(user_chart.router)
app.include_router(order_chart.router)
app.include_router(routing_chart.router)
app.include_router(tracking_chart.router)
app.include_router(equipment_chart.router)
app.include_router(invoice_chart.router)
app.include_router(route_sheet_chart.router)

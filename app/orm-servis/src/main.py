from fastapi import FastAPI

from src.api import equipment_chart, order_chart, routing_chart, tracking_chart, user, user_chart

app = FastAPI(title="orm-servis")
app.include_router(user.router)
app.include_router(user_chart.router)
app.include_router(order_chart.router)
app.include_router(routing_chart.router)
app.include_router(tracking_chart.router)
app.include_router(equipment_chart.router)

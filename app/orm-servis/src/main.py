from fastapi import FastAPI

from src.api import order_chart, user_chart

app = FastAPI(title="orm-servis")
app.include_router(user_chart.router)
app.include_router(order_chart.router)

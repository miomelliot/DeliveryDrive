from fastapi import FastAPI

from src.api import user_chart

app = FastAPI(title="orm-servis")
app.include_router(user_chart.router)

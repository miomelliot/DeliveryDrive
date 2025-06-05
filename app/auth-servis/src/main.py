from fastapi import FastAPI

from src.api import auth

app = FastAPI(title="auth-servis")
app.include_router(auth.router)

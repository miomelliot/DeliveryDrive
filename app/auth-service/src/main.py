from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api import auth

app = FastAPI(title="auth-service")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Или
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем роутеры с префиксом
app.include_router(auth.router)

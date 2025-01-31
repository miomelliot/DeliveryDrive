from fastapi import FastAPI
from routes import item_route
from services.database import engine, Base

# Создаем таблицы в базе данных
Base.metadata.create_all(bind=engine)

# Инициализируем приложение
app = FastAPI()

# Подключаем маршруты
app.include_router(item_route.router)

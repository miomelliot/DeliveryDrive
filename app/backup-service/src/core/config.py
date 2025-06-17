# src/core/config.py
import os
from functools import lru_cache

from pydantic import Field, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ── базовые переменные; в контейнере переопределяются через ENV ────────────
    user: str = Field("postgres", alias="POSTGRES_USER")
    host: str = Field("localhost", alias="POSTGRES_HOST")
    port: int = Field(5432, alias="POSTGRES_PORT")
    db: str = Field("postgres", alias="POSTGRES_DB")

    #  App / Debug -
    debug: bool = Field(False, alias="DEBUG")

    # ── pydantic-config ────────────────────────────────────────────────────────
    model_config = SettingsConfigDict(
        env_file=os.getenv("ENV_FILE", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Синглтон метод"""
    return Settings()  # type: ignore

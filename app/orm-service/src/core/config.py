# src/core/config.py
import os
from functools import lru_cache

from pydantic import Field, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ── базовые переменные; в контейнере переопределяются через ENV ────────────
    user: str = Field("postgres", alias="POSTGRES_USER")
    password: str = Field("postgres", alias="POSTGRES_PASSWORD")
    host: str = Field("localhost", alias="POSTGRES_HOST")
    port: int = Field(5432, alias="POSTGRES_PORT")
    db: str = Field("postgres", alias="POSTGRES_DB")
    osrm_service_url: str = Field("http://osrm-service:8000", alias="OSRM_SERVICE_URL")

    # --- App / Debug ----------------------------------------------
    debug: bool = Field(False, alias="DEBUG")

    # --- Auth/JWT -------------------------------------------------
    jwt_secret: str = Field(default=str("super-secret-change-me"), alias="JWT_SECRET")
    jwt_alg: str = Field("HS256", alias="JWT_ALG")
    access_token_ttl: int = Field(60 * 24 * 30, alias="ACCESS_TOKEN_TTL_MIN")  # 30 дней

    # ── готовый DSN для SQLAlchemy ─────────────────────────────────────────────
    @property
    def sqlalchemy_dsn_str(self) -> str:
        return str(
            PostgresDsn.build(
                scheme="postgresql+asyncpg",
                username=self.user,
                password=self.password,
                host=self.host,
                port=self.port,
                path=self.db,
            )
        )

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

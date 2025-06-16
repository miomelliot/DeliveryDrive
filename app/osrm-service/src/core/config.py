# src/core/config.py
import os
from functools import lru_cache

from pydantic import Field, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # -- базовые переменные; в контейнере переопределяются через ENV ------------
    user: str = Field("postgres", alias="POSTGRES_USER")
    password: str = Field("postgres", alias="POSTGRES_PASSWORD")
    host: str = Field("localhost", alias="POSTGRES_HOST")
    port: int = Field(5432, alias="POSTGRES_PORT")
    db: str = Field("postgres", alias="POSTGRES_DB")

    # -- Neo4j ------------------------------------------------------------------
    neo4j_user: str = Field("neo4j", alias="NEO4J_USER")
    neo4j_password: str = Field("neo4j", alias="NEO4J_PASSWORD")
    neo4j_scheme: str = Field("bolt", alias="NEO4J_SCHEME")
    neo4j_host: str = Field("localhost", alias="NEO4J_HOST")
    neo4j_port: int = Field(7687, alias="NEO4J_PORT")

    @property
    def neo4j_dsn(self) -> str:
        return f"{self.neo4j_scheme}://{self.neo4j_host}:{self.neo4j_port}"

    # --- App / Debug ----------------------------------------------------------
    debug: bool = Field(False, alias="DEBUG")

    # -- готовый DSN для SQLAlchemy ---------------------------------------------
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

    # -- pydantic-config --------------------------------------------------------
    model_config = SettingsConfigDict(
        env_file=os.getenv("ENV_FILE", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Синглтон метод"""
    return Settings()  # type: ignore

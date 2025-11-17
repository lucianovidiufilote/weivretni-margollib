"""Application configuration."""
from __future__ import annotations

from decimal import Decimal
from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment driven configuration for the API and worker."""

    api_host: str = Field("0.0.0.0", validation_alias="API_HOST")
    api_port: int = Field(8000, validation_alias="API_PORT")

    database_host: str = Field("db", validation_alias="DATABASE_HOST")
    database_port: int = Field(5432, validation_alias="DATABASE_PORT")
    database_user: str = Field("app", validation_alias="DATABASE_USER")
    database_password: str = Field("app", validation_alias="DATABASE_PASSWORD")
    database_name: str = Field("app", validation_alias="DATABASE_NAME")

    redis_host: str = Field("redis", validation_alias="REDIS_HOST")
    redis_port: int = Field(6379, validation_alias="REDIS_PORT")
    redis_db: int = Field(0, validation_alias="REDIS_DB")

    worker_queue: str = Field("app:jobs", validation_alias="WORKER_QUEUE")
    worker_poll_interval: float = Field(2.0, validation_alias="WORKER_POLL_INTERVAL")
    notification_channel: str = Field("notifications", validation_alias="NOTIFICATION_CHANNEL")
    alert_channel: str = Field("alerts", validation_alias="ALERT_CHANNEL")
    alert_threshold: Decimal = Field(Decimal("1000"), validation_alias="ALERT_THRESHOLD")
    aggregation_cooldown_seconds: int = Field(60, validation_alias="AGGREGATION_COOLDOWN_SECONDS")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.database_user}:{self.database_password}"
            f"@{self.database_host}:{self.database_port}/{self.database_name}"
        )

    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"


@lru_cache
def get_settings() -> Settings:
    """Return a cached settings instance."""

    return Settings()

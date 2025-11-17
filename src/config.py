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

    kafka_bootstrap_servers: str = Field("kafka:9092", validation_alias="KAFKA_BOOTSTRAP_SERVERS")
    records_topic: str = Field("records.in", validation_alias="RECORDS_TOPIC")
    notifications_topic: str = Field("notifications", validation_alias="NOTIFICATIONS_TOPIC")
    alerts_topic: str = Field("alerts", validation_alias="ALERTS_TOPIC")

    outbox_batch_size: int = Field(100, validation_alias="OUTBOX_BATCH_SIZE")
    outbox_poll_interval: float = Field(0.5, validation_alias="OUTBOX_POLL_INTERVAL")

    default_alert_threshold: Decimal = Field(Decimal("1000"), validation_alias="DEFAULT_ALERT_THRESHOLD")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.database_user}:{self.database_password}"
            f"@{self.database_host}:{self.database_port}/{self.database_name}"
        )


@lru_cache
def get_settings() -> Settings:
    """Return a cached settings instance."""

    return Settings()

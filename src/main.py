"""Application entrypoint."""
from __future__ import annotations

from fastapi import FastAPI

from src.db import init_models
from src.api.records import router as records_router
from src.api.health import router as health_router


async def on_startup() -> None:
    await init_models()


async def on_shutdown() -> None:
    from src.services.kafka import stop_kafka_producer  # lazy import to avoid unused if never started

    await stop_kafka_producer()


app = FastAPI(title="Interview Service", version="0.1.0")
app.include_router(records_router)
app.include_router(health_router)
app.add_event_handler("startup", on_startup)
app.add_event_handler("shutdown", on_shutdown)

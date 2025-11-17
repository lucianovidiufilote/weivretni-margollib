"""Application entrypoint."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.db import init_models
from src.api.records import router as records_router
from src.api.health import router as health_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    await init_models()
    yield


app = FastAPI(title="Interview Service", version="0.1.0", lifespan=lifespan)
app.include_router(records_router)
app.include_router(health_router)

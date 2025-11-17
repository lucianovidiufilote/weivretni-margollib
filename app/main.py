"""Application entrypoint."""
from __future__ import annotations

from fastapi import FastAPI

from app.services.health import combined_health

app = FastAPI(title="Interview Service", version="0.1.0")


@app.get("/health", summary="Service health check")
async def health() -> dict[str, object]:
    """Return aggregated component health information."""

    return await combined_health()

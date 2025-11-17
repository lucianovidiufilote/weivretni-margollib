"""Health endpoint."""
from __future__ import annotations

from fastapi import APIRouter

from src.services.health import combined_health

router = APIRouter()


@router.get("/health", summary="Service health check")
async def health() -> dict[str, object]:
    """Return aggregated component health information."""

    return await combined_health()

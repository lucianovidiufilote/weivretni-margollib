"""Health check helpers."""
from __future__ import annotations

from typing import Any, Dict

import asyncpg

from src.config import get_settings


async def postgres_health() -> Dict[str, Any]:
    """Attempt a simple query against Postgres to verify connectivity."""

    settings = get_settings()
    try:
        conn = await asyncpg.connect(
            host=settings.database_host,
            port=settings.database_port,
            user=settings.database_user,
            password=settings.database_password,
            database=settings.database_name,
            timeout=5,
        )
    except Exception as exc:  # pragma: no cover - diagnosic path
        return {"status": "error", "detail": str(exc)}

    try:
        await conn.execute("SELECT 1")
    finally:
        await conn.close()

    return {"status": "ok"}


async def combined_health() -> Dict[str, Any]:
    """Aggregate all component health checks."""

    postgres_result = await postgres_health()
    return {"status": postgres_result["status"], "components": {"postgres": postgres_result}}

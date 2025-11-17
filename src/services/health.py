"""Health check helpers."""
from __future__ import annotations

import asyncio
from typing import Any, Dict

import asyncpg
import redis.asyncio as aioredis

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


async def redis_health() -> Dict[str, Any]:
    """Ping the Redis instance to ensure it is reachable."""

    settings = get_settings()
    client = aioredis.from_url(settings.redis_url, decode_responses=True)
    try:
        response = await client.ping()
    except Exception as exc:  # pragma: no cover - diagnostic path
        return {"status": "error", "detail": str(exc)}
    finally:
        await client.close()

    return {"status": "ok", "detail": f"pong={response}"}


async def combined_health() -> Dict[str, Any]:
    """Aggregate all component health checks."""

    postgres_task = asyncio.create_task(postgres_health())
    redis_task = asyncio.create_task(redis_health())

    postgres_result, redis_result = await asyncio.gather(postgres_task, redis_task)

    overall = "ok" if postgres_result["status"] == "ok" and redis_result["status"] == "ok" else "degraded"

    return {
        "status": overall,
        "components": {
            "postgres": postgres_result,
            "redis": redis_result,
        },
    }

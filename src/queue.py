"""Helpers for interacting with the background job queue."""
from __future__ import annotations

from redis import Redis
from rq import Queue

from src.config import get_settings


def get_redis_connection() -> Redis:
    settings = get_settings()
    return Redis(host=settings.redis_host, port=settings.redis_port, db=settings.redis_db)


def get_worker_queue(name: str | None = None) -> Queue:
    settings = get_settings()
    queue_name = name or settings.worker_queue

    return Queue(queue_name, connection=get_redis_connection())

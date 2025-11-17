"""Helpers for interacting with the background job queue."""
from __future__ import annotations

from redis import Redis
from rq import Queue

from app.config import get_settings


def get_connection() -> Redis:
    settings = get_settings()
    return Redis(host=settings.redis_host, port=settings.redis_port, db=settings.redis_db)


def get_queue(name: str | None = None) -> Queue:
    settings = get_settings()
    queue_name = name or settings.worker_queue

    return Queue(queue_name, connection=get_connection())

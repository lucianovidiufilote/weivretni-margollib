"""Aggregation snapshot rebuild and scheduling helpers."""
from __future__ import annotations


import logging

from redis import Redis
from rq import Retry

from src.config import get_settings
from src.queue import get_redis_connection, get_worker_queue

LOCK_KEY = "aggregation:cooldown"
logger = logging.getLogger(__name__)


def _get_redis() -> Redis:
    return get_redis_connection()


def request_aggregation_run() -> bool:
    """Enqueue the aggregation job if the cooldown allows it."""

    settings = get_settings()
    conn = _get_redis()
    acquired = conn.set(LOCK_KEY, "1", nx=True, ex=settings.aggregation_cooldown_seconds)
    if acquired:
        queue = get_worker_queue()
        queue.enqueue(
            "src.services.aggregation_scheduler.recompute_destination_summaries",
            retry=Retry(max=3, interval=[10, 30, 60]),
        )
        return True
    return False

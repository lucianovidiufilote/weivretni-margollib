"""Outbox dispatcher worker."""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Awaitable, Callable

from aiokafka import AIOKafkaProducer

from src.config import get_settings
from src.db import async_session_factory
from src.services.outbox import fetch_pending_events, mark_event_published

logger = logging.getLogger(__name__)


async def dispatch_once(producer: AIOKafkaProducer) -> bool:
    settings = get_settings()
    async with async_session_factory() as session:
        async with session.begin():
            rows = await fetch_pending_events(session, limit=settings.outbox_batch_size)
            if not rows:
                return False

            for row in rows:
                event_id = row["id"]
                destination = row["destination"]
                payload = row["payload"]
                await producer.send_and_wait(destination, payload)
                await mark_event_published(session, event_id)
                logger.info("Published outbox %s to %s", event_id, destination)
    return True


async def run_dispatcher() -> None:
    settings = get_settings()
    producer = AIOKafkaProducer(
        bootstrap_servers=settings.kafka_bootstrap_servers,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )
    await producer.start()
    try:
        while True:
            has_work = await dispatch_once(producer)
            if not has_work:
                await asyncio.sleep(settings.outbox_poll_interval)
    finally:
        await producer.stop()


async def worker_loop(handler: Callable[[], Awaitable[None]], name: str) -> None:
    while True:
        try:
            await handler()
        except Exception:  # pragma: no cover - diagnostics
            logger.exception("%s encountered an error", name)
            await asyncio.sleep(1)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s %(name)s %(message)s")
    asyncio.run(worker_loop(run_dispatcher, "outbox-dispatcher"))


if __name__ == "__main__":
    main()

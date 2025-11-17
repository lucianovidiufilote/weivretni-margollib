"""Outbox dispatcher worker."""
from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any

from aiokafka import AIOKafkaProducer
from sqlalchemy import text

from src.config import get_settings
from src.db import async_session_factory

logger = logging.getLogger(__name__)


async def dispatch_once(producer: AIOKafkaProducer) -> bool:
    settings = get_settings()
    async with async_session_factory() as session:
        async with session.begin():
            stmt = text(
                """
                SELECT id, destination, payload
                FROM outbox
                WHERE published_at IS NULL
                ORDER BY created_at
                LIMIT :limit
                FOR UPDATE SKIP LOCKED
                """
            )
            result = await session.execute(
                stmt,
                {"limit": settings.outbox_batch_size},
            )
            mapping_result = result.mappings()
            rows = mapping_result.all()
            if not rows:
                return False

            for row in rows:
                event_id = row["id"]
                destination = row["destination"]
                payload: Any = row["payload"]
                await producer.send_and_wait(destination, payload)
                logger.info("Published outbox %s to %s", event_id, destination)
                await session.execute(
                    text("UPDATE outbox SET published_at = :published WHERE id = :id"),
                    {"published": datetime.now(tz=timezone.utc), "id": event_id},
                )
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


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s %(name)s %(message)s")
    asyncio.run(run_dispatcher())


if __name__ == "__main__":
    main()

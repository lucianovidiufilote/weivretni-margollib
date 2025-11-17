"""Kafka producer utilities."""
from __future__ import annotations

import asyncio
import json
from typing import Any

from aiokafka import AIOKafkaProducer

from src.config import get_settings

_producer: AIOKafkaProducer | None = None
_producer_lock = asyncio.Lock()


async def get_or_create_producer() -> AIOKafkaProducer:
    global _producer
    if _producer is not None:
        return _producer
    async with _producer_lock:
        if _producer is None:
            settings = get_settings()
            producer = AIOKafkaProducer(
                bootstrap_servers=settings.kafka_bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            )
            await producer.start()
            _producer = producer
    return _producer


async def stop_kafka_producer() -> None:
    global _producer
    async with _producer_lock:
        if _producer is None:
            return
        await _producer.stop()
        _producer = None


def get_kafka_producer_sync() -> AIOKafkaProducer:
    if _producer is None:
        raise RuntimeError("Kafka producer is not initialized. Call get_or_create_producer() first.")
    return _producer

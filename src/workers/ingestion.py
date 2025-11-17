"""Kafka ingestion worker."""
from __future__ import annotations

import asyncio
import logging

from aiokafka import AIOKafkaConsumer
from sqlalchemy.dialects.postgresql import insert

from src.config import get_settings
from src.db import async_session_factory
from src.models import Aggregate, OutboxEvent, Record, RecordType
from src.schemas import RecordPayload

logger = logging.getLogger(__name__)


async def _process_payload(payload: RecordPayload) -> None:
    settings = get_settings()

    async with async_session_factory() as session:
        async with session.begin():
            record_stmt = (
                insert(Record)
                .values(
                    record_id=payload.record_id,
                    time=payload.time,
                    source_id=payload.source_id,
                    destination_id=payload.destination_id,
                    type=payload.type,
                    value=payload.value,
                    unit=payload.unit,
                    reference=payload.reference,
                )
                .on_conflict_do_nothing()
                .returning(
                    Record.record_id,
                    Record.time,
                    Record.source_id,
                    Record.destination_id,
                    Record.type,
                    Record.value,
                    Record.unit,
                    Record.reference,
                )
            )

            record_result = await session.execute(record_stmt)
            row = record_result.mappings().first()
            if row is None:
                logger.info("Duplicate record %s ignored", payload.record_id)
                return

            signed_value = payload.value if payload.type == RecordType.POSITIVE else -payload.value

            aggregate_stmt = (
                insert(Aggregate)
                .values(
                    destination_id=payload.destination_id,
                    reference=payload.reference,
                    total_value=signed_value,
                    record_count=1,
                    last_record_id=payload.record_id,
                    last_time=payload.time,
                )
                .on_conflict_do_update(
                    index_elements=[Aggregate.destination_id, Aggregate.reference],
                    set_={
                        "total_value": Aggregate.total_value + signed_value,
                        "record_count": Aggregate.record_count + 1,
                        "last_record_id": payload.record_id,
                        "last_time": payload.time,
                    },
                )
                .returning(
                    Aggregate.destination_id,
                    Aggregate.reference,
                    Aggregate.total_value,
                    Aggregate.record_count,
                    Aggregate.last_time,
                )
            )

            aggregate_result = await session.execute(aggregate_stmt)
            aggregate_row = aggregate_result.mappings().one()

            record_dict = payload.model_dump(by_alias=True)
            record_dict["time"] = payload.time.isoformat()
            record_dict["value"] = float(payload.value)
            summary = {
                "destinationId": aggregate_row["destination_id"],
                "reference": aggregate_row["reference"],
                "totalValue": float(aggregate_row["total_value"]),
                "count": int(aggregate_row["record_count"]),
                "lastTime": aggregate_row["last_time"].isoformat(),
            }

            notification_payload = {
                "record": record_dict,
                "summary": summary,
            }

            await session.execute(
                insert(OutboxEvent).values(
                    event_type="notification",
                    destination=settings.notifications_topic,
                    payload=notification_payload,
                )
            )

            if payload.value >= settings.default_alert_threshold:
                alert_payload = {
                    "record": record_dict,
                    "threshold": float(settings.default_alert_threshold),
                }
                await session.execute(
                    insert(OutboxEvent).values(
                        event_type="alert",
                        destination=settings.alerts_topic,
                        payload=alert_payload,
                    )
                )


async def consume_records() -> None:
    settings = get_settings()
    consumer = AIOKafkaConsumer(
        settings.records_topic,
        bootstrap_servers=settings.kafka_bootstrap_servers,
        group_id="records-processor",
        enable_auto_commit=False,
        value_deserializer=lambda v: RecordPayload.model_validate_json(v),
    )

    await consumer.start()
    try:
        async for message in consumer:
            payload: RecordPayload = message.value
            try:
                await _process_payload(payload)
                await consumer.commit()
            except Exception:  # pragma: no cover - worker diagnostics
                logger.exception("Failed to process record %s", payload.record_id)
                await asyncio.sleep(1)
    finally:
        await consumer.stop()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s %(name)s %(message)s")
    asyncio.run(consume_records())


if __name__ == "__main__":
    main()

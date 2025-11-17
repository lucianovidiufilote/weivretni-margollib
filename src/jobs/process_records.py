"""Core record processing pipeline used by the worker."""
from __future__ import annotations

import asyncio
from decimal import Decimal
from typing import Any, Mapping

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_settings
from src.db import async_session_factory
from src.models import DestinationSummary, Record
from src.notifications import publish_alert, publish_notification
from src.services.aggregation_scheduler import request_aggregation_run
from src.schemas import ProcessResult, RecordPayload, SummarySnapshot
from src.utils import _as_decimal


async def _insert_record(session: AsyncSession, payload: RecordPayload) -> bool:
    stmt = (
        insert(Record)
        .values(
            record_id=payload.record_id,
            event_time=payload.time,
            source_id=payload.source_id,
            destination_id=payload.destination_id,
            record_type=payload.type,
            value=payload.value,
            unit=payload.unit,
            reference=payload.reference,
        )
        .on_conflict_do_nothing(index_elements=[Record.record_id])
        .returning(Record.id)
    )

    result = await session.execute(stmt)
    inserted = result.scalar_one_or_none()
    return inserted is not None


async def _load_cached_summary(session: AsyncSession, payload: RecordPayload) -> SummarySnapshot:
    stmt = select(
        DestinationSummary.total_value,
        DestinationSummary.record_count,
        DestinationSummary.last_record_time,
    ).where(
        DestinationSummary.destination_id == payload.destination_id,
        DestinationSummary.reference == payload.reference,
    )

    result = await session.execute(stmt)
    row = result.one_or_none()
    if not row:
        return SummarySnapshot(
            destination_id=payload.destination_id,
            reference=payload.reference,
            total_value=Decimal("0"),
            record_count=0,
            last_record_time=None,
        )

    return SummarySnapshot(
        destination_id=payload.destination_id,
        reference=payload.reference,
        total_value=_as_decimal(row.total_value),
        record_count=row.record_count,
        last_record_time=row.last_record_time,
    )


async def process_record_payload(payload: RecordPayload) -> ProcessResult:
    """Persist a record, update aggregates, and emit notifications."""

    async with async_session_factory() as session:
        async with session.begin():
            inserted = await _insert_record(session, payload)
            if not inserted:
                return ProcessResult(duplicate=True)

        summary = await _load_cached_summary(session, payload)
        if summary.last_record_time is None:
            summary.last_record_time = payload.time

    # send notification
    publish_notification(payload, summary)

    # send alert if threshold is exceeded
    settings = get_settings()
    threshold = _as_decimal(settings.alert_threshold)
    if payload.value >= threshold:
        publish_alert(payload, summary)

    # trigger aggregation run
    request_aggregation_run()

    return ProcessResult(duplicate=False, summary=summary)


def process_record_job(record_data: Mapping[str, Any]) -> ProcessResult:
    """RQ job entrypoint. Accepts dictionaries so it can be enqueued via JSON."""

    #raise RuntimeError("process_record_job should not be called directly")

    payload = RecordPayload(**record_data)
    return asyncio.run(process_record_payload(payload))

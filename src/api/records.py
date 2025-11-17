"""Record ingestion and query API."""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from decimal import Decimal
from typing import Dict, List

from fastapi import APIRouter, Depends, Query
from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_settings
from src.db import get_session
from src.models import Record, RecordType
from src.schemas import AggregationGroup, RecordAcceptedResponse, RecordDTO, RecordPayload
from src.services.kafka import get_kafka_producer

router = APIRouter(prefix="/records", tags=["records"])


@router.post("", response_model=RecordAcceptedResponse, status_code=202)
async def submit_record(payload: RecordPayload) -> RecordAcceptedResponse:
    """Enqueue a record for background processing."""

    producer = get_kafka_producer()
    settings = get_settings()
    await producer.send_and_wait(settings.records_topic, payload.model_dump(by_alias=True, mode="json"))

    return RecordAcceptedResponse(job_id=payload.record_id, record_id=payload.record_id)


def _apply_filters(
        stmt: Select[tuple[Record]],
        start_time: datetime | None,
        end_time: datetime | None,
        record_type: RecordType | None,
) -> Select[tuple[Record]]:
    if start_time:
        stmt = stmt.where(Record.time >= start_time)
    if end_time:
        stmt = stmt.where(Record.time <= end_time)
    if record_type:
        stmt = stmt.where(Record.type == record_type)
    return stmt


@router.get("/aggregations", response_model=list[AggregationGroup])
async def aggregated_records(
        start_time: datetime | None = Query(None, alias="startTime"),
        end_time: datetime | None = Query(None, alias="endTime"),
        record_type: RecordType | None = Query(None, alias="type"),
        session: AsyncSession = Depends(get_session),
) -> list[AggregationGroup]:
    """Return grouped records along with the summed value per destination."""

    stmt = select(Record).order_by(Record.destination_id, Record.time)
    stmt = _apply_filters(stmt, start_time, end_time, record_type)

    result = await session.execute(stmt)
    rows = result.scalars().all()

    grouped: Dict[str, Dict[str, object]] = defaultdict(lambda: {"records": [], "total": Decimal("0")})

    for row in rows:
        dto = RecordDTO(
            record_id=row.record_id,
            time=row.time,
            source_id=row.source_id,
            destination_id=row.destination_id,
            type=row.type,
            value=row.value,
            unit=row.unit,
            reference=row.reference,
        )
        group = grouped[row.destination_id]
        group["records"].append(dto)
        signed_value = row.value if row.type == RecordType.POSITIVE else -row.value
        group["total"] += signed_value

    response: List[AggregationGroup] = []
    for destination_id, data in grouped.items():
        response.append(
            AggregationGroup(
                destination_id=destination_id,
                total_value=data["total"],
                records=data["records"],
            )
        )

    return response

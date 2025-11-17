"""Record ingestion and query API."""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from decimal import Decimal
from typing import Dict, List
from rq import Retry

from fastapi import APIRouter, Depends, Query
from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db import get_session
from src.models import Record, RecordType
from src.queue import get_worker_queue
from src.schemas import AggregationGroup, RecordAcceptedResponse, RecordDTO, RecordPayload

router = APIRouter(prefix="/records", tags=["records"])


@router.post("", response_model=RecordAcceptedResponse, status_code=202)
async def submit_record(payload: RecordPayload) -> RecordAcceptedResponse:
    """Enqueue a record for background processing."""

    queue = get_worker_queue()
    job = queue.enqueue("src.jobs.process_records.process_record_job", payload.model_dump(by_alias=True),
                        retry=Retry(max=3, interval=[10, 30, 60]))

    return RecordAcceptedResponse(job_id=job.id, record_id=payload.record_id)


def _apply_filters(
        stmt: Select[tuple[Record]],
        start_time: datetime | None,
        end_time: datetime | None,
        record_type: RecordType | None,
) -> Select[tuple[Record]]:
    if start_time:
        stmt = stmt.where(Record.event_time >= start_time)
    if end_time:
        stmt = stmt.where(Record.event_time <= end_time)
    if record_type:
        stmt = stmt.where(Record.record_type == record_type)
    return stmt


@router.get("/aggregations", response_model=list[AggregationGroup])
async def aggregated_records(
        start_time: datetime | None = Query(None, alias="startTime"),
        end_time: datetime | None = Query(None, alias="endTime"),
        record_type: RecordType | None = Query(None, alias="type"),
        session: AsyncSession = Depends(get_session),
) -> list[AggregationGroup]:
    """Return grouped records along with the summed value per destination."""

    stmt = select(Record).order_by(Record.destination_id, Record.event_time)
    stmt = _apply_filters(stmt, start_time, end_time, record_type)

    result = await session.execute(stmt)
    rows = result.scalars().all()

    grouped: Dict[str, Dict[str, object]] = defaultdict(lambda: {"records": [], "total": Decimal("0")})

    for row in rows:
        dto = RecordDTO(
            record_id=row.record_id,
            time=row.event_time,
            source_id=row.source_id,
            destination_id=row.destination_id,
            type=row.record_type,
            value=row.value,
            unit=row.unit,
            reference=row.reference,
        )
        group = grouped[row.destination_id]
        group["records"].append(dto)
        signed_value = row.value if row.record_type == RecordType.POSITIVE else -row.value
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

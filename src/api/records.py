"""Record ingestion and query API."""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_settings
from src.db import get_session
from src.models import RecordType
from src.services.aggregations import fetch_aggregations
from src.schemas import AggregationGroup, RecordAcceptedResponse, RecordPayload
from src.services.kafka import get_or_create_producer

router = APIRouter(prefix="/records", tags=["records"])


@router.post("", response_model=RecordAcceptedResponse, status_code=202)
async def submit_record(payload: RecordPayload) -> RecordAcceptedResponse:
    producer = await get_or_create_producer()
    settings = get_settings()
    await producer.send_and_wait(settings.records_topic, payload.model_dump(by_alias=True, mode="json"))
    return RecordAcceptedResponse(job_id=payload.record_id, record_id=payload.record_id)


@router.get("/aggregations", response_model=list[AggregationGroup])
async def aggregated_records(
    start_time: datetime | None = Query(None, alias="startTime"),
    end_time: datetime | None = Query(None, alias="endTime"),
    record_type: RecordType | None = Query(None, alias="type"),
    session: AsyncSession = Depends(get_session),
) -> list[AggregationGroup]:
    return await fetch_aggregations(
        session,
        start_time=start_time,
        end_time=end_time,
        record_type=record_type,
    )

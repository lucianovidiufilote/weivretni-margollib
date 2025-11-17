"""Query helpers for record aggregations."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Dict, List

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Record, RecordType
from src.schemas import AggregationGroup, RecordDTO


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


async def fetch_aggregations(
    session: AsyncSession,
    *,
    start_time: datetime | None,
    end_time: datetime | None,
    record_type: RecordType | None,
) -> List[AggregationGroup]:
    stmt = select(Record).order_by(Record.destination_id, Record.time)
    stmt = _apply_filters(stmt, start_time, end_time, record_type)

    result = await session.execute(stmt)
    rows = result.scalars().all()

    grouped: Dict[str, Dict[str, object]] = {}
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
        entry = grouped.setdefault(row.destination_id, {"records": [], "total": Decimal("0")})
        entry["records"].append(dto)
        signed_value = row.value if row.type == RecordType.POSITIVE else -row.value
        entry["total"] += signed_value

    return [
        AggregationGroup(
            destination_id=destination_id,
            total_value=data["total"],
            records=data["records"],
        )
        for destination_id, data in grouped.items()
    ]

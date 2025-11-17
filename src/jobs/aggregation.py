"""Aggregation routines executed by the periodic worker."""
from __future__ import annotations

import asyncio
from sqlalchemy import case, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
import logging
from src.db import async_session_factory
from src.models import DestinationSummary, Record, RecordType

logger = logging.getLogger(__name__)

async def rebuild_destination_summaries(session: AsyncSession) -> int:
    """Recompute destination summaries from the raw records table."""

    await session.execute(delete(DestinationSummary))

    stmt = (
        select(
            Record.destination_id.label("destination_id"),
            Record.reference.label("reference"),
            func.coalesce(
                func.sum(
                    case(
                        (Record.record_type == RecordType.POSITIVE, Record.value),
                        else_=-Record.value,
                    )
                ),
                0,
            ).label("total_value"),
            func.count().label("record_count"),
            func.max(Record.event_time).label("last_record_time"),
        )
        .group_by(Record.destination_id, Record.reference)
    )

    result = await session.execute(stmt)
    rows = result.all()

    summaries = [
        DestinationSummary(
            destination_id=row.destination_id,
            reference=row.reference,
            total_value=row.total_value,
            record_count=row.record_count,
            last_record_time=row.last_record_time,
        )
        for row in rows
    ]

    if summaries:
        session.add_all(summaries)

    return len(summaries)


async def _run_job() -> int:
    async with async_session_factory() as session:
        async with session.begin():
            return await rebuild_destination_summaries(session)


def recompute_destination_summaries() -> int:
    """RQ job entry point."""

    result = asyncio.run(_run_job())
    logger.info("Aggregation snapshot rebuilt (%s groups)", result)
    return result

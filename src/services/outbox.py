"""Helpers for working with outbox events."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Sequence

from sqlalchemy import insert, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import OutboxEvent


async def enqueue_outbox_event(
    session: AsyncSession,
    *,
    event_type: str,
    destination: str,
    payload: Any,
) -> None:
    """Persist an outbox event."""

    await session.execute(
        insert(OutboxEvent).values(
            event_type=event_type,
            destination=destination,
            payload=payload,
        )
    )


async def fetch_pending_events(session: AsyncSession, *, limit: int) -> Sequence[dict[str, Any]]:
    """Return unpublished outbox rows and acquire a lock on them."""

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
    result = await session.execute(stmt, {"limit": limit})
    return result.mappings().all()


async def mark_event_published(session: AsyncSession, event_id: str) -> None:
    """Mark a row as published."""

    await session.execute(
        text("UPDATE outbox SET published_at = :published WHERE id = :id"),
        {"published": datetime.now(tz=timezone.utc), "id": event_id},
    )

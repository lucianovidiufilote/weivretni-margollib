"""Database models."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum
from uuid import uuid4

from sqlalchemy import DateTime, Enum as SAEnum, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.db import Base


class RecordType(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"


class Record(Base):
    __tablename__ = "records"

    record_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source_id: Mapped[str] = mapped_column(String(64), nullable=False)
    destination_id: Mapped[str] = mapped_column(String(64), nullable=False)
    type: Mapped[RecordType] = mapped_column(SAEnum(RecordType, name="record_type"), nullable=False)
    value: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    unit: Mapped[str] = mapped_column(String(16), nullable=False)
    reference: Mapped[str] = mapped_column(String(64), nullable=False)
    processed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class Aggregate(Base):
    __tablename__ = "aggregates"

    destination_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    reference: Mapped[str] = mapped_column(String(64), primary_key=True)
    total_value: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    record_count: Mapped[int] = mapped_column(nullable=False)
    last_record_id: Mapped[str] = mapped_column(String(64), nullable=False)
    last_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class Threshold(Base):
    __tablename__ = "thresholds"

    destination_id: Mapped[str | None] = mapped_column(String(64), primary_key=True)
    reference: Mapped[str | None] = mapped_column(String(64), primary_key=True)
    unit: Mapped[str] = mapped_column(String(16), primary_key=True)
    threshold: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)


class OutboxEvent(Base):
    __tablename__ = "outbox"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    event_type: Mapped[str] = mapped_column(String(32), nullable=False)
    destination: Mapped[str] = mapped_column(Text, nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    retries: Mapped[int] = mapped_column(nullable=False, default=0)

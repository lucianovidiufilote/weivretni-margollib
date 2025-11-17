"""Database models."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum

from sqlalchemy import DateTime, Enum as SAEnum, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from src.db import Base


class RecordType(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"


class Record(Base):
    """Individual data record ingested by the service."""

    __tablename__ = "records"

    id: Mapped[int] = mapped_column(primary_key=True)
    record_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    event_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    source_id: Mapped[str] = mapped_column(String(64))
    destination_id: Mapped[str] = mapped_column(String(64), index=True)
    record_type: Mapped[RecordType] = mapped_column(SAEnum(RecordType, name="record_type"))
    value: Mapped[Decimal] = mapped_column(Numeric(18, 4))
    unit: Mapped[str] = mapped_column(String(16))
    reference: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class DestinationSummary(Base):
    """Running aggregate per destination and reference."""

    __tablename__ = "destination_summaries"
    __table_args__ = (UniqueConstraint("destination_id", "reference", name="uq_destination_reference"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    destination_id: Mapped[str] = mapped_column(String(64), index=True)
    reference: Mapped[str] = mapped_column(String(64))
    total_value: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0)
    record_count: Mapped[int] = mapped_column(default=0)
    last_record_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

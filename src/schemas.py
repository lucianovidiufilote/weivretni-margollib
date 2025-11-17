"""Pydantic schemas shared across API and worker."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from src.models import RecordType


class RecordPayload(BaseModel):
    """Incoming record schema."""

    record_id: str = Field(..., alias="recordId")
    time: datetime
    source_id: str = Field(..., alias="sourceId")
    destination_id: str = Field(..., alias="destinationId")
    type: RecordType = Field(..., alias="type")
    value: Decimal
    unit: str
    reference: str

    model_config = ConfigDict(populate_by_name=True, frozen=True, use_enum_values=True)


class RecordAcceptedResponse(BaseModel):
    """Response returned when a record has been enqueued for processing."""

    job_id: str = Field(..., alias="jobId")
    record_id: str = Field(..., alias="recordId")
    status: str = "accepted"

    model_config = ConfigDict(populate_by_name=True)


class RecordDTO(BaseModel):
    """Representation of a stored record."""

    record_id: str = Field(..., alias="recordId")
    time: datetime
    source_id: str = Field(..., alias="sourceId")
    destination_id: str = Field(..., alias="destinationId")
    type: RecordType
    value: Decimal
    unit: str
    reference: str

    model_config = ConfigDict(populate_by_name=True, use_enum_values=True)


class AggregationQueryParams(BaseModel):
    """Query parameter container for aggregation endpoint."""

    start_time: Optional[datetime] = Field(None, alias="startTime")
    end_time: Optional[datetime] = Field(None, alias="endTime")
    type: Optional[RecordType] = None


class AggregationGroup(BaseModel):
    """Response element representing a destination group."""

    destination_id: str = Field(..., alias="destinationId")
    total_value: Decimal = Field(..., alias="totalValue")
    records: List[RecordDTO]

    model_config = ConfigDict(populate_by_name=True)

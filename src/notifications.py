"""Publish messages for downstream services."""
from __future__ import annotations

from jobs.process_records import SummarySnapshot
from src.queue import get_redis_connection
from src.config import get_settings
from src.schemas import RecordPayload
from src.utils import _dump


def publish_notification(record: RecordPayload, summary: SummarySnapshot) -> None:
    """Publish full record payload plus running summary."""

    settings = get_settings()
    client = get_redis_connection()

    message = _dump(
        {
            "type": "notification",
            "record": record.model_dump(by_alias=True),
            "summary": {
                "destinationId": summary.destination_id,
                "reference": summary.reference,
                "totalValue": format(summary.total_value, "f"),
                "recordCount": summary.record_count,
                "lastRecordTime": summary.last_record_time.isoformat(),
            },
        }
    )
    client.publish(settings.notification_channel, message)
    client.close()


def publish_alert(record: RecordPayload, summary: SummarySnapshot) -> None:
    """Emit alert messages to a dedicated channel when value crosses the threshold."""

    settings = get_settings()
    client = get_redis_connection()

    message = _dump(
        {
            "type": "alert",
            "recordId": record.record_id,
            "value": format(record.value, "f"),
            "destinationId": record.destination_id,
            "reference": record.reference,
            "summaryValue": format(summary.total_value, "f"),
        }
    )
    client.publish(settings.alert_channel, message)
    client.close()

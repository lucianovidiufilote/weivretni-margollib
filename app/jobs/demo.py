"""Demo jobs used for validating the worker pipeline."""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict

logger = logging.getLogger(__name__)


def log_message(payload: Dict[str, Any] | None = None) -> None:
    """Log the payload to illustrate that the worker executed a job."""

    logger.info("RQ job received payload %s at %s", payload, datetime.utcnow().isoformat())

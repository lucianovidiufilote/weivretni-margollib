from __future__ import annotations

import json
from datetime import datetime
from decimal import Decimal
from typing import Any


def _dump(payload: dict[str, Any]) -> str:
    return json.dumps(payload, default=_serialize)


def _serialize(value: Any) -> str:
    if isinstance(value, (datetime,)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return format(value, "f")
    raise TypeError(f"Unsupported type {type(value)}")


def _as_decimal(value: Decimal | float | int) -> Decimal:
    return Decimal(str(value))

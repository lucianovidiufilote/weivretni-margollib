"""Utility script for enqueuing demo RQ jobs."""
from __future__ import annotations

from datetime import datetime

from app.queue import get_queue


def main() -> None:
    queue = get_queue()
    job = queue.enqueue(
        "app.jobs.demo.log_message",
        {"source": "devtools", "enqueued_at": datetime.utcnow().isoformat()},
    )
    print(f"Enqueued job {job.id} targeting queue '{queue.name}'")


if __name__ == "__main__":
    main()

"""RQ worker runner."""
from __future__ import annotations

import logging

from rq import Connection, Worker

from app.config import get_settings
from app.queue import get_connection

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    settings = get_settings()
    connection = get_connection()

    logger.info("Starting RQ worker for queue '%s'", settings.worker_queue)

    with Connection(connection):
        worker = Worker([settings.worker_queue])
        worker.work(with_scheduler=True)


if __name__ == "__main__":
    main()

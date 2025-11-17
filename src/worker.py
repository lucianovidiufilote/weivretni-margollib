"""RQ worker runner."""
from __future__ import annotations

import logging

from rq import Worker

from src.config import get_settings
from src.queue import get_redis_connection

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    settings = get_settings()
    connection = get_redis_connection()

    logger.info("Starting RQ worker for queue '%s'", settings.worker_queue)

    worker = Worker([settings.worker_queue],  connection = connection)
    worker.work(with_scheduler=True)

if __name__ == "__main__":
    main()

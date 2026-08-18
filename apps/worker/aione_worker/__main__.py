"""Run the relay and worker together for local development.

Production runs them as separate processes; a single process here keeps the
local topology to one command.
"""

from __future__ import annotations

import logging
import os
import sys
import time

import redis

from .relay import Relay
from .runtime import Worker


def main() -> int:
    logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"), stream=sys.stdout)
    database_url = os.environ.get("DATABASE_URL_WORKER", "").strip()
    if not database_url:
        sys.stderr.write("DATABASE_URL_WORKER is not set\n")
        return 2

    relay = Relay(database_url, redis.from_url(os.environ.get("REDIS_URL", "redis://localhost:56379/0")))
    worker = Worker(database_url)

    while True:
        relay.publish_pending()
        if worker.tick() is None:
            time.sleep(1.0)


if __name__ == "__main__":
    raise SystemExit(main())

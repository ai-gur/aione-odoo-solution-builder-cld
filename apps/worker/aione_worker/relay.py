"""Transactional outbox relay.

Moves committed outbox rows onto the queue. It is the only component allowed
to publish, and it publishes *after* the transaction that wrote the row has
committed — which is what makes "the queue never saw an event that did not
happen" true.

The relay is allowed to publish the same row twice. It marks a row published
after handing it to Redis, so a crash in between produces a duplicate delivery
rather than a lost one. Losing work is unrecoverable; duplicating it is
absorbed by the job's idempotency key, and the duplicate-delivery test proves
that absorption rather than assuming it.
"""

from __future__ import annotations

import logging

import psycopg
from psycopg.rows import dict_row

logger = logging.getLogger("aione.relay")

QUEUE_KEY = "aione:jobs"


class Relay:
    def __init__(self, database_url: str, redis_client) -> None:
        self.database_url = database_url
        self.redis = redis_client

    def publish_pending(self, *, batch_size: int = 100) -> int:
        """Publish unpublished outbox rows. Returns how many were published."""
        published = 0
        with psycopg.connect(self.database_url, row_factory=dict_row) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id, job_id, tenant_id, topic, correlation_id
                      FROM jobs.outbox
                     WHERE published_at IS NULL
                     ORDER BY id
                     FOR UPDATE SKIP LOCKED
                     LIMIT %s
                    """,
                    (batch_size,),
                )
                rows = cursor.fetchall()

                for row in rows:
                    # Deliberately at-least-once: publish, then mark. A crash
                    # here repeats a delivery, which the worker absorbs.
                    self.redis.rpush(QUEUE_KEY, row["job_id"])
                    cursor.execute(
                        "UPDATE jobs.outbox SET published_at = now() WHERE id = %s",
                        (row["id"],),
                    )
                    published += 1

                connection.commit()

        if published:
            logger.info("relay published %d event(s)", published)
        return published

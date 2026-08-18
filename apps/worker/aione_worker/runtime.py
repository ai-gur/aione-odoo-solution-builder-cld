"""Durable job worker.

The contract this implements (ADR-005):

- PostgreSQL holds authoritative state. Redis carries a nudge, nothing more.
- Claiming takes a lease, not a lock. A worker that dies stops renewing, and
  the job returns to the pool when the lease expires — no supervisor has to
  notice the death.
- A repeated delivery reuses the same idempotency identity, so a duplicate
  produces no second material effect.
- Queue acknowledgement is never proof of business completion. The job row is.

The worker exposes `tick()` — claim and run at most one job — rather than only
a run loop, so tests can drive it deterministically instead of sleeping and
hoping.
"""

from __future__ import annotations

import json
import logging
import os
import socket
import time
from dataclasses import dataclass
from typing import Any, Callable

import psycopg
from psycopg.rows import dict_row

logger = logging.getLogger("aione.worker")

LEASE_SECONDS = 30
QUEUE_KEY = "aione:jobs"

Handler = Callable[["JobContext"], dict[str, Any]]
_HANDLERS: dict[str, Handler] = {}


def handler(job_type: str) -> Callable[[Handler], Handler]:
    def register(function: Handler) -> Handler:
        _HANDLERS[job_type] = function
        return function

    return register


@dataclass(frozen=True)
class JobContext:
    job_id: str
    tenant_id: str
    job_type: str
    payload: dict[str, Any]
    idempotency_key: str
    correlation_id: str
    attempts: int
    cursor: psycopg.Cursor


class TransientError(Exception):
    """Retryable. Anything else is treated as needing a person."""


@handler("health.echo")
def health_echo(context: JobContext) -> dict[str, Any]:
    """The Increment 0 example job.

    Its material effect is one row keyed by the job's idempotency key. A second
    delivery hits the unique constraint and changes nothing, which is what
    "safely redeliverable" has to mean in practice — not "the handler runs
    twice and we hope it is harmless".
    """
    context.cursor.execute(
        """
        INSERT INTO jobs.job_effects (tenant_id, job_id, effect_key, detail)
        VALUES (%s, %s, %s, %s::jsonb)
        ON CONFLICT (tenant_id, effect_key) DO NOTHING
        """,
        (
            context.tenant_id,
            context.job_id,
            context.idempotency_key,
            json.dumps({"echo": context.payload.get("message", ""), "attempt": context.attempts}),
        ),
    )
    return {"applied_rows": context.cursor.rowcount}


class Worker:
    def __init__(self, database_url: str, *, name: str | None = None) -> None:
        self.database_url = database_url
        self.name = name or f"{socket.gethostname()}:{os.getpid()}"

    def _connect(self) -> psycopg.Connection:
        return psycopg.connect(self.database_url, row_factory=dict_row, autocommit=False)

    def claim(self, cursor: psycopg.Cursor) -> dict[str, Any] | None:
        """Take the next claimable job.

        `FOR UPDATE SKIP LOCKED` lets several workers claim concurrently
        without blocking each other. Jobs whose lease has expired are claimable
        again, which is how work recovers from a worker that stopped.
        """
        cursor.execute(
            """
            UPDATE jobs.jobs
               SET state = 'running',
                   attempts = attempts + 1,
                   lease_owner = %s,
                   lease_expires_at = now() + make_interval(secs => %s),
                   heartbeat_at = now(),
                   updated_at = now()
             WHERE id = (
                   SELECT id FROM jobs.jobs
                    WHERE (state = 'pending'
                           OR (state = 'running' AND lease_expires_at < now()))
                      AND attempts < max_attempts
                    ORDER BY created_at
                    FOR UPDATE SKIP LOCKED
                    LIMIT 1
             )
         RETURNING id, tenant_id, job_type, payload, idempotency_key,
                   correlation_id, attempts
            """,
            (self.name, LEASE_SECONDS),
        )
        return cursor.fetchone()

    def heartbeat(self, cursor: psycopg.Cursor, job_id: str) -> None:
        cursor.execute(
            """
            UPDATE jobs.jobs
               SET heartbeat_at = now(),
                   lease_expires_at = now() + make_interval(secs => %s)
             WHERE id = %s AND lease_owner = %s
            """,
            (LEASE_SECONDS, job_id, self.name),
        )

    def tick(self) -> str | None:
        """Claim and run at most one job. Returns the job id, or None."""
        with self._connect() as connection:
            with connection.cursor() as cursor:
                job = self.claim(cursor)
                if job is None:
                    connection.rollback()
                    return None

                job_id = job["id"]
                function = _HANDLERS.get(job["job_type"])
                if function is None:
                    connection.rollback()
                    self._fail(job_id, f"no handler for {job['job_type']}", blocked=True)
                    return job_id

                context = JobContext(
                    job_id=job_id,
                    tenant_id=job["tenant_id"],
                    job_type=job["job_type"],
                    payload=job["payload"] or {},
                    idempotency_key=job["idempotency_key"],
                    correlation_id=job["correlation_id"],
                    attempts=job["attempts"],
                    cursor=cursor,
                )

                try:
                    result = function(context)
                except TransientError as error:
                    connection.rollback()
                    self._fail(job_id, f"transient: {error}", blocked=False)
                    return job_id
                except Exception as error:  # noqa: BLE001
                    connection.rollback()
                    self._fail(job_id, f"{type(error).__name__}: {error}", blocked=True)
                    return job_id

                # The handler's effect and the completion of the job commit
                # together. A crash between them would otherwise leave work
                # done but unrecorded, and the retry would repeat it.
                cursor.execute(
                    """
                    UPDATE jobs.jobs
                       SET state = 'succeeded',
                           lease_owner = NULL,
                           lease_expires_at = NULL,
                           last_error = NULL,
                           completed_at = now(),
                           updated_at = now()
                     WHERE id = %s
                    """,
                    (job_id,),
                )
                connection.commit()
                logger.info(
                    "job completed id=%s type=%s correlation=%s result=%s",
                    job_id, job["job_type"], job["correlation_id"], result,
                )
                return job_id

    def _fail(self, job_id: str, message: str, *, blocked: bool) -> None:
        """Record failure in its own transaction, so it survives the rollback
        of the work that failed."""
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE jobs.jobs
                       SET state = CASE
                                     WHEN %s THEN 'blocked'
                                     WHEN attempts >= max_attempts THEN 'failed'
                                     ELSE 'pending'
                                   END,
                           lease_owner = NULL,
                           lease_expires_at = NULL,
                           last_error = %s,
                           updated_at = now()
                     WHERE id = %s
                    """,
                    (blocked, message[:2000], job_id),
                )
            connection.commit()
        logger.warning("job failed id=%s blocked=%s error=%s", job_id, blocked, message)

    def run(self, *, idle_sleep: float = 1.0) -> None:  # pragma: no cover - loop
        logger.info("worker %s started", self.name)
        while True:
            if self.tick() is None:
                time.sleep(idle_sleep)

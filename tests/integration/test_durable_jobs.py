"""Durable job path (Increment 0, story I0-06).

Acceptance tests 9, 10 and 11 from the packet: an outbox event reaches a
worker, duplicate delivery does not duplicate the effect, and an interrupted
worker leaves a recoverable job.

These use the real Postgres and Redis. The point of the exercise is what
happens between them under failure, and a fake would only prove the fake
behaves as written.

Requires: make stack-up && make db-migrate
"""

from __future__ import annotations

import pathlib
import secrets
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "apps" / "worker"))

import redis  # noqa: E402

from aione_worker.relay import QUEUE_KEY, Relay  # noqa: E402
from aione_worker.runtime import Worker  # noqa: E402
import os  # noqa: E402

os.environ.setdefault("AIONE_DATABASE", "aione_control_test")

from scripts.db import psql  # noqa: E402

import os
WORKER_DSN = os.environ.get(
    "DATABASE_URL_WORKER",
    "postgresql://app_worker:local_dev_only@localhost:55432/aione_control_test",
)
REDIS_URL = "redis://localhost:56379/0"
TENANT = "ten_01JQZX3K8YB2N4V6R8T0W2C5J1"


def new_job_id() -> str:
    return "job_" + secrets.token_hex(13).upper()


def submit(job_id: str, idempotency_key: str, *, message: str = "hello") -> None:
    """Write a job and its outbox event in one transaction, as the API does."""
    psql(
        f"""
        BEGIN;
        INSERT INTO jobs.jobs (id, tenant_id, job_type, payload, idempotency_key, correlation_id)
        VALUES ('{job_id}', '{TENANT}', 'health.echo',
                '{{"message": "{message}"}}'::jsonb, '{idempotency_key}', 'cor_{job_id}');
        INSERT INTO jobs.outbox (tenant_id, job_id, topic, correlation_id)
        VALUES ('{TENANT}', '{job_id}', 'job.submitted', 'cor_{job_id}');
        COMMIT;
        """
    )


class DurableJobTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        psql(
            f"""
            DELETE FROM jobs.job_effects WHERE tenant_id = '{TENANT}';
            DELETE FROM jobs.outbox WHERE tenant_id = '{TENANT}';
            DELETE FROM jobs.jobs WHERE tenant_id = '{TENANT}';
            DELETE FROM app.tenants WHERE id = '{TENANT}';
            INSERT INTO app.tenants (id, name) VALUES ('{TENANT}', 'Jobs Test Tenant');
            """
        )
        cls.redis = redis.from_url(REDIS_URL)
        cls.redis.delete(QUEUE_KEY)
        cls.relay = Relay(WORKER_DSN, cls.redis)
        cls.worker = Worker(WORKER_DSN, name="test-worker-1")

    def setUp(self) -> None:
        # A worker claims the oldest claimable job in the whole queue, not the
        # one a given test just submitted — correct behaviour, but it makes
        # assertions about "the" job meaningless unless the queue starts empty.
        # These tests own the local queue for their duration.
        psql(
            "DELETE FROM jobs.job_effects; DELETE FROM jobs.outbox; DELETE FROM jobs.jobs;"
        )
        self.redis.delete(QUEUE_KEY)

    @staticmethod
    def state_of(job_id: str) -> str:
        return psql(f"SELECT state FROM jobs.jobs WHERE id = '{job_id}';")

    @staticmethod
    def effect_count(job_id: str) -> int:
        return int(psql(f"SELECT count(*) FROM jobs.job_effects WHERE job_id = '{job_id}';"))

    @staticmethod
    def attempts(job_id: str) -> int:
        return int(psql(f"SELECT attempts FROM jobs.jobs WHERE id = '{job_id}';"))


class TestOutboxReachesWorker(DurableJobTestCase):
    def test_outbox_event_is_published_and_the_job_runs(self) -> None:
        job_id = new_job_id()
        submit(job_id, f"key_{job_id}")

        published = self.relay.publish_pending()
        self.assertGreaterEqual(published, 1)
        self.assertIn(job_id.encode(), self.redis.lrange(QUEUE_KEY, 0, -1))

        self.assertEqual(self.worker.tick(), job_id)
        self.assertEqual(self.state_of(job_id), "succeeded")
        self.assertEqual(self.effect_count(job_id), 1)

    def test_outbox_rows_are_marked_published_once(self) -> None:
        job_id = new_job_id()
        submit(job_id, f"key_{job_id}")
        self.relay.publish_pending()
        # A second pass has nothing new to publish for this job.
        remaining = psql(
            f"SELECT count(*) FROM jobs.outbox WHERE job_id = '{job_id}' AND published_at IS NULL;"
        )
        self.assertEqual(remaining, "0")
        self.worker.tick()


class TestDuplicateDelivery(DurableJobTestCase):
    """Acceptance test 10: duplicate delivery does not duplicate the effect."""

    def test_second_delivery_produces_no_second_effect(self) -> None:
        job_id = new_job_id()
        key = f"key_{job_id}"
        submit(job_id, key)
        self.relay.publish_pending()

        self.assertEqual(self.worker.tick(), job_id)
        self.assertEqual(self.effect_count(job_id), 1)

        # The relay is at-least-once by design, so simulate the duplicate it is
        # allowed to produce: push the same job onto the queue and force the
        # job back to claimable, as an expired lease would.
        self.redis.rpush(QUEUE_KEY, job_id)
        psql(f"UPDATE jobs.jobs SET state = 'pending', attempts = 0 WHERE id = '{job_id}';")

        self.assertEqual(self.worker.tick(), job_id)
        self.assertEqual(
            self.effect_count(job_id), 1, "a redelivered job created a second effect"
        )
        self.assertEqual(self.state_of(job_id), "succeeded")

    def test_resubmitting_the_same_idempotency_key_is_rejected_by_the_database(self) -> None:
        job_id = new_job_id()
        key = f"key_{job_id}"
        submit(job_id, key)
        from scripts.db import run_psql

        result = run_psql(
            f"""
            INSERT INTO jobs.jobs (id, tenant_id, job_type, idempotency_key, correlation_id)
            VALUES ('{new_job_id()}', '{TENANT}', 'health.echo', '{key}', 'cor_dupe');
            """
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("duplicate key", (result.stderr + result.stdout).lower())


class TestInterruptedWorker(DurableJobTestCase):
    """Acceptance test 11: worker interruption produces a recoverable state."""

    def test_expired_lease_makes_the_job_claimable_again(self) -> None:
        job_id = new_job_id()
        submit(job_id, f"key_{job_id}")

        # Claim without completing, as a worker that died mid-flight would.
        import psycopg

        with psycopg.connect(WORKER_DSN) as connection:
            with connection.cursor() as cursor:
                claimed = Worker(WORKER_DSN, name="doomed-worker").claim(cursor)
                self.assertIsNotNone(claimed)
                connection.commit()

        self.assertEqual(self.state_of(job_id), "running")

        # Nothing has to notice the death: the lease simply stops being renewed.
        psql(
            f"UPDATE jobs.jobs SET lease_expires_at = now() - interval '1 minute' "
            f"WHERE id = '{job_id}';"
        )

        self.assertEqual(self.worker.tick(), job_id)
        self.assertEqual(self.state_of(job_id), "succeeded")
        self.assertEqual(self.effect_count(job_id), 1)
        self.assertEqual(self.attempts(job_id), 2, "the recovery attempt should be recorded")

    def test_a_live_lease_is_not_stolen(self) -> None:
        job_id = new_job_id()
        submit(job_id, f"key_{job_id}")

        import psycopg

        with psycopg.connect(WORKER_DSN) as connection:
            with connection.cursor() as cursor:
                Worker(WORKER_DSN, name="holder").claim(cursor)
                connection.commit()

        # A second worker must not take work that is still leased.
        other = Worker(WORKER_DSN, name="test-worker-2")
        self.assertIsNone(other.tick())
        self.assertEqual(self.state_of(job_id), "running")


class TestQueueIsNotAuthority(DurableJobTestCase):
    """ADR-005: queue acknowledgement is not proof of business completion."""

    def test_a_queue_message_without_a_job_row_does_nothing(self) -> None:
        self.redis.rpush(QUEUE_KEY, "job_DOES_NOT_EXIST")
        # The worker reads authoritative state from the database, so a stray
        # message cannot invent work.
        self.assertIsNone(self.worker.tick())

    def test_losing_the_queue_message_does_not_lose_the_job(self) -> None:
        job_id = new_job_id()
        submit(job_id, f"key_{job_id}")
        self.redis.delete(QUEUE_KEY)  # the queue forgets everything

        self.assertEqual(self.worker.tick(), job_id)
        self.assertEqual(self.state_of(job_id), "succeeded")


if __name__ == "__main__":
    unittest.main(verbosity=2)

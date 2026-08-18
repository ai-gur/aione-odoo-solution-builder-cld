"""Domain API tests (Increment 0, stories I0-04, I0-05, I0-09).

These run against the real local database rather than a mock. The behaviour
being tested is the interaction between application checks and database
policies, and a mock would assert only that the code calls itself as written.

Requires: make stack-up && make db-migrate
"""

from __future__ import annotations

import os
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

os.environ.setdefault(
    "DATABASE_URL_API",
    "postgresql://app_api:local_dev_only@localhost:55432/aione_control_test",
)
os.environ.setdefault("APP_ENVIRONMENT", "local")
os.environ.setdefault("AUTH_MODE", "dev")
os.environ.setdefault("AIONE_DATABASE", "aione_control_test")

from fastapi.testclient import TestClient  # noqa: E402

from aione_domain import db  # noqa: E402
from aione_domain.config import ConfigurationError, load_settings, redact_dsn  # noqa: E402
from aione_domain.main import app  # noqa: E402

TENANT_A = "ten_01JQZX3K8YB2N4V6R8T0W2C5A1"
TENANT_B = "ten_01JQZX3K8YB2N4V6R8T0W2C5B2"
SUBJECT_A = "auth|test-a"
SUBJECT_B = "auth|test-b"


def seed() -> None:
    """Seed through the migrator role: the API's own role cannot create
    tenants it is not yet a member of, which is the point."""
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))
    from scripts.db import psql

    psql(
        f"""
        DELETE FROM audit.events WHERE tenant_id IN ('{TENANT_A}', '{TENANT_B}');
        DELETE FROM app.memberships WHERE tenant_id IN ('{TENANT_A}', '{TENANT_B}');
        DELETE FROM app.users WHERE auth_subject IN ('{SUBJECT_A}', '{SUBJECT_B}');
        DELETE FROM app.tenants WHERE id IN ('{TENANT_A}', '{TENANT_B}');

        INSERT INTO app.tenants (id, name) VALUES
          ('{TENANT_A}', 'AIOne Test Tenant A'),
          ('{TENANT_B}', 'AIOne Test Tenant B');
        INSERT INTO app.users (id, auth_subject, email, display_name) VALUES
          ('usr_01JQZX3K8YB2N4V6R8T0W2C5A3', '{SUBJECT_A}', 'a@example.test', 'Tester A'),
          ('usr_01JQZX3K8YB2N4V6R8T0W2C5B4', '{SUBJECT_B}', 'b@example.test', 'Tester B');
        INSERT INTO app.memberships (id, tenant_id, user_id, role_key) VALUES
          ('mbr_01JQZX3K8YB2N4V6R8T0W2C5A5', '{TENANT_A}', 'usr_01JQZX3K8YB2N4V6R8T0W2C5A3', 'consultant'),
          ('mbr_01JQZX3K8YB2N4V6R8T0W2C5B6', '{TENANT_B}', 'usr_01JQZX3K8YB2N4V6R8T0W2C5B4', 'account_owner');
        INSERT INTO audit.events (id, tenant_id, action, correlation_id, outcome) VALUES
          ('evt_01JQZX3K8YB2N4V6R8T0W2C5A7', '{TENANT_A}', 'seed.tenant_a', 'cor_seed_a', 'succeeded'),
          ('evt_01JQZX3K8YB2N4V6R8T0W2C5B8', '{TENANT_B}', 'seed.tenant_b', 'cor_seed_b', 'succeeded');
        """
    )


class APITestCase(unittest.TestCase):
    client: TestClient

    @classmethod
    def setUpClass(cls) -> None:
        seed()
        cls.client = TestClient(app)
        cls.client.__enter__()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.client.__exit__(None, None, None)

    @staticmethod
    def as_user(subject: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {subject}"}


class TestHealth(APITestCase):
    def test_health_does_not_require_the_database(self) -> None:
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    def test_ready_reports_the_schema(self) -> None:
        response = self.client.get("/ready")
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["status"], "ready")

    def test_every_response_carries_a_correlation_id(self) -> None:
        response = self.client.get("/health")
        self.assertTrue(response.headers.get("X-Correlation-Id"))

    def test_supplied_correlation_id_is_preserved(self) -> None:
        response = self.client.get("/health", headers={"X-Correlation-Id": "cor_supplied"})
        self.assertEqual(response.headers["X-Correlation-Id"], "cor_supplied")


class TestIdentity(APITestCase):
    """I0-04: identity resolved server-side, never from a client-supplied
    tenant identifier."""

    def test_anonymous_is_refused(self) -> None:
        self.assertEqual(self.client.get("/v1/me").status_code, 401)

    def test_malformed_credential_is_refused(self) -> None:
        response = self.client.get("/v1/me", headers={"Authorization": "Basic zzz"})
        self.assertEqual(response.status_code, 401)

    def test_unknown_subject_is_refused(self) -> None:
        response = self.client.get("/v1/me", headers=self.as_user("auth|nobody"))
        self.assertEqual(response.status_code, 401)

    def test_memberships_are_resolved_from_the_database(self) -> None:
        response = self.client.get("/v1/me", headers=self.as_user(SUBJECT_A))
        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertEqual(body["email"], "a@example.test")
        self.assertEqual([m["tenantId"] for m in body["memberships"]], [TENANT_A])
        self.assertEqual(body["memberships"][0]["roleKey"], "consultant")

    def test_a_client_supplied_tenant_header_is_ignored(self) -> None:
        response = self.client.get(
            "/v1/me",
            headers={**self.as_user(SUBJECT_A), "X-Tenant-Id": TENANT_B},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [m["tenantId"] for m in response.json()["memberships"]],
            [TENANT_A],
            "membership must come from the database, not the request",
        )


class TestHebrewRoundTrip(APITestCase):
    """Hebrew is the primary product language, so a control database that
    silently mangles it is a product defect rather than an encoding detail.

    This exists because the first local stack came up SQL_ASCII: text columns
    returned bytes instead of str, and Hebrew would have survived only as long
    as nothing in the chain disagreed about encoding.
    """

    def test_hebrew_tenant_name_survives_the_round_trip(self) -> None:
        sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))
        from scripts.db import psql

        hebrew = "איי-ואן פתרונות אודו"
        psql(f"UPDATE app.tenants SET name = '{hebrew}' WHERE id = '{TENANT_A}';")

        response = self.client.get("/v1/me", headers=self.as_user(SUBJECT_A))
        self.assertEqual(response.status_code, 200, response.text)
        returned = response.json()["memberships"][0]["tenantName"]
        self.assertEqual(returned, hebrew)
        self.assertIsInstance(returned, str)


class TestCrossTenantAccess(APITestCase):
    """I0-05 at the API layer. The database proof already exists; this proves
    the service does not hand out what the policies would refuse."""

    def test_member_reads_own_tenant_events(self) -> None:
        response = self.client.get(
            f"/v1/tenants/{TENANT_A}/audit-events", headers=self.as_user(SUBJECT_A)
        )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertTrue(response.json()["events"])

    def test_non_member_is_forbidden(self) -> None:
        response = self.client.get(
            f"/v1/tenants/{TENANT_B}/audit-events", headers=self.as_user(SUBJECT_A)
        )
        self.assertEqual(response.status_code, 403)

    def test_denial_is_recorded_against_the_tenant_that_was_reached_for(self) -> None:
        self.client.get(
            f"/v1/tenants/{TENANT_B}/audit-events",
            headers={**self.as_user(SUBJECT_A), "X-Correlation-Id": "cor_denial_probe"},
        )
        with db.transaction(tenant_id=TENANT_B) as cursor:
            cursor.execute(
                "SELECT action, outcome, actor_id FROM audit.events "
                "WHERE correlation_id = %s",
                ("cor_denial_probe",),
            )
            rows = cursor.fetchall()
        self.assertEqual(len(rows), 1, "a denied access attempt must be auditable")
        self.assertEqual(rows[0]["outcome"], "denied")
        self.assertEqual(rows[0]["actor_id"], "usr_01JQZX3K8YB2N4V6R8T0W2C5A3")

    def test_events_returned_are_only_the_tenants_own(self) -> None:
        response = self.client.get(
            f"/v1/tenants/{TENANT_A}/audit-events", headers=self.as_user(SUBJECT_A)
        )
        actions = {event["action"] for event in response.json()["events"]}
        self.assertIn("seed.tenant_a", actions)
        self.assertNotIn("seed.tenant_b", actions)


class TestConfiguration(unittest.TestCase):
    def test_dsn_is_redacted_for_logs(self) -> None:
        redacted = redact_dsn("postgresql://app_api:hunter2@localhost:55432/aione_control")
        self.assertNotIn("hunter2", redacted)
        self.assertIn("app_api", redacted)

    def test_dev_auth_is_refused_outside_local(self) -> None:
        original = os.environ.get("APP_ENVIRONMENT")
        os.environ["APP_ENVIRONMENT"] = "staging"
        try:
            with self.assertRaises(ConfigurationError) as raised:
                load_settings()
            self.assertIn("AUTH_MODE=dev", str(raised.exception))
        finally:
            if original is None:
                del os.environ["APP_ENVIRONMENT"]
            else:
                os.environ["APP_ENVIRONMENT"] = original

    def test_missing_setting_names_it_without_printing_a_value(self) -> None:
        original = os.environ.pop("DATABASE_URL_API")
        try:
            with self.assertRaises(ConfigurationError) as raised:
                load_settings()
            self.assertIn("DATABASE_URL_API", str(raised.exception))
        finally:
            os.environ["DATABASE_URL_API"] = original


if __name__ == "__main__":
    unittest.main(verbosity=2)

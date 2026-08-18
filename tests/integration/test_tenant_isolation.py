"""Tenant isolation proof (Increment 0, story I0-05).

These tests connect as `app_api` — the role the domain API actually uses — and
not as the migrator or a superuser. That distinction is the whole point: a
policy test run as a superuser passes no matter what the policies say, because
superusers bypass row-level security entirely. Running as `app_api` is what
makes a failure here mean something.

Requires the local stack: `make stack-up && make db-migrate`.
"""

from __future__ import annotations

import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from scripts.db import psql, run_psql  # noqa: E402

API_USER = "app_api"
API_PASSWORD = "local_dev_only"

TENANT_A = "ten_01JQZX3K8YB2N4V6R8T0W2C5A1"
TENANT_B = "ten_01JQZX3K8YB2N4V6R8T0W2C5B2"
USER_A = "usr_01JQZX3K8YB2N4V6R8T0W2C5A3"
USER_B = "usr_01JQZX3K8YB2N4V6R8T0W2C5B4"

SEED = f"""
DELETE FROM audit.events WHERE tenant_id IN ('{TENANT_A}', '{TENANT_B}');
DELETE FROM app.memberships WHERE tenant_id IN ('{TENANT_A}', '{TENANT_B}');
DELETE FROM app.users WHERE id IN ('{USER_A}', '{USER_B}');
DELETE FROM app.tenants WHERE id IN ('{TENANT_A}', '{TENANT_B}');

INSERT INTO app.tenants (id, name) VALUES
  ('{TENANT_A}', 'AIOne Test Tenant A'),
  ('{TENANT_B}', 'AIOne Test Tenant B');

INSERT INTO app.users (id, auth_subject, email, display_name) VALUES
  ('{USER_A}', 'auth|test-a', 'a@example.test', 'Tester A'),
  ('{USER_B}', 'auth|test-b', 'b@example.test', 'Tester B');

INSERT INTO app.memberships (id, tenant_id, user_id, role_key) VALUES
  ('mbr_01JQZX3K8YB2N4V6R8T0W2C5A5', '{TENANT_A}', '{USER_A}', 'consultant'),
  ('mbr_01JQZX3K8YB2N4V6R8T0W2C5B6', '{TENANT_B}', '{USER_B}', 'consultant');

INSERT INTO audit.events (id, tenant_id, actor_id, actor_role, action, correlation_id, outcome) VALUES
  ('evt_01JQZX3K8YB2N4V6R8T0W2C5A7', '{TENANT_A}', '{USER_A}', 'consultant', 'membership.created', 'cor_a', 'succeeded'),
  ('evt_01JQZX3K8YB2N4V6R8T0W2C5B8', '{TENANT_B}', '{USER_B}', 'consultant', 'membership.created', 'cor_b', 'succeeded');
"""


def as_api(sql: str):
    return run_psql(sql, user=API_USER, password=API_PASSWORD)


def in_tenant(tenant_id: str, sql: str):
    """Run SQL inside one transaction with tenant context, as the API role.

    SET LOCAL, never a session-level SET: connection pooling reuses sessions
    across requests, and a session-level setting would leak one request's
    tenant into the next one.
    """
    return as_api(
        f"BEGIN; SET LOCAL app.tenant_id = '{tenant_id}'; {sql} COMMIT;"
    )


class TestRoleConfiguration(unittest.TestCase):
    """If these fail, every policy below is decorative."""

    def test_api_role_is_not_superuser_and_cannot_bypass_rls(self) -> None:
        row = psql(
            "SELECT rolsuper, rolbypassrls FROM pg_roles WHERE rolname = 'app_api';"
        )
        self.assertEqual(row, "f|f", "app_api must be neither superuser nor BYPASSRLS")

    def test_rls_is_enabled_and_forced_on_tenant_scoped_tables(self) -> None:
        rows = psql(
            "SELECT n.nspname || '.' || c.relname || '=' "
            "|| c.relrowsecurity::text || ',' || c.relforcerowsecurity::text "
            "FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace "
            "WHERE n.nspname IN ('app', 'audit') AND c.relkind = 'r' ORDER BY 1;"
        )
        for table in ("app.memberships=true,true", "app.tenants=true,true", "audit.events=true,true"):
            self.assertIn(table, rows, f"expected RLS enabled and forced: {rows}")


class TestTenantIsolation(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        psql(SEED)

    def test_reads_are_confined_to_the_tenant_in_context(self) -> None:
        result = in_tenant(TENANT_A, "SELECT tenant_id FROM app.memberships;")
        self.assertIn(TENANT_A, result.stdout)
        self.assertNotIn(TENANT_B, result.stdout)

    def test_audit_reads_are_confined_to_the_tenant_in_context(self) -> None:
        result = in_tenant(TENANT_A, "SELECT tenant_id FROM audit.events;")
        self.assertIn(TENANT_A, result.stdout)
        self.assertNotIn(TENANT_B, result.stdout)

    def test_without_context_nothing_is_visible(self) -> None:
        """Fail closed: a request that forgets to set context reads nothing."""
        result = as_api("SELECT count(*) FROM app.memberships;")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "0")

    def test_cannot_write_a_row_belonging_to_another_tenant(self) -> None:
        result = in_tenant(
            TENANT_A,
            "INSERT INTO app.memberships (id, tenant_id, user_id, role_key) VALUES "
            f"('mbr_01JQZX3K8YB2N4V6R8T0W2C5C9', '{TENANT_B}', '{USER_B}', 'consultant');",
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("row-level security", (result.stderr + result.stdout).lower())

    def test_cannot_update_another_tenants_row(self) -> None:
        result = in_tenant(
            TENANT_A,
            f"UPDATE app.memberships SET role_key = 'platform_administrator' "
            f"WHERE tenant_id = '{TENANT_B}';",
        )
        # The update is not refused; the row is simply not visible to it.
        self.assertEqual(result.returncode, 0)
        after = psql(
            f"SELECT role_key FROM app.memberships WHERE tenant_id = '{TENANT_B}';"
        )
        self.assertEqual(after, "consultant", "another tenant's row was modified")

    def test_switching_context_switches_visibility(self) -> None:
        result = in_tenant(TENANT_B, "SELECT tenant_id FROM app.memberships;")
        self.assertIn(TENANT_B, result.stdout)
        self.assertNotIn(TENANT_A, result.stdout)

    def test_context_does_not_survive_the_transaction(self) -> None:
        """SET LOCAL must not leak into the next transaction on the same
        connection, which is how a pooled session would cross tenants."""
        result = as_api(
            f"BEGIN; SET LOCAL app.tenant_id = '{TENANT_A}'; "
            "SELECT count(*) FROM app.memberships; COMMIT; "
            "SELECT count(*) FROM app.memberships;"
        )
        # psql echoes command tags (BEGIN, SET, COMMIT); only the query results
        # are numeric.
        counts = [line.strip() for line in result.stdout.split() if line.strip().isdigit()]
        self.assertEqual(counts, ["1", "0"], "tenant context leaked past COMMIT")


class TestAuditIsAppendOnly(unittest.TestCase):
    """ADR-011: application users cannot update or delete audit events. Enforced
    by privilege, not by convention."""

    def test_api_role_cannot_update_audit_events(self) -> None:
        result = in_tenant(TENANT_A, "UPDATE audit.events SET outcome = 'failed';")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("permission denied", (result.stderr + result.stdout).lower())

    def test_api_role_cannot_delete_audit_events(self) -> None:
        result = in_tenant(TENANT_A, "DELETE FROM audit.events;")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("permission denied", (result.stderr + result.stdout).lower())

    def test_api_role_can_append(self) -> None:
        result = in_tenant(
            TENANT_A,
            "INSERT INTO audit.events (id, tenant_id, action, correlation_id, outcome) "
            f"VALUES ('evt_01JQZX3K8YB2N4V6R8T0W2C5D0', '{TENANT_A}', 'test.append', 'cor_a', 'succeeded');",
        )
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)

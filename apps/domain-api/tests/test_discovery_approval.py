"""The discovery approval gate (Constitution §11 gate 1, Discovery §16.4).

The first place the product refuses to proceed. What is tested here is that the
refusal is real: blocking open questions and unanswered required questions stop
approval, the approved version is immutable, and its digest is reproducible by
anyone holding the snapshot.
"""

from __future__ import annotations

import os
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))

os.environ.setdefault(
    "DATABASE_URL_API",
    "postgresql://app_api:local_dev_only@localhost:55432/aione_control_test",
)
os.environ.setdefault("APP_ENVIRONMENT", "local")
os.environ.setdefault("AUTH_MODE", "dev")
os.environ.setdefault("AIONE_DATABASE", "aione_control_test")

from aione_contracts import digest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from aione_domain.main import app  # noqa: E402
from scripts.db import psql, run_psql  # noqa: E402

TENANT = "ten_01JQZX3K8YB2N4V6R8T0W2C5G1"
LEAD = "auth|gate-lead"

SEED = f"""
DELETE FROM discovery.discovery_versions WHERE tenant_id = '{TENANT}';
DELETE FROM discovery.open_questions WHERE tenant_id = '{TENANT}';
DELETE FROM discovery.requirements WHERE tenant_id = '{TENANT}';
DELETE FROM discovery.business_facts WHERE tenant_id = '{TENANT}';
DELETE FROM discovery.answers WHERE tenant_id = '{TENANT}';
DELETE FROM discovery.interview_runs WHERE tenant_id = '{TENANT}';
DELETE FROM app.workspace_state_history WHERE tenant_id = '{TENANT}';
DELETE FROM app.solution_workspaces WHERE tenant_id = '{TENANT}';
DELETE FROM app.customer_organizations WHERE tenant_id = '{TENANT}';
DELETE FROM audit.events WHERE tenant_id = '{TENANT}';
DELETE FROM app.memberships WHERE tenant_id = '{TENANT}';
DELETE FROM app.users WHERE auth_subject = '{LEAD}' OR email = 'gate@aione.test';
DELETE FROM app.tenants WHERE id = '{TENANT}';

INSERT INTO app.tenants (id, name) VALUES ('{TENANT}', 'AIOne Gate');
INSERT INTO app.users (id, auth_subject, email, display_name) VALUES
  ('usr_GATELEAD00000000000001', '{LEAD}', 'gate@aione.test', 'Gate Lead');
INSERT INTO app.memberships (id, tenant_id, user_id, role_key) VALUES
  ('mbr_GATE000000000000000001', '{TENANT}', 'usr_GATELEAD00000000000001', 'account_owner'),
  ('mbr_GATE000000000000000002', '{TENANT}', 'usr_GATELEAD00000000000001', 'consultant');
"""

# Every required Quick Start question, with answers that raise no blocking item.
CLEAN_ANSWERS = {
    "QS-01": "מפיצים ציוד חשמלי לחנויות.",
    "QS-02": ["physical_products"],
    "QS-03": ["businesses", "sales_team"],
    "QS-04": {"employees": "18", "expected_users": "12", "monthly_transactions": "900"},
    "QS-05": {"companies": "1", "countries": "1", "branches": "1", "warehouses": "2"},
    "QS-06": ["crm", "sales", "purchase", "inventory"],
    "QS-07": ["spreadsheets"],
    "QS-08": ["multiple_warehouses"],
    # External accounting raises no finance confirmation item.
    "QS-11": "external",
    "QS-14": ["איטיות בהפקת הזמנות", "חוסר נראות מלאי", "טעויות תמחור"],
    "QS-15": "קיצור זמן הפקת הזמנה בחצי.",
    "QS-16": ["discounts"],
    # No historical or financial migration, so no data qualification item.
    "QS-17": ["customers", "products"],
}


class GateTestCase(unittest.TestCase):
    client: TestClient
    workspace_id: str
    run_id: str

    @classmethod
    def setUpClass(cls) -> None:
        psql(SEED)
        cls.client = TestClient(app)
        cls.client.__enter__()

        customer = cls.client.post(
            f"/v1/tenants/{TENANT}/customers", headers=cls.auth(),
            json={"legalName": "שער בדיקה בע\"מ", "customerCode": "C0900"},
        ).json()["customer"]
        cls.workspace_id = cls.client.post(
            f"/v1/tenants/{TENANT}/workspaces", headers=cls.auth(),
            json={"customerId": customer["id"], "name": "ERP"},
        ).json()["workspace"]["id"]

    @classmethod
    def tearDownClass(cls) -> None:
        cls.client.__exit__(None, None, None)

    @classmethod
    def auth(cls) -> dict[str, str]:
        return {"Authorization": f"Bearer {LEAD}"}

    def setUp(self) -> None:
        # A fresh run per test: approval is terminal, so tests cannot share one.
        psql(
            f"DELETE FROM discovery.discovery_versions WHERE tenant_id = '{TENANT}';"
            f"DELETE FROM discovery.open_questions WHERE tenant_id = '{TENANT}';"
            f"DELETE FROM discovery.requirements WHERE tenant_id = '{TENANT}';"
            f"DELETE FROM discovery.business_facts WHERE tenant_id = '{TENANT}';"
            f"DELETE FROM discovery.answers WHERE tenant_id = '{TENANT}';"
            f"DELETE FROM discovery.interview_runs WHERE tenant_id = '{TENANT}';"
        )
        self.run_id = self.client.post(
            f"/v1/tenants/{TENANT}/workspaces/{self.workspace_id}/interviews",
            headers=self.auth(), json={"mode": "quick_start"},
        ).json()["run"]["id"]

    def answer(self, key: str, value) -> None:
        response = self.client.post(
            f"/v1/tenants/{TENANT}/interviews/{self.run_id}/answers",
            headers=self.auth(), json={"questionKey": key, "value": value},
        )
        self.assertEqual(response.status_code, 200, response.text)

    def answer_all(self, overrides: dict | None = None) -> None:
        for key, value in {**CLEAN_ANSWERS, **(overrides or {})}.items():
            self.answer(key, value)
        self.client.post(
            f"/v1/tenants/{TENANT}/interviews/{self.run_id}/normalise", headers=self.auth()
        )

    def readiness(self) -> dict:
        return self.client.get(
            f"/v1/tenants/{TENANT}/interviews/{self.run_id}/readiness", headers=self.auth()
        ).json()

    def approve(self):
        return self.client.post(
            f"/v1/tenants/{TENANT}/interviews/{self.run_id}/approve", headers=self.auth()
        )


class TestGateRefusals(GateTestCase):
    def test_an_empty_interview_cannot_be_approved(self) -> None:
        response = self.approve()
        self.assertEqual(response.status_code, 409)
        reasons = {item["reason"] for item in response.json()["detail"]["reasons"]}
        self.assertIn("outstanding_required_questions", reasons)

    def test_every_blocker_is_reported_at_once(self) -> None:
        """A gate that reveals one blocker at a time turns review into a queue
        of round trips."""
        self.answer("QS-11", "full_accounting")
        self.client.post(
            f"/v1/tenants/{TENANT}/interviews/{self.run_id}/normalise", headers=self.auth()
        )
        reasons = {item["reason"] for item in self.approve().json()["detail"]["reasons"]}
        self.assertIn("outstanding_required_questions", reasons)
        self.assertIn("blocking_open_questions", reasons)

    def test_a_blocking_open_question_alone_prevents_approval(self) -> None:
        # Everything answered, but full accounting demands a finance owner's
        # confirmation before discovery can be approved.
        self.answer_all({"QS-11": "full_accounting"})
        state = self.readiness()
        self.assertFalse(state["ready"])

        response = self.approve()
        self.assertEqual(response.status_code, 409)
        reasons = {item["reason"] for item in response.json()["detail"]["reasons"]}
        self.assertEqual(reasons, {"blocking_open_questions"})

    def test_refusal_is_audited(self) -> None:
        self.approve()
        denied = psql(
            "SELECT count(*) FROM audit.events WHERE tenant_id = "
            f"'{TENANT}' AND action = 'discovery.approve' AND outcome = 'denied';"
        )
        self.assertGreaterEqual(int(denied), 1)


class TestApproval(GateTestCase):
    def test_a_complete_interview_can_be_approved(self) -> None:
        self.answer_all()
        state = self.readiness()
        self.assertTrue(state["ready"], state["reasons"])

        response = self.approve()
        self.assertEqual(response.status_code, 201, response.text)
        version = response.json()["version"]
        self.assertEqual(version["version"], 1)
        self.assertRegex(version["content_digest"], r"^sha256:[0-9a-f]{64}$")

    def test_the_digest_is_reproducible_from_the_snapshot(self) -> None:
        """Anyone holding the snapshot can recompute the hash, in either
        language, and confirm nothing changed (ADR-015)."""
        self.answer_all()
        stored = self.approve().json()["version"]["content_digest"]

        content = psql(
            "SELECT content::text FROM discovery.discovery_versions "
            f"WHERE run_id = '{self.run_id}';"
        )
        import json

        self.assertEqual(digest(json.loads(content)), stored)

    def test_an_approved_version_cannot_be_edited_by_the_api_role(self) -> None:
        self.answer_all()
        self.approve()
        result = run_psql(
            "UPDATE discovery.discovery_versions SET content_digest = 'sha256:0';",
            user="app_api", password="local_dev_only",
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("permission denied", (result.stderr + result.stdout).lower())

    def test_approving_unchanged_discovery_creates_no_second_version(self) -> None:
        """A version that records no change is noise in the history."""
        self.answer_all()
        self.assertEqual(self.approve().status_code, 201)
        second = self.approve()
        self.assertEqual(second.status_code, 409)
        self.assertIn("nothing has changed", second.json()["detail"]["error"])

    def test_a_corrected_answer_can_be_approved_as_a_new_version(self) -> None:
        """This is how a correction reaches the Blueprint Engine: a new
        version, never an edit of the approved one."""
        self.answer_all()
        first = self.approve().json()["version"]

        self.answer("QS-16", ["discounts", "purchases", "refunds"])
        self.client.post(
            f"/v1/tenants/{TENANT}/interviews/{self.run_id}/normalise", headers=self.auth()
        )

        second = self.approve()
        self.assertEqual(second.status_code, 201, second.text)
        self.assertEqual(second.json()["version"]["version"], first["version"] + 1)
        self.assertNotEqual(second.json()["version"]["content_digest"], first["content_digest"])

    def test_the_snapshot_carries_answers_and_conclusions(self) -> None:
        self.answer_all()
        self.approve()
        import json

        content = json.loads(
            psql(
                "SELECT content::text FROM discovery.discovery_versions "
                f"WHERE run_id = '{self.run_id}';"
            )
        )
        self.assertEqual(content["kind"], "DiscoveryPackage")
        self.assertTrue(content["answers"])
        self.assertTrue(content["requirements"])
        # The answers are the customer's words, not the normalised form.
        first = next(a for a in content["answers"] if a["questionKey"] == "QS-01")
        self.assertEqual(first["value"], CLEAN_ANSWERS["QS-01"])

    def test_the_version_is_listed_for_the_workspace(self) -> None:
        self.answer_all()
        self.approve()
        versions = self.client.get(
            f"/v1/tenants/{TENANT}/workspaces/{self.workspace_id}/discovery-versions",
            headers=self.auth(),
        ).json()["versions"]
        self.assertEqual(len(versions), 1)
        self.assertEqual(versions[0]["approved_role"], "consultant")


if __name__ == "__main__":
    unittest.main(verbosity=2)

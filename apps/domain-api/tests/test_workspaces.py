"""Customers, workspaces and authority (Increment 1).

The behaviour under test is the three-layer check from ADR-014: role resolved
from the database, authority from the role, and scope from the tenant. Each
layer is tested where it can actually fail, and denials are checked for their
audit trail rather than only their status code.
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

from fastapi.testclient import TestClient  # noqa: E402

from aione_domain.main import app  # noqa: E402
from scripts.db import psql  # noqa: E402

TENANT = "ten_01JQZX3K8YB2N4V6R8T0W2C5W1"
OTHER_TENANT = "ten_01JQZX3K8YB2N4V6R8T0W2C5W2"

MANAGER = "auth|wsp-manager"       # account_owner
LEAD = "auth|wsp-lead"             # solution_owner
CONSULTANT = "auth|wsp-consultant" # consultant
OUTSIDER = "auth|wsp-outsider"     # member of the other tenant only

SEED = f"""
DELETE FROM app.workspace_state_history WHERE tenant_id IN ('{TENANT}', '{OTHER_TENANT}');
DELETE FROM app.workspace_members WHERE tenant_id IN ('{TENANT}', '{OTHER_TENANT}');
DELETE FROM app.solution_workspaces WHERE tenant_id IN ('{TENANT}', '{OTHER_TENANT}');
DELETE FROM app.customer_organizations WHERE tenant_id IN ('{TENANT}', '{OTHER_TENANT}');
DELETE FROM audit.events WHERE tenant_id IN ('{TENANT}', '{OTHER_TENANT}');
DELETE FROM app.memberships WHERE tenant_id IN ('{TENANT}', '{OTHER_TENANT}');
DELETE FROM app.users WHERE auth_subject IN
  ('{MANAGER}', '{LEAD}', '{CONSULTANT}', '{OUTSIDER}');
DELETE FROM app.tenants WHERE id IN ('{TENANT}', '{OTHER_TENANT}');

INSERT INTO app.tenants (id, name) VALUES
  ('{TENANT}', 'AIOne'), ('{OTHER_TENANT}', 'Another Partner');

INSERT INTO app.users (id, auth_subject, email, display_name) VALUES
  ('usr_WSPMANAGER00000000000001', '{MANAGER}', 'manager@aione.test', 'Account Manager'),
  ('usr_WSPLEAD0000000000000002', '{LEAD}', 'lead@aione.test', 'Team Lead'),
  ('usr_WSPCONSULT000000000003', '{CONSULTANT}', 'consultant@aione.test', 'Consultant'),
  ('usr_WSPOUTSIDER00000000004', '{OUTSIDER}', 'outsider@other.test', 'Outsider');

INSERT INTO app.memberships (id, tenant_id, user_id, role_key) VALUES
  ('mbr_WSP0000000000000000001', '{TENANT}', 'usr_WSPMANAGER00000000000001', 'account_owner'),
  ('mbr_WSP0000000000000000002', '{TENANT}', 'usr_WSPLEAD0000000000000002', 'solution_owner'),
  ('mbr_WSP0000000000000000003', '{TENANT}', 'usr_WSPCONSULT000000000003', 'consultant'),
  ('mbr_WSP0000000000000000004', '{OTHER_TENANT}', 'usr_WSPOUTSIDER00000000004', 'account_owner');
"""


class WorkspaceTestCase(unittest.TestCase):
    client: TestClient

    @classmethod
    def setUpClass(cls) -> None:
        psql(SEED)
        cls.client = TestClient(app)
        cls.client.__enter__()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.client.__exit__(None, None, None)

    @staticmethod
    def auth(subject: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {subject}"}

    def create_customer(self, code: str, name: str = "לקוח בדיקה בע\"מ") -> str:
        response = self.client.post(
            f"/v1/tenants/{TENANT}/customers",
            headers=self.auth(MANAGER),
            json={"legalName": name, "customerCode": code},
        )
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()["customer"]["id"]

    def create_workspace(self, customer_id: str, name: str) -> str:
        response = self.client.post(
            f"/v1/tenants/{TENANT}/workspaces",
            headers=self.auth(LEAD),
            json={"customerId": customer_id, "name": name, "discoveryMode": "quick_start"},
        )
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()["workspace"]["id"]


class TestCustomers(WorkspaceTestCase):
    def test_account_manager_can_create_a_customer(self) -> None:
        customer_id = self.create_customer("C0101")
        self.assertTrue(customer_id.startswith("cus_"))

    def test_hebrew_legal_name_round_trips(self) -> None:
        self.create_customer("C0102", "מפיצי הצפון בע\"מ")
        response = self.client.get(
            f"/v1/tenants/{TENANT}/customers", headers=self.auth(MANAGER)
        )
        names = [c["legal_name"] for c in response.json()["customers"]]
        self.assertIn("מפיצי הצפון בע\"מ", names)

    def test_consultant_cannot_create_a_customer(self) -> None:
        response = self.client.post(
            f"/v1/tenants/{TENANT}/customers",
            headers=self.auth(CONSULTANT),
            json={"legalName": "X", "customerCode": "C0199"},
        )
        self.assertEqual(response.status_code, 403)

    def test_consultant_can_read_customers(self) -> None:
        response = self.client.get(
            f"/v1/tenants/{TENANT}/customers", headers=self.auth(CONSULTANT)
        )
        self.assertEqual(response.status_code, 200)

    def test_duplicate_customer_code_is_refused(self) -> None:
        self.create_customer("C0103")
        response = self.client.post(
            f"/v1/tenants/{TENANT}/customers",
            headers=self.auth(MANAGER),
            json={"legalName": "Another", "customerCode": "C0103"},
        )
        self.assertEqual(response.status_code, 409)

    def test_another_tenants_member_is_refused(self) -> None:
        response = self.client.get(
            f"/v1/tenants/{TENANT}/customers", headers=self.auth(OUTSIDER)
        )
        self.assertEqual(response.status_code, 403)

    def test_denial_is_audited_with_the_reason(self) -> None:
        self.client.post(
            f"/v1/tenants/{TENANT}/customers",
            headers={**self.auth(CONSULTANT), "X-Correlation-Id": "cor_wsp_denial"},
            json={"legalName": "X", "customerCode": "C0198"},
        )
        rows = psql(
            "SELECT outcome || '|' || (detail->>'reason') FROM audit.events "
            "WHERE correlation_id = 'cor_wsp_denial';"
        )
        self.assertEqual(rows, "denied|role_lacks_authority")


class TestWorkspaces(WorkspaceTestCase):
    def test_workspace_is_created_under_a_customer(self) -> None:
        customer_id = self.create_customer("C0201")
        workspace_id = self.create_workspace(customer_id, "ERP ראשי")

        response = self.client.get(
            f"/v1/tenants/{TENANT}/workspaces?customer_id={customer_id}",
            headers=self.auth(LEAD),
        )
        workspaces = response.json()["workspaces"]
        self.assertEqual(len(workspaces), 1)
        self.assertEqual(workspaces[0]["id"], workspace_id)
        self.assertEqual(workspaces[0]["state"], "proposed")
        self.assertEqual(workspaces[0]["customer_name"], "לקוח בדיקה בע\"מ")

    def test_a_customer_may_hold_several_workspaces(self) -> None:
        customer_id = self.create_customer("C0202")
        self.create_workspace(customer_id, "ERP")
        self.create_workspace(customer_id, "eCommerce")
        response = self.client.get(
            f"/v1/tenants/{TENANT}/workspaces?customer_id={customer_id}",
            headers=self.auth(LEAD),
        )
        self.assertEqual(len(response.json()["workspaces"]), 2)

    def test_duplicate_workspace_name_for_one_customer_is_refused(self) -> None:
        customer_id = self.create_customer("C0203")
        self.create_workspace(customer_id, "ERP")
        response = self.client.post(
            f"/v1/tenants/{TENANT}/workspaces",
            headers=self.auth(LEAD),
            json={"customerId": customer_id, "name": "ERP"},
        )
        self.assertEqual(response.status_code, 409)

    def test_a_workspace_cannot_be_created_for_another_tenants_customer(self) -> None:
        customer_id = self.create_customer("C0204")
        response = self.client.post(
            f"/v1/tenants/{OTHER_TENANT}/workspaces",
            headers=self.auth(OUTSIDER),
            json={"customerId": customer_id, "name": "Stolen"},
        )
        # The outsider is a legitimate account_owner in their own tenant, so
        # authority passes and scope is what refuses: the customer row is
        # invisible under their tenant context.
        self.assertEqual(response.status_code, 409, response.text)


class TestStateMachine(WorkspaceTestCase):
    def test_legal_transition_is_recorded_with_the_role_used(self) -> None:
        customer_id = self.create_customer("C0301")
        workspace_id = self.create_workspace(customer_id, "ERP")

        response = self.client.post(
            f"/v1/tenants/{TENANT}/workspaces/{workspace_id}/transition",
            headers=self.auth(LEAD),
            json={"toState": "discovering", "reason": "kickoff"},
        )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["workspace"]["state"], "discovering")

        history = self.client.get(
            f"/v1/tenants/{TENANT}/workspaces/{workspace_id}/history",
            headers=self.auth(LEAD),
        ).json()["history"]
        self.assertEqual([h["to_state"] for h in history], ["proposed", "discovering"])
        self.assertEqual(history[1]["actor_role"], "solution_owner")
        self.assertEqual(history[1]["reason"], "kickoff")

    def test_illegal_transition_is_refused(self) -> None:
        customer_id = self.create_customer("C0302")
        workspace_id = self.create_workspace(customer_id, "ERP")

        # proposed -> operating skips the entire engagement.
        response = self.client.post(
            f"/v1/tenants/{TENANT}/workspaces/{workspace_id}/transition",
            headers=self.auth(MANAGER),
            json={"toState": "operating"},
        )
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["detail"]["error"], "illegal_transition")

    def test_completion_requires_the_account_manager(self) -> None:
        customer_id = self.create_customer("C0303")
        workspace_id = self.create_workspace(customer_id, "ERP")

        for state in ("discovering", "designing", "blueprint_review",
                      "approved_for_sandbox", "provisioning", "sandbox_active",
                      "customer_review", "accepted"):
            response = self.client.post(
                f"/v1/tenants/{TENANT}/workspaces/{workspace_id}/transition",
                headers=self.auth(LEAD),
                json={"toState": state},
            )
            self.assertEqual(response.status_code, 200, f"{state}: {response.text}")

        # The Team Lead delivered it, but confirming the engagement is finished
        # belongs to the Account Manager.
        refused = self.client.post(
            f"/v1/tenants/{TENANT}/workspaces/{workspace_id}/transition",
            headers=self.auth(LEAD),
            json={"toState": "operating"},
        )
        self.assertEqual(refused.status_code, 403)

        allowed = self.client.post(
            f"/v1/tenants/{TENANT}/workspaces/{workspace_id}/transition",
            headers=self.auth(MANAGER),
            json={"toState": "operating", "reason": "customer signed off"},
        )
        self.assertEqual(allowed.status_code, 200, allowed.text)
        self.assertEqual(allowed.json()["workspace"]["state"], "operating")

    def test_history_is_append_only_for_the_api_role(self) -> None:
        from scripts.db import run_psql

        result = run_psql(
            "UPDATE app.workspace_state_history SET to_state = 'closed';",
            user="app_api",
            password="local_dev_only",
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("permission denied", (result.stderr + result.stdout).lower())


if __name__ == "__main__":
    unittest.main(verbosity=2)

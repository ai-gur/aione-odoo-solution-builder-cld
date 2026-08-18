"""Blueprint generation (Increment 4).

The behaviours that make a blueprint trustworthy: it reads only an approved
discovery version, it joins requirements to capabilities on an explicit key
rather than on words, and when the catalogue has nothing it says so instead of
naming a plausible module.
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

from aione_domain import blueprint  # noqa: E402
from aione_domain.main import app  # noqa: E402
from scripts.db import psql  # noqa: E402

TENANT = "ten_01JQZX3K8YB2N4V6R8T0W2C5B1"
LEAD = "auth|bp-lead"

SEED = f"""
DELETE FROM app.fit_assessments WHERE tenant_id = '{TENANT}';
DELETE FROM app.blueprint_modules WHERE tenant_id = '{TENANT}';
DELETE FROM app.blueprints WHERE tenant_id = '{TENANT}';
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
DELETE FROM app.users WHERE auth_subject = '{LEAD}' OR email = 'bp@aione.test';
DELETE FROM app.tenants WHERE id = '{TENANT}';

INSERT INTO app.tenants (id, name) VALUES ('{TENANT}', 'AIOne Blueprint');
INSERT INTO app.users (id, auth_subject, email, display_name) VALUES
  ('usr_BPLEAD000000000000001', '{LEAD}', 'bp@aione.test', 'Blueprint Lead');
INSERT INTO app.memberships (id, tenant_id, user_id, role_key) VALUES
  ('mbr_BP00000000000000000001', '{TENANT}', 'usr_BPLEAD000000000000001', 'account_owner'),
  ('mbr_BP00000000000000000002', '{TENANT}', 'usr_BPLEAD000000000000001', 'consultant');
"""

# A wholesale distributor: two companies, three warehouses, serial tracking,
# Israeli accounting, discount and credit approvals.
ANSWERS = {
    "QS-01": "מפיצים ציוד חשמלי לקבלנים ולחנויות.",
    "QS-02": ["physical_products"],
    "QS-03": ["businesses", "sales_team"],
    "QS-04": {"employees": "24", "expected_users": "15", "monthly_transactions": "1200"},
    "QS-05": {"companies": "2", "countries": "1", "branches": "2", "warehouses": "3"},
    "QS-06": ["crm", "sales", "purchase", "inventory", "accounting"],
    "QS-07": ["another_erp"],
    "QS-08": ["multiple_warehouses", "serial_tracking"],
    "QS-11": "external",
    "QS-14": ["איטיות בהפקת הזמנות", "חוסר נראות מלאי", "טעויות תמחור"],
    "QS-15": "קיצור זמן הפקת הזמנה בחצי.",
    "QS-16": ["discounts", "purchases"],
    "QS-17": ["customers", "products"],
}


class TestClassification(unittest.TestCase):
    """The decision function is pure, so most behaviour needs no database."""

    def capability(self, **overrides):
        base = {
            "capability_key": "inventory.multi_warehouse",
            "domain": "INV",
            "description": {"en_US": "Manage stock across warehouses.", "he_IL": "ניהול מלאי."},
            "addresses_topics": ["inventory.multi_warehouse"],
            "modules": ["stock"],
            "edition": "community",
            "coverage": "full",
            "activation": {"settingField": "group_stock_multi_locations"},
            "security_surfaces": [],
            "evidence": [],
            "limitations": [],
            "residual_gap": None,
            "status": "draft",
        }
        return {**base, **overrides}

    def test_no_candidate_is_unresolved_not_a_guess(self) -> None:
        decision = blueprint.classify(
            {"requirement_ref": "REQ-APR-001", "topic": "approval.discounts"},
            [],
            {"approval.discounts": {
                "topic": "approval.discounts", "finding": "F-01",
                "reason": "No capability requires approval before a discounted quotation.",
                "candidates": [{"modules": ["approvals"], "edition": "enterprise"}],
                "treatment": "Unresolved pending functional review.",
            }},
        )
        self.assertEqual(decision["classification"], "unresolved")
        self.assertIsNone(decision["capability_key"])
        self.assertEqual(decision["modules"], [], "no module may be named for an unresolved topic")
        self.assertEqual(decision["confidence"], "red")
        # The candidate that needs verification is carried forward for review.
        self.assertEqual(decision["alternatives"][0]["modules"], ["approvals"])

    def test_an_unknown_topic_with_no_recorded_reason_is_still_unresolved(self) -> None:
        decision = blueprint.classify(
            {"requirement_ref": "REQ-X", "topic": "something.unheard_of"}, [], {}
        )
        self.assertEqual(decision["classification"], "unresolved")
        self.assertIn("something.unheard_of", decision["rationale"]["en_US"])

    def test_a_capability_needing_a_setting_is_a_configuration_fit(self) -> None:
        decision = blueprint.classify(
            {"requirement_ref": "REQ-INV-003", "topic": "inventory.multi_warehouse"},
            [self.capability()], {},
        )
        self.assertEqual(decision["classification"], "configuration_fit")
        self.assertIn("group_stock_multi_locations", decision["rationale"]["en_US"])

    def test_a_draft_capability_cannot_produce_a_green_assessment(self) -> None:
        draft = blueprint.classify(
            {"requirement_ref": "R", "topic": "inventory.multi_warehouse"},
            [self.capability(status="draft")], {},
        )
        verified = blueprint.classify(
            {"requirement_ref": "R", "topic": "inventory.multi_warehouse"},
            [self.capability(status="verified", verified_by="A Reviewer",
                             verified_on="2026-08-18")], {},
        )
        self.assertEqual(draft["confidence"], "amber")
        self.assertIn("draft", draft["rationale"]["en_US"])
        self.assertEqual(verified["confidence"], "green")

    def test_a_green_assessment_names_the_reviewer_it_rests_on(self) -> None:
        """Green means a person confirmed the claim. The record says which
        person, and keeps saying so after the catalogue moves on."""
        decision = blueprint.classify(
            {"requirement_ref": "R", "topic": "inventory.multi_warehouse"},
            [self.capability(status="verified", verified_by="Nir Bar, founding partner, AIOne",
                             verified_on="2026-08-18")], {},
        )
        self.assertIn("Nir Bar", decision["rationale"]["en_US"])
        self.assertIn("2026-08-18", decision["rationale"]["en_US"])

    def test_verification_does_not_close_a_partial_coverage_gap(self) -> None:
        """A reviewer confirming that a capability is partial has confirmed
        the gap, not removed it."""
        decision = blueprint.classify(
            {"requirement_ref": "R", "topic": "inventory.traceability.expiry"},
            [self.capability(status="verified", verified_by="A Reviewer",
                             verified_on="2026-08-18", coverage="partial",
                             residual_gap="Blocking is unconfirmed.")], {},
        )
        self.assertEqual(decision["confidence"], "amber")
        self.assertEqual(decision["residual_gap"], "Blocking is unconfirmed.")

    def test_partial_coverage_produces_a_gap(self) -> None:
        decision = blueprint.classify(
            {"requirement_ref": "R", "topic": "inventory.traceability.expiry"},
            [self.capability(coverage="partial", residual_gap="Blocking is unconfirmed.")], {},
        )
        self.assertEqual(decision["classification"], "partial_fit")
        self.assertEqual(decision["residual_gap"], "Blocking is unconfirmed.")

    def test_a_verified_capability_is_preferred_over_a_draft(self) -> None:
        decision = blueprint.classify(
            {"requirement_ref": "R", "topic": "inventory.multi_warehouse"},
            [
                self.capability(capability_key="draft.one", status="draft"),
                self.capability(capability_key="verified.one", status="verified"),
            ],
            {},
        )
        self.assertEqual(decision["capability_key"], "verified.one")
        self.assertEqual(decision["alternatives"][0]["capabilityKey"], "draft.one")

    def test_two_equally_ranked_capabilities_are_a_decision_not_a_sort_order(self) -> None:
        """Odoo often offers two real ways to do something — a threshold on the
        purchase order, or an approval request the order is created from
        (F-05). Choosing alphabetically and calling it green would hide that a
        business decision was made by a sort."""
        verified = dict(status="verified", verified_by="A Reviewer", verified_on="2026-08-18")
        decision = blueprint.classify(
            {"requirement_ref": "REQ-APR-002", "topic": "approval.purchases"},
            [
                self.capability(capability_key="purchase.approval.request_workflow", **verified),
                self.capability(capability_key="purchase.approval.thresholds", **verified),
            ],
            {},
        )
        self.assertEqual(decision["confidence"], "amber")
        self.assertIn("decision for the review", decision["rationale"]["en_US"])
        self.assertIn("consulting decision", decision["alternatives"][0]["reason"])

    def test_a_verified_capability_still_outranks_a_draft_one(self) -> None:
        """Unequal ranks are settled by evidence, so no decision is needed."""
        decision = blueprint.classify(
            {"requirement_ref": "R", "topic": "approval.purchases"},
            [
                self.capability(capability_key="draft.one", status="draft"),
                self.capability(capability_key="verified.one", status="verified",
                                verified_by="A Reviewer", verified_on="2026-08-18"),
            ],
            {},
        )
        self.assertEqual(decision["capability_key"], "verified.one")
        self.assertEqual(decision["confidence"], "green")
        self.assertNotIn("decision for the review", decision["rationale"]["en_US"])

    def test_israeli_localization_is_classified_as_localization(self) -> None:
        decision = blueprint.classify(
            {"requirement_ref": "REQ-FIN-001", "topic": "finance.accounting_israel"},
            [self.capability(
                capability_key="finance.chart_of_accounts_israel", domain="FIN",
                modules=["l10n_il", "account"], activation={},
            )],
            {},
        )
        self.assertEqual(decision["classification"], "localization_fit")


class TestBlueprintGeneration(unittest.TestCase):
    client: TestClient
    workspace_id: str

    @classmethod
    def setUpClass(cls) -> None:
        psql(SEED)
        cls.client = TestClient(app)
        cls.client.__enter__()

        customer = cls.client.post(
            f"/v1/tenants/{TENANT}/customers", headers=cls.auth(),
            json={"legalName": "מפיצי הצפון בע\"מ", "customerCode": "C1100"},
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

    def generate(self):
        return self.client.post(
            f"/v1/tenants/{TENANT}/workspaces/{self.workspace_id}/blueprints", headers=self.auth()
        )

    def complete_and_approve_discovery(self) -> None:
        run_id = self.client.post(
            f"/v1/tenants/{TENANT}/workspaces/{self.workspace_id}/interviews",
            headers=self.auth(), json={"mode": "quick_start"},
        ).json()["run"]["id"]
        for key, value in ANSWERS.items():
            self.client.post(
                f"/v1/tenants/{TENANT}/interviews/{run_id}/answers",
                headers=self.auth(), json={"questionKey": key, "value": value},
            )
        self.client.post(
            f"/v1/tenants/{TENANT}/interviews/{run_id}/normalise", headers=self.auth()
        )
        approved = self.client.post(
            f"/v1/tenants/{TENANT}/interviews/{run_id}/approve", headers=self.auth()
        )
        self.assertEqual(approved.status_code, 201, approved.text)

    def test_generation_refuses_without_approved_discovery(self) -> None:
        # Its own workspace: discovery approval is terminal, so this cannot
        # share the one the other tests approve.
        customer = self.client.post(
            f"/v1/tenants/{TENANT}/customers", headers=self.auth(),
            json={"legalName": "ללא אפיון בע\"מ", "customerCode": "C1101"},
        ).json()["customer"]
        workspace = self.client.post(
            f"/v1/tenants/{TENANT}/workspaces", headers=self.auth(),
            json={"customerId": customer["id"], "name": "No discovery"},
        ).json()["workspace"]

        response = self.client.post(
            f"/v1/tenants/{TENANT}/workspaces/{workspace['id']}/blueprints", headers=self.auth()
        )
        self.assertEqual(response.status_code, 409)
        self.assertIn("approved discovery version", response.json()["detail"]["error"])

    def setUp(self) -> None:
        """Approve discovery once for the shared workspace, then reuse it.

        Approval is terminal, so this runs only when it has not happened yet.
        """
        approved = psql(
            "SELECT count(*) FROM discovery.discovery_versions "
            f"WHERE workspace_id = '{self.workspace_id}';"
        )
        if approved.strip() == "0":
            self.complete_and_approve_discovery()

    def test_a_blueprint_maps_the_approved_requirements(self) -> None:
        response = self.generate()
        self.assertEqual(response.status_code, 201, response.text)

        result = response.json()["blueprint"]
        by_ref = {a["requirement_ref"]: a for a in result["assessments"]}

        # Multi-warehouse and serial tracking are covered by stock.
        self.assertEqual(by_ref["REQ-INV-003"]["classification"], "configuration_fit")
        self.assertEqual(by_ref["REQ-INV-003"]["modules"], ["stock"])
        self.assertEqual(by_ref["REQ-INV-001"]["capability_key"], "inventory.traceability.serial")

        # Two companies means multi-company.
        self.assertEqual(by_ref["REQ-ORG-001"]["capability_key"], "organisation.multi_company")

        # Purchase approvals exist; discount approvals do not (F-01).
        self.assertEqual(by_ref["REQ-APR-002"]["capability_key"], "purchase.approval.thresholds")
        self.assertEqual(by_ref["REQ-APR-001"]["classification"], "unresolved")
        self.assertEqual(by_ref["REQ-APR-001"]["modules"], [])

    def test_a_verified_catalogue_carries_assessments_to_green(self) -> None:
        """The nine pilot capabilities were verified on 18 August 2026, and
        that is what green rests on: a fully covered, verified capability is
        green, and the assessment names the reviewer."""
        blueprint_id = self.generate().json()["blueprint"]["id"]
        result = self.client.get(
            f"/v1/tenants/{TENANT}/blueprints/{blueprint_id}", headers=self.auth()
        ).json()["blueprint"]
        self.assertTrue(result["assessments"])

        green = [a for a in result["assessments"] if a["confidence"] == "green"]
        self.assertTrue(green, "a verified catalogue produced no green assessment")
        for assessment in green:
            self.assertIsNotNone(assessment["capability_key"])
            self.assertIsNone(assessment["residual_gap"])
            self.assertIn("verified by", assessment["rationale"]["en_US"])

    def test_verification_does_not_resolve_what_the_catalogue_lacks(self) -> None:
        """Reviewing what the catalogue contains says nothing about what it
        does not. F-01 is still open, so discount approval is still red."""
        blueprint_id = self.generate().json()["blueprint"]["id"]
        result = self.client.get(
            f"/v1/tenants/{TENANT}/blueprints/{blueprint_id}", headers=self.auth()
        ).json()["blueprint"]
        by_ref = {a["requirement_ref"]: a for a in result["assessments"]}

        self.assertEqual(by_ref["REQ-APR-001"]["classification"], "unresolved")
        self.assertEqual(by_ref["REQ-APR-001"]["confidence"], "red")
        self.assertEqual(by_ref["REQ-APR-001"]["modules"], [])
        self.assertFalse(result["summary"]["readyForReview"])

    def test_selected_modules_record_what_justified_them(self) -> None:
        blueprint_id = self.generate().json()["blueprint"]["id"]
        result = self.client.get(
            f"/v1/tenants/{TENANT}/blueprints/{blueprint_id}", headers=self.auth()
        ).json()["blueprint"]

        by_module = {m["technical_name"]: m for m in result["modules"]}
        self.assertIn("stock", by_module)
        # Business-selected, and the requirement that selected it is named.
        self.assertEqual(by_module["stock"]["inclusion"], "business_selected")
        self.assertTrue(by_module["stock"]["justified_by"])

    def test_an_unresolved_topic_blocks_review_readiness(self) -> None:
        result = self.generate().json()["blueprint"]
        self.assertGreaterEqual(result["summary"]["unresolved"], 1)
        self.assertFalse(result["summary"]["readyForReview"])

    def test_each_generation_creates_a_new_version(self) -> None:
        first = self.generate().json()["blueprint"]["version"]
        second = self.generate().json()["blueprint"]["version"]
        self.assertEqual(second, first + 1)

    def test_generation_is_audited(self) -> None:
        self.generate()
        count = psql(
            "SELECT count(*) FROM audit.events WHERE tenant_id = "
            f"'{TENANT}' AND action = 'blueprint.generated';"
        )
        self.assertGreaterEqual(int(count), 1)

    def test_the_database_refuses_a_verified_capability_with_no_reviewer(self) -> None:
        """Even the migrator cannot write one. A loader that forgets to carry
        the provenance fails at load rather than producing green assessments
        that rest on nobody (migration 0010)."""
        from scripts.db import run_psql

        set_id = psql(
            "SELECT id FROM catalogue.capability_sets ORDER BY loaded_at DESC LIMIT 1;"
        ).strip()
        result = run_psql(
            "INSERT INTO catalogue.capabilities "
            "(id, set_id, capability_key, domain, description, status) VALUES "
            f"('cap_UNATTRIBUTED0000000000001', '{set_id}', 'test.unattributed', 'INV', "
            "'{}'::jsonb, 'verified');"
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "capabilities_verified_names_its_reviewer",
            (result.stderr + result.stdout).lower(),
        )

    def test_fit_assessments_cannot_be_deleted_by_the_api_role(self) -> None:
        from scripts.db import run_psql

        result = run_psql(
            "DELETE FROM app.fit_assessments;", user="app_api", password="local_dev_only"
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("permission denied", (result.stderr + result.stdout).lower())


if __name__ == "__main__":
    unittest.main(verbosity=2)

"""Normalisation: answers to facts, requirements and open questions.

Discovery §12 and §18. The properties under test are the ones that make the
output trustworthy rather than merely present: determinism, provenance on every
row, uncertainty preserved rather than resolved by the system, and nothing
derived from an unanswered question.
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
    "postgresql://app_api:local_dev_only@localhost:55432/aione_control",
)
os.environ.setdefault("APP_ENVIRONMENT", "local")
os.environ.setdefault("AUTH_MODE", "dev")

from fastapi.testclient import TestClient  # noqa: E402

from aione_domain import normalisation  # noqa: E402
from aione_domain.main import app  # noqa: E402
from scripts.db import psql  # noqa: E402

TENANT = "ten_01JQZX3K8YB2N4V6R8T0W2C5N1"
LEAD = "auth|norm-lead"

SEED = f"""
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
DELETE FROM app.users WHERE auth_subject = '{LEAD}' OR email = 'norm-lead@aione.test';
DELETE FROM app.tenants WHERE id = '{TENANT}';

INSERT INTO app.tenants (id, name) VALUES ('{TENANT}', 'AIOne Normalisation');
INSERT INTO app.users (id, auth_subject, email, display_name) VALUES
  ('usr_NORMLEAD00000000000001', '{LEAD}', 'norm-lead@aione.test', 'Normalisation Lead');
INSERT INTO app.memberships (id, tenant_id, user_id, role_key) VALUES
  ('mbr_NORM000000000000000001', '{TENANT}', 'usr_NORMLEAD00000000000001', 'account_owner'),
  ('mbr_NORM000000000000000002', '{TENANT}', 'usr_NORMLEAD00000000000001', 'consultant');
"""


class TestRulesInIsolation(unittest.TestCase):
    """The rules are pure functions, so most of the behaviour needs no database."""

    def test_nothing_is_derived_from_no_answers(self) -> None:
        derived = normalisation.derive({})
        self.assertEqual(derived.facts, [])
        self.assertEqual(derived.requirements, [])
        self.assertEqual(derived.open_questions, [])

    def test_stated_facts_are_confirmed_and_inferred_facts_are_labelled(self) -> None:
        derived = normalisation.derive({"QS-02": ["physical_products"]})
        by_key = {fact["fact_key"]: fact for fact in derived.facts}

        self.assertEqual(by_key["offering.types"]["verification_state"], "confirmed")
        # Not stated by the customer; concluded by the system, and marked so.
        self.assertEqual(by_key["offering.handles_physical_goods"]["verification_state"], "inferred")
        self.assertTrue(by_key["offering.handles_physical_goods"]["value"])

    def test_finance_stays_unverified_however_clearly_it_was_stated(self) -> None:
        derived = normalisation.derive({"QS-11": "full_accounting"})
        scope = next(f for f in derived.facts if f["fact_key"] == "finance.scope")
        self.assertEqual(scope["confidence"], "amber")
        self.assertEqual(scope["verification_state"], "unverified")

    def test_finance_scope_raises_a_blocking_confirmation_item(self) -> None:
        derived = normalisation.derive({"QS-11": "full_accounting"})
        item = next(q for q in derived.open_questions if q["topic_key"] == "finance.owner_confirmation")
        self.assertTrue(item["blocking"])
        self.assertEqual(item["severity"], "high")

    def test_undecided_finance_blocks_rather_than_assuming(self) -> None:
        derived = normalisation.derive({"QS-11": "undecided"})
        topics = {q["topic_key"] for q in derived.open_questions}
        self.assertIn("finance.scope_undecided", topics)
        # An undecided answer must not produce a requirement.
        self.assertEqual([r for r in derived.requirements if r["domain"] == "FIN"], [])

    def test_approvals_become_must_requirements_with_acceptance_criteria(self) -> None:
        derived = normalisation.derive({"QS-16": ["discounts", "purchases"]})
        self.assertEqual(len(derived.requirements), 2)
        first = derived.requirements[0]
        self.assertEqual(first["priority"], "must")
        self.assertEqual(first["sources"], ["QS-16"])
        self.assertTrue(first["acceptance_criteria"])
        self.assertIn("הנחות", first["statement"]["he_IL"])
        self.assertIn("discounts", first["statement"]["en_US"])

    def test_no_approval_selection_produces_no_requirement(self) -> None:
        self.assertEqual(normalisation.derive({"QS-16": ["none"]}).requirements, [])

    def test_requirements_do_not_name_odoo_modules(self) -> None:
        """The technical decision belongs to the Blueprint Engine against a
        verified catalogue, not to normalisation (Discovery §18)."""
        answers = {
            "QS-02": ["physical_products"],
            "QS-05": {"companies": "2", "warehouses": "3"},
            "QS-08": ["serial_tracking", "expiry_dates"],
            "QS-11": "full_accounting",
            "QS-16": ["discounts"],
        }
        # "stock" and "inventory" are ordinary business words and must stay
        # allowed; what may not appear is a product or technical identifier.
        forbidden = ("odoo", "studio", "sale_management", "account.move", "stock.picking")
        for requirement in normalisation.derive(answers).requirements:
            text = " ".join(requirement["statement"].values()).lower()
            for word in forbidden:
                self.assertNotIn(word, text, f"{requirement['requirement_ref']} names a technical choice")
            # Nor a module-shaped token, which is how such a name would arrive.
            for token in text.split():
                self.assertNotRegex(
                    token.strip(".,"), r"^[a-z]+[._][a-z_.]+$",
                    f"{requirement['requirement_ref']} contains a technical identifier",
                )

    def test_multi_company_and_warehouse_counts_drive_requirements(self) -> None:
        derived = normalisation.derive({"QS-05": {"companies": "3", "warehouses": "2"}})
        refs = {r["requirement_ref"] for r in derived.requirements}
        self.assertIn("REQ-ORG-001", refs)
        self.assertIn("REQ-INV-003", refs)

    def test_single_company_produces_no_multi_company_requirement(self) -> None:
        derived = normalisation.derive({"QS-05": {"companies": "1", "warehouses": "1"}})
        self.assertEqual(derived.requirements, [])

    def test_manufacturing_complexity_escalates(self) -> None:
        simple = normalisation.derive({"QS-10": "simple_assembly"}).open_questions
        self.assertEqual(simple, [])
        complex_ = normalisation.derive({"QS-10": "work_centers"}).open_questions
        self.assertTrue(complex_[0]["blocking"])

    def test_named_integration_opens_a_qualification_item(self) -> None:
        derived = normalisation.derive({"QS-13": {"system_name": "Priority", "purpose": "billing"}})
        item = derived.open_questions[0]
        self.assertEqual(item["topic_key"], "integration.qualification")
        self.assertIn("Priority", item["question"]["en_US"])

    def test_derivation_is_deterministic(self) -> None:
        answers = {"QS-02": ["physical_products"], "QS-16": ["discounts"], "QS-11": "invoicing_only"}
        first = normalisation.derive(answers)
        second = normalisation.derive(answers)
        self.assertEqual(
            [f["fact_key"] for f in first.facts], [f["fact_key"] for f in second.facts]
        )
        self.assertEqual(
            [r["requirement_ref"] for r in first.requirements],
            [r["requirement_ref"] for r in second.requirements],
        )


class TestNormalisationEndToEnd(unittest.TestCase):
    client: TestClient
    run_id: str

    @classmethod
    def setUpClass(cls) -> None:
        psql(SEED)
        cls.client = TestClient(app)
        cls.client.__enter__()

        customer = cls.client.post(
            f"/v1/tenants/{TENANT}/customers",
            headers=cls.auth(),
            json={"legalName": "מפיצי המרכז בע\"מ", "customerCode": "C0700"},
        ).json()["customer"]
        workspace = cls.client.post(
            f"/v1/tenants/{TENANT}/workspaces",
            headers=cls.auth(),
            json={"customerId": customer["id"], "name": "ERP"},
        ).json()["workspace"]
        run = cls.client.post(
            f"/v1/tenants/{TENANT}/workspaces/{workspace['id']}/interviews",
            headers=cls.auth(),
            json={"mode": "quick_start"},
        ).json()["run"]
        cls.run_id = run["id"]

    @classmethod
    def tearDownClass(cls) -> None:
        cls.client.__exit__(None, None, None)

    @classmethod
    def auth(cls) -> dict[str, str]:
        return {"Authorization": f"Bearer {LEAD}"}

    def setUp(self) -> None:
        """Each test starts from the same answered interview.

        unittest runs methods in alphabetical order, so a test that depends on
        another having run first passes or fails according to its own name.
        Re-answering is cheap and makes each test independent.
        """
        self.answer("QS-01", "מפיצים ציוד חשמלי לקבלנים ולחנויות.")
        self.answer("QS-02", ["physical_products"])
        self.answer("QS-05", {"companies": "2", "countries": "1", "warehouses": "3"})
        self.answer("QS-08", ["multiple_warehouses", "serial_tracking"])
        self.answer("QS-11", "full_accounting")
        self.answer("QS-16", ["discounts", "credit"])
        self.answer("QS-17", ["customers", "products", "accounting_balances"])
        self.normalise()

    def answer(self, key: str, value) -> None:
        response = self.client.post(
            f"/v1/tenants/{TENANT}/interviews/{self.run_id}/answers",
            headers=self.auth(),
            json={"questionKey": key, "value": value},
        )
        self.assertEqual(response.status_code, 200, response.text)

    def normalise(self) -> dict:
        response = self.client.post(
            f"/v1/tenants/{TENANT}/interviews/{self.run_id}/normalise", headers=self.auth()
        )
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def derived(self) -> dict:
        response = self.client.get(
            f"/v1/tenants/{TENANT}/interviews/{self.run_id}/derived", headers=self.auth()
        )
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def test_a_wholesale_interview_produces_a_reviewable_result(self) -> None:
        view = self.derived()
        self.assertTrue(view["facts"])
        self.assertTrue(view["requirements"])
        refs = {r["requirement_ref"] for r in view["requirements"]}
        self.assertIn("REQ-ORG-001", refs, "two companies should require multi-company support")
        self.assertIn("REQ-INV-001", refs, "serial tracking should require traceability")
        self.assertIn("REQ-FIN-001", refs)

        topics = {q["topic_key"] for q in view["openQuestions"]}
        self.assertIn("finance.owner_confirmation", topics)
        self.assertIn("data.migration_qualification", topics)
        self.assertGreaterEqual(view["blockingCount"], 2)

    def test_every_derived_row_carries_its_source(self) -> None:
        view = self.derived()
        for collection in ("facts", "requirements", "openQuestions"):
            for row in view[collection]:
                self.assertTrue(
                    row["source_question_keys"],
                    f"{collection} row without provenance: {row}",
                )

    def test_re_running_changes_nothing(self) -> None:
        before = self.derived()
        result = self.normalise()
        after = self.derived()
        self.assertEqual(result["superseded"], 0)
        self.assertEqual(
            [r["requirement_ref"] for r in before["requirements"]],
            [r["requirement_ref"] for r in after["requirements"]],
        )

    def test_a_corrected_answer_withdraws_the_conclusion_it_supported(self) -> None:
        # The customer corrects themselves: one company, not two.
        self.answer("QS-05", {"companies": "1", "countries": "1", "warehouses": "3"})
        result = self.normalise()
        self.assertGreaterEqual(result["superseded"], 1)

        refs = {r["requirement_ref"] for r in self.derived()["requirements"]}
        self.assertNotIn("REQ-ORG-001", refs, "the multi-company requirement should be withdrawn")
        self.assertIn("REQ-INV-003", refs, "the warehouse requirement should survive")

        # Withdrawn, not erased: the superseded row remains for review.
        superseded = psql(
            "SELECT count(*) FROM discovery.requirements "
            f"WHERE run_id = '{self.run_id}' AND requirement_ref = 'REQ-ORG-001' "
            "AND superseded_at IS NOT NULL;"
        )
        self.assertEqual(superseded, "1")

    def test_derived_rows_cannot_be_deleted_by_the_api_role(self) -> None:
        from scripts.db import run_psql

        result = run_psql(
            "DELETE FROM discovery.requirements;", user="app_api", password="local_dev_only"
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("permission denied", (result.stderr + result.stdout).lower())


if __name__ == "__main__":
    unittest.main(verbosity=2)

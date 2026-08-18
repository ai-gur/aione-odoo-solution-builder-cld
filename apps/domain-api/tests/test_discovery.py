"""Interview engine (Increment 2).

Discovery §25 acceptance criteria exercised here: branching is deterministic,
answers preserve source and original value, a revision does not destroy what
came before, and a hidden question is not an answered question.
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

from aione_domain import rules  # noqa: E402
from aione_domain.main import app  # noqa: E402
from scripts.db import psql  # noqa: E402

TENANT = "ten_01JQZX3K8YB2N4V6R8T0W2C5D1"
LEAD = "auth|disc-lead"
CONSULTANT = "auth|disc-consultant"

SEED = f"""
DELETE FROM discovery.answers WHERE tenant_id = '{TENANT}';
DELETE FROM discovery.interview_runs WHERE tenant_id = '{TENANT}';
DELETE FROM app.workspace_state_history WHERE tenant_id = '{TENANT}';
DELETE FROM app.solution_workspaces WHERE tenant_id = '{TENANT}';
DELETE FROM app.customer_organizations WHERE tenant_id = '{TENANT}';
DELETE FROM audit.events WHERE tenant_id = '{TENANT}';
DELETE FROM app.memberships WHERE tenant_id = '{TENANT}';
DELETE FROM app.users WHERE auth_subject IN ('{LEAD}', '{CONSULTANT}')
   OR email IN ('disc-lead@aione.test', 'disc-consultant@aione.test');
DELETE FROM app.tenants WHERE id = '{TENANT}';

INSERT INTO app.tenants (id, name) VALUES ('{TENANT}', 'AIOne Discovery');
INSERT INTO app.users (id, auth_subject, email, display_name) VALUES
  ('usr_DISCLEAD00000000000001', '{LEAD}', 'disc-lead@aione.test', 'Discovery Lead'),
  ('usr_DISCCONSULT0000000002', '{CONSULTANT}', 'disc-consultant@aione.test', 'Discovery Consultant');
INSERT INTO app.memberships (id, tenant_id, user_id, role_key) VALUES
  ('mbr_DISC000000000000000001', '{TENANT}', 'usr_DISCLEAD00000000000001', 'solution_owner'),
  ('mbr_DISC000000000000000002', '{TENANT}', 'usr_DISCCONSULT0000000002', 'consultant');
"""


class TestRuleEvaluator(unittest.TestCase):
    """The evaluator is pure, so it is tested without a database."""

    def test_always(self) -> None:
        self.assertTrue(rules.evaluate({"always": True}, {}).applicable)
        self.assertFalse(rules.evaluate({"always": False}, {}).applicable)

    def test_answer_includes(self) -> None:
        rule = {"answer_includes": {"question": "QS-02", "any_of": ["physical_products"]}}
        self.assertTrue(rules.evaluate(rule, {"QS-02": ["physical_products", "services"]}).applicable)
        self.assertFalse(rules.evaluate(rule, {"QS-02": ["services"]}).applicable)
        self.assertFalse(rules.evaluate(rule, {}).applicable)

    def test_all_and_any_and_not(self) -> None:
        answers = {"QS-02": ["services"], "QS-11": "full_accounting"}
        self.assertTrue(
            rules.evaluate(
                {"all": [
                    {"answer_includes": {"question": "QS-02", "any_of": ["services"]}},
                    {"answer_equals": {"question": "QS-11", "value": "full_accounting"}},
                ]},
                answers,
            ).applicable
        )
        self.assertTrue(
            rules.evaluate({"any": [
                {"answer_equals": {"question": "QS-11", "value": "invoicing_only"}},
                {"answer_equals": {"question": "QS-11", "value": "full_accounting"}},
            ]}, answers).applicable
        )
        self.assertFalse(rules.evaluate({"not": {"answered": "QS-02"}}, answers).applicable)

    def test_unknown_operator_denies_and_explains(self) -> None:
        result = rules.evaluate({"vibes": "good"}, {})
        self.assertFalse(result.applicable)
        self.assertIn("unknown operator", result.reason)

    def test_validation_rejects_unknown_question(self) -> None:
        with self.assertRaises(rules.RuleError):
            rules.validate({"answered": "QS-99"}, {"QS-01"})

    def test_evaluation_explains_itself(self) -> None:
        rule = {"answer_includes": {"question": "QS-02", "any_of": ["manufactured_products"]}}
        result = rules.evaluate(rule, {"QS-02": ["services"]})
        self.assertIn("QS-02", result.reason)


class InterviewTestCase(unittest.TestCase):
    client: TestClient
    workspace_id: str
    run_id: str

    @classmethod
    def setUpClass(cls) -> None:
        psql(SEED)
        cls.client = TestClient(app)
        cls.client.__enter__()

        customer = cls.client.post(
            f"/v1/tenants/{TENANT}/customers",
            headers={"Authorization": f"Bearer {LEAD}"},
            json={"legalName": "מפיצי הדרום בע\"מ", "customerCode": "C0500"},
        ).json()["customer"]

        workspace = cls.client.post(
            f"/v1/tenants/{TENANT}/workspaces",
            headers={"Authorization": f"Bearer {LEAD}"},
            json={"customerId": customer["id"], "name": "ERP", "discoveryMode": "quick_start"},
        ).json()["workspace"]
        cls.workspace_id = workspace["id"]

    @classmethod
    def tearDownClass(cls) -> None:
        cls.client.__exit__(None, None, None)

    def setUp(self) -> None:
        psql(f"DELETE FROM discovery.answers WHERE tenant_id = '{TENANT}';")
        psql(f"DELETE FROM discovery.interview_runs WHERE tenant_id = '{TENANT}';")
        response = self.client.post(
            f"/v1/tenants/{TENANT}/workspaces/{self.workspace_id}/interviews",
            headers=self.auth(CONSULTANT),
            json={"mode": "quick_start"},
        )
        self.assertEqual(response.status_code, 201, response.text)
        self.run_id = response.json()["run"]["id"]

    @staticmethod
    def auth(subject: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {subject}"}

    def plan(self, locale: str = "he_IL") -> dict:
        response = self.client.get(
            f"/v1/tenants/{TENANT}/interviews/{self.run_id}?locale={locale}",
            headers=self.auth(CONSULTANT),
        )
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def answer(self, question_key: str, value) -> dict:
        return self.client.post(
            f"/v1/tenants/{TENANT}/interviews/{self.run_id}/answers",
            headers=self.auth(CONSULTANT),
            json={"questionKey": question_key, "value": value},
        )


class TestInterviewFlow(InterviewTestCase):
    def test_quick_start_has_eighteen_questions_pinned_to_a_version(self) -> None:
        plan = self.plan()
        self.assertEqual(len(plan["questions"]), 18)
        self.assertEqual(plan["definitionVersion"], 1)
        self.assertEqual(plan["mode"], "quick_start")

    def test_prompts_render_in_the_requested_language(self) -> None:
        hebrew = self.plan("he_IL")["questions"][0]["prompt"]
        english = self.plan("en_US")["questions"][0]["prompt"]
        self.assertIn("החברה", hebrew)
        self.assertIn("company", english)

    def test_conditional_questions_are_hidden_until_their_trigger(self) -> None:
        plan = self.plan()
        by_key = {q["questionKey"]: q for q in plan["questions"]}
        # Nothing has been answered, so the three conditional branches are off.
        self.assertFalse(by_key["QS-08"]["applicable"])
        self.assertFalse(by_key["QS-09"]["applicable"])
        self.assertFalse(by_key["QS-10"]["applicable"])

    def test_answering_offerings_opens_the_matching_branch(self) -> None:
        self.answer("QS-02", ["physical_products"])
        by_key = {q["questionKey"]: q for q in self.plan()["questions"]}

        self.assertTrue(by_key["QS-08"]["applicable"], "inventory branch should open")
        self.assertFalse(by_key["QS-09"]["applicable"], "services branch should stay closed")
        self.assertFalse(by_key["QS-10"]["applicable"], "manufacturing branch should stay closed")

    def test_a_hidden_question_cannot_be_answered(self) -> None:
        # QS-10 applies only to manufacturers. Accepting an answer would create
        # a record of something the customer was never shown.
        response = self.answer("QS-10", "work_centers")
        self.assertEqual(response.status_code, 409)
        self.assertIn("does not apply", response.json()["detail"]["error"])

    def test_progress_counts_only_applicable_questions(self) -> None:
        before = self.plan()["progress"]["applicable"]
        self.answer("QS-02", ["physical_products", "services"])
        after = self.plan()["progress"]

        # Two branches opened, so the denominator grew rather than progress
        # jumping because a fixed total was assumed.
        self.assertEqual(after["applicable"], before + 2)
        self.assertEqual(after["answered"], 1)
        self.assertFalse(after["readyForReview"])

    def test_next_question_walks_the_applicable_set(self) -> None:
        self.assertEqual(self.plan()["nextQuestionKey"], "QS-01")
        self.answer("QS-01", "אנחנו מפיצים ציוד חשמלי לעסקים.")
        self.assertEqual(self.plan()["nextQuestionKey"], "QS-02")

    def test_unknown_question_is_refused(self) -> None:
        self.assertEqual(self.answer("QS-99", "x").status_code, 409)


class TestAnswerIntegrity(InterviewTestCase):
    def test_original_wording_is_preserved_exactly(self) -> None:
        original = "יש לנו מחסן ראשי בפתח תקווה ואזור החזרות קטן במשרד."
        self.answer("QS-01", original)
        plan_answer = next(
            q for q in self.plan()["questions"] if q["questionKey"] == "QS-01"
        )["answer"]
        self.assertEqual(plan_answer, original)

    def test_revision_supersedes_and_keeps_both_versions(self) -> None:
        self.answer("QS-01", "first description")
        second = self.answer("QS-01", "corrected description")
        self.assertEqual(second.status_code, 200)
        self.assertTrue(second.json()["answer"]["revision"])

        history = self.client.get(
            f"/v1/tenants/{TENANT}/interviews/{self.run_id}/answers/QS-01/history",
            headers=self.auth(CONSULTANT),
        ).json()["history"]

        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]["raw_value"], "first description")
        self.assertIsNotNone(history[0]["superseded_at"], "the old answer must be marked, not erased")
        self.assertEqual(history[1]["raw_value"], "corrected description")
        self.assertIsNone(history[1]["superseded_at"])

    def test_answers_cannot_be_deleted_by_the_api_role(self) -> None:
        from scripts.db import run_psql

        self.answer("QS-01", "some answer")
        result = run_psql(
            "DELETE FROM discovery.answers;", user="app_api", password="local_dev_only"
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("permission denied", (result.stderr + result.stdout).lower())

    def test_answer_records_its_source_and_author(self) -> None:
        self.answer("QS-01", "narrative")
        rows = psql(
            "SELECT answer_source || '|' || answered_by FROM discovery.answers "
            f"WHERE run_id = '{self.run_id}' AND question_key = 'QS-01';"
        )
        self.assertEqual(rows, "customer|usr_DISCCONSULT0000000002")


class TestRunLifecycle(InterviewTestCase):
    def test_starting_twice_resumes_rather_than_duplicating(self) -> None:
        again = self.client.post(
            f"/v1/tenants/{TENANT}/workspaces/{self.workspace_id}/interviews",
            headers=self.auth(CONSULTANT),
            json={"mode": "quick_start"},
        )
        self.assertEqual(again.status_code, 201)
        self.assertTrue(again.json()["run"]["resumed"])
        self.assertEqual(again.json()["run"]["id"], self.run_id)

    def test_start_is_audited(self) -> None:
        rows = psql(
            "SELECT count(*) FROM audit.events "
            f"WHERE tenant_id = '{TENANT}' AND action = 'discovery.run.started';"
        )
        self.assertGreaterEqual(int(rows), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)

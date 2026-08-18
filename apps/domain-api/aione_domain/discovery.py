"""Interview runs and answers.

What this module protects (Discovery Engine §12, §25):

- The original wording survives. Normalisation writes a separate field, and a
  revision supersedes rather than overwrites, so what a customer said in March
  is still answerable in September.
- Which questions appear is decided by versioned rules, and the reason each one
  appeared is recorded — "why am I being asked this" always has an answer.
- A run pins its definition version. Improving the questionnaire never rewrites
  a customer's history.
- A hidden question is not an answered question. Progress counts only what is
  applicable now.
"""

from __future__ import annotations

import json
import secrets
from typing import Any

from . import db, rules


class DiscoveryError(Exception):
    """The request cannot be satisfied against the run's current state."""


def new_id(prefix: str) -> str:
    return f"{prefix}_" + secrets.token_hex(13).upper()


def published_definition(mode: str) -> dict[str, Any]:
    """The current published definition for a mode."""
    with db.transaction() as cursor:
        cursor.execute(
            """
            SELECT id, definition_key, version, mode, title, content_digest
              FROM discovery.interview_definitions
             WHERE mode = %s AND status = 'published'
          ORDER BY version DESC
             LIMIT 1
            """,
            (mode,),
        )
        row = cursor.fetchone()
    if row is None:
        raise DiscoveryError(f"no published interview definition for mode {mode}")
    return dict(row)


def _questions(definition_id: str) -> list[dict[str, Any]]:
    with db.transaction() as cursor:
        cursor.execute(
            """
            SELECT question_key, order_index, domain, concept, prompt, help_text,
                   answer_type, options, applicability, required_policy,
                   risk_weight, complexity_weight, evidence_policy
              FROM discovery.question_definitions
             WHERE definition_id = %s
          ORDER BY order_index
            """,
            (definition_id,),
        )
        return [dict(row) for row in cursor.fetchall()]


def start_run(
    *, tenant_id: str, user_id: str, workspace_id: str, mode: str = "quick_start"
) -> dict[str, Any]:
    """Start an interview, or return the one already in progress.

    Resuming rather than starting again is the default: Discovery §3.6 says a
    customer is never asked to repeat information they have already supplied,
    and starting a second run would do exactly that.
    """
    definition = published_definition(mode)
    run_id = new_id("run")

    with db.transaction(tenant_id=tenant_id, user_id=user_id) as cursor:
        cursor.execute(
            """
            SELECT id, definition_id, state, started_at
              FROM discovery.interview_runs
             WHERE workspace_id = %s
               AND state NOT IN ('superseded', 'cancelled')
          ORDER BY started_at
             LIMIT 1
            """,
            (workspace_id,),
        )
        existing = cursor.fetchone()
        if existing is not None:
            return {**dict(existing), "resumed": True}

        cursor.execute(
            """
            INSERT INTO discovery.interview_runs
              (id, tenant_id, workspace_id, definition_id, state, started_by)
            VALUES (%s, %s, %s, %s, 'in_progress', %s)
         RETURNING id, definition_id, state, started_at
            """,
            (run_id, tenant_id, workspace_id, definition["id"], user_id),
        )
        row = cursor.fetchone()
    return {**dict(row), "resumed": False}


def _run(tenant_id: str, user_id: str, run_id: str) -> dict[str, Any]:
    with db.transaction(tenant_id=tenant_id, user_id=user_id) as cursor:
        cursor.execute(
            """
            SELECT r.id, r.workspace_id, r.definition_id, r.state, d.mode, d.version
              FROM discovery.interview_runs r
              JOIN discovery.interview_definitions d ON d.id = r.definition_id
             WHERE r.id = %s
            """,
            (run_id,),
        )
        row = cursor.fetchone()
    if row is None:
        raise DiscoveryError("interview run not found")
    return dict(row)


def current_answers(*, tenant_id: str, user_id: str, run_id: str) -> dict[str, Any]:
    """Live answers as {question_key: normalized_or_raw_value}."""
    with db.transaction(tenant_id=tenant_id, user_id=user_id) as cursor:
        cursor.execute(
            """
            SELECT question_key, raw_value, normalized_value
              FROM discovery.answers
             WHERE run_id = %s AND superseded_at IS NULL
            """,
            (run_id,),
        )
        return {
            row["question_key"]: (
                row["normalized_value"] if row["normalized_value"] is not None else row["raw_value"]
            )
            for row in cursor.fetchall()
        }


def question_plan(*, tenant_id: str, user_id: str, run_id: str, locale: str = "he_IL") -> dict[str, Any]:
    """Every question, with whether it applies now and why.

    Returns the whole plan rather than only the next question, so the interface
    can show progress by section without pretending to know a total that
    branching has not settled yet (Discovery §3.4).
    """
    run = _run(tenant_id, user_id, run_id)
    answers = current_answers(tenant_id=tenant_id, user_id=user_id, run_id=run_id)

    plan: list[dict[str, Any]] = []
    for question in _questions(run["definition_id"]):
        evaluation = rules.evaluate(question["applicability"], answers)
        key = question["question_key"]
        plan.append(
            {
                "questionKey": key,
                "domain": question["domain"],
                "answerType": question["answer_type"],
                "requiredPolicy": question["required_policy"],
                "prompt": question["prompt"].get(locale) or question["prompt"].get("en_US"),
                "helpText": question["help_text"].get(locale),
                "options": [
                    {"value": option["value"], "label": option.get(locale) or option.get("en_US")}
                    for option in question["options"]
                ],
                "applicable": evaluation.applicable,
                # Shown in the consultant workspace, and the reason a skipped
                # section is explainable rather than mysterious.
                "applicabilityReason": evaluation.reason,
                "answered": key in answers,
                "answer": answers.get(key),
            }
        )

    applicable = [item for item in plan if item["applicable"]]
    answered = [item for item in applicable if item["answered"]]
    outstanding_required = [
        item for item in applicable
        if not item["answered"] and item["requiredPolicy"] in ("required", "conditional")
    ]

    return {
        "runId": run_id,
        "mode": run["mode"],
        "definitionVersion": run["version"],
        "state": run["state"],
        "questions": plan,
        "progress": {
            "applicable": len(applicable),
            "answered": len(answered),
            # Not a percentage of the whole definition: questions hidden by
            # branching were never asked, and counting them would make progress
            # look worse than it is.
            "percent": round(100 * len(answered) / len(applicable)) if applicable else 0,
            "outstandingRequired": [item["questionKey"] for item in outstanding_required],
            "readyForReview": not outstanding_required,
        },
        "nextQuestionKey": next(
            (item["questionKey"] for item in applicable if not item["answered"]), None
        ),
    }


def submit_answer(
    *,
    tenant_id: str,
    user_id: str,
    run_id: str,
    question_key: str,
    raw_value: Any,
    answer_source: str = "customer",
    confidence: str = "amber",
) -> dict[str, Any]:
    """Record an answer, superseding any previous one for that question."""
    run = _run(tenant_id, user_id, run_id)
    if run["state"] in ("approved_for_blueprint", "superseded", "cancelled"):
        raise DiscoveryError(f"run is {run['state']} and no longer accepts answers")

    known = {question["question_key"] for question in _questions(run["definition_id"])}
    if question_key not in known:
        raise DiscoveryError(f"{question_key} is not part of this interview definition")

    # A question hidden by branching cannot be answered. Accepting it would
    # let an answer exist that the customer was never shown.
    answers = current_answers(tenant_id=tenant_id, user_id=user_id, run_id=run_id)
    question = next(q for q in _questions(run["definition_id"]) if q["question_key"] == question_key)
    evaluation = rules.evaluate(question["applicability"], answers)
    if not evaluation.applicable:
        raise DiscoveryError(f"{question_key} does not apply: {evaluation.reason}")

    answer_id = new_id("ans")
    with db.transaction(tenant_id=tenant_id, user_id=user_id) as cursor:
        cursor.execute(
            """
            SELECT id FROM discovery.answers
             WHERE run_id = %s AND question_key = %s AND superseded_at IS NULL
            """,
            (run_id, question_key),
        )
        previous = cursor.fetchone()

        if previous is not None:
            cursor.execute(
                "UPDATE discovery.answers SET superseded_at = now() WHERE id = %s",
                (previous["id"],),
            )

        cursor.execute(
            """
            INSERT INTO discovery.answers
              (id, tenant_id, run_id, question_key, raw_value, answered_by,
               answer_source, confidence, supersedes_id)
            VALUES (%s, %s, %s, %s, %s::jsonb, %s, %s, %s, %s)
         RETURNING id, question_key, raw_value, confidence, verification_state, created_at
            """,
            (
                answer_id, tenant_id, run_id, question_key,
                json.dumps(raw_value, ensure_ascii=False), user_id,
                answer_source, confidence,
                previous["id"] if previous else None,
            ),
        )
        row = cursor.fetchone()
    return {**dict(row), "revision": previous is not None}


def answer_history(*, tenant_id: str, user_id: str, run_id: str, question_key: str) -> list[dict[str, Any]]:
    """Every version of one answer, oldest first."""
    with db.transaction(tenant_id=tenant_id, user_id=user_id) as cursor:
        cursor.execute(
            """
            SELECT id, raw_value, answered_by, answer_source, confidence,
                   verification_state, created_at, superseded_at
              FROM discovery.answers
             WHERE run_id = %s AND question_key = %s
          ORDER BY created_at
            """,
            (run_id, question_key),
        )
        return [dict(row) for row in cursor.fetchall()]

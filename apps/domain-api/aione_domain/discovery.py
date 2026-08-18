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

from aione_contracts import digest

from . import db, normalisation, rules


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
            SELECT r.id, r.tenant_id, r.workspace_id, r.definition_id, r.state, d.mode, d.version
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
    if run["state"] in ("superseded", "cancelled"):
        raise DiscoveryError(f"run is {run['state']} and no longer accepts answers")

    # An approved run still accepts corrections. The approved version is a
    # frozen snapshot, so nothing already approved changes; the run simply
    # returns to in progress, and re-approving produces the next version.
    reopened = run["state"] == "approved_for_blueprint"

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

        if reopened:
            cursor.execute(
                "UPDATE discovery.interview_runs SET state = 'in_progress', completed_at = NULL "
                "WHERE id = %s",
                (run_id,),
            )

    return {**dict(row), "revision": previous is not None, "reopened": reopened}


def normalise(*, tenant_id: str, user_id: str, run_id: str) -> dict[str, Any]:
    """Re-derive facts, requirements and open questions from current answers.

    Idempotent by construction: rules are deterministic, so running this twice
    without new answers leaves the same live rows. A row whose value changed is
    superseded and replaced; a row that no longer derives is superseded and not
    replaced, which is how a corrected answer withdraws a conclusion without
    erasing that it was once drawn.
    """
    run = _run(tenant_id, user_id, run_id)
    answers = current_answers(tenant_id=tenant_id, user_id=user_id, run_id=run_id)
    derived = normalisation.derive(answers)

    counts = {"facts": 0, "requirements": 0, "openQuestions": 0, "superseded": 0}

    with db.transaction(tenant_id=tenant_id, user_id=user_id) as cursor:
        counts["superseded"] += _reconcile(
            cursor, run, "business_facts", "fact_key", derived.facts,
            ["value", "confidence", "verification_state"],
            lambda row: {
                "value": row["value"],
                "confidence": row["confidence"],
                "verification_state": row["verification_state"],
            },
            _insert_fact,
        )
        counts["facts"] = len(derived.facts)

        counts["superseded"] += _reconcile(
            cursor, run, "requirements", "requirement_ref", derived.requirements,
            ["topic", "statement", "priority", "confidence"],
            lambda row: {
                "topic": row.get("topic", ""),
                "statement": row["statement"],
                "priority": row["priority"],
                "confidence": row["confidence"],
            },
            _insert_requirement,
        )
        counts["requirements"] = len(derived.requirements)

        counts["superseded"] += _reconcile(
            cursor, run, "open_questions", "topic_key", derived.open_questions,
            ["question", "severity", "blocking"],
            lambda row: {
                "question": row["question"],
                "severity": row["severity"],
                "blocking": row["blocking"],
            },
            _insert_open_question,
        )
        counts["openQuestions"] = len(derived.open_questions)

    return counts


def _reconcile(cursor, run, table: str, key_column: str, wanted: list[dict[str, Any]],
               comparable_columns: list[str], comparable, insert) -> int:
    """Supersede live rows that are gone or changed, insert what is missing.

    Comparing content matters as much as comparing keys. Skipping a row because
    its key already exists means a corrected rule, or a new field, never reaches
    the rows already stored — which is how every requirement ended up with an
    empty topic after the generator learned to produce one.
    """
    columns = ", ".join([key_column, *comparable_columns])
    cursor.execute(
        f"SELECT id, {columns} FROM discovery.{table} "
        "WHERE run_id = %s AND superseded_at IS NULL",
        (run["id"],),
    )
    existing = {row[key_column]: row for row in cursor.fetchall()}
    wanted_by_key = {row[key_column]: row for row in wanted}

    superseded = 0

    def supersede(row_id: str) -> None:
        cursor.execute(
            f"UPDATE discovery.{table} SET superseded_at = now() WHERE id = %s", (row_id,)
        )

    for key, row in existing.items():
        if key not in wanted_by_key:
            supersede(row["id"])
            superseded += 1

    for key, row in wanted_by_key.items():
        current = existing.get(key)
        if current is None:
            insert(cursor, run, row)
            continue

        stored = {column: current[column] for column in comparable_columns}
        if comparable(row) == stored:
            continue

        # The conclusion changed under the same key: the old one is superseded
        # and stays visible, and the new one is inserted beside it.
        supersede(current["id"])
        superseded += 1
        insert(cursor, run, row)

    return superseded


def _insert_fact(cursor, run, row) -> None:
    cursor.execute(
        """
        INSERT INTO discovery.business_facts
          (id, tenant_id, workspace_id, run_id, fact_key, value, source_question_keys,
           extraction_version, confidence, verification_state)
        VALUES (%s, %s, %s, %s, %s, %s::jsonb, %s, %s, %s, %s)
        """,
        (
            new_id("fct"), run["tenant_id"], run["workspace_id"], run["id"],
            row["fact_key"], json.dumps(row["value"], ensure_ascii=False), row["sources"],
            normalisation.VERSION, row["confidence"], row["verification_state"],
        ),
    )


def _insert_requirement(cursor, run, row) -> None:
    cursor.execute(
        """
        INSERT INTO discovery.requirements
          (id, tenant_id, workspace_id, run_id, requirement_ref, domain, topic, statement,
           rationale, acceptance_criteria, priority, confidence, source_question_keys,
           generator_version)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb, %s::jsonb, %s, %s, %s, %s)
        """,
        (
            new_id("req"), run["tenant_id"], run["workspace_id"], run["id"],
            row["requirement_ref"], row["domain"], row.get("topic", ""),
            json.dumps(row["statement"], ensure_ascii=False),
            json.dumps(row["rationale"], ensure_ascii=False),
            json.dumps(row["acceptance_criteria"], ensure_ascii=False),
            row["priority"], row["confidence"], row["sources"], normalisation.VERSION,
        ),
    )


def _insert_open_question(cursor, run, row) -> None:
    cursor.execute(
        """
        INSERT INTO discovery.open_questions
          (id, tenant_id, workspace_id, run_id, topic_key, question, severity, blocking,
           owner_role, source_question_keys, generator_version)
        VALUES (%s, %s, %s, %s, %s, %s::jsonb, %s, %s, %s, %s, %s)
        """,
        (
            new_id("oqs"), run["tenant_id"], run["workspace_id"], run["id"],
            row["topic_key"], json.dumps(row["question"], ensure_ascii=False),
            row["severity"], row["blocking"], row["owner_role"], row["sources"],
            normalisation.VERSION,
        ),
    )


def derived_view(*, tenant_id: str, user_id: str, run_id: str) -> dict[str, Any]:
    """Live facts, requirements and open questions for a run."""
    with db.transaction(tenant_id=tenant_id, user_id=user_id) as cursor:
        cursor.execute(
            """
            SELECT fact_key, value, source_question_keys, confidence, verification_state
              FROM discovery.business_facts
             WHERE run_id = %s AND superseded_at IS NULL
          ORDER BY fact_key
            """,
            (run_id,),
        )
        facts = [dict(row) for row in cursor.fetchall()]

        cursor.execute(
            """
            SELECT requirement_ref, domain, topic, statement, rationale, acceptance_criteria,
                   priority, status, confidence, source_question_keys
              FROM discovery.requirements
             WHERE run_id = %s AND superseded_at IS NULL
          ORDER BY requirement_ref
            """,
            (run_id,),
        )
        requirements = [dict(row) for row in cursor.fetchall()]

        cursor.execute(
            """
            SELECT topic_key, question, severity, blocking, owner_role, state,
                   source_question_keys
              FROM discovery.open_questions
             WHERE run_id = %s AND superseded_at IS NULL
          ORDER BY blocking DESC, severity, topic_key
            """,
            (run_id,),
        )
        open_questions = [dict(row) for row in cursor.fetchall()]

    return {
        "facts": facts,
        "requirements": requirements,
        "openQuestions": open_questions,
        # Blocking items prevent discovery approval (Discovery §16.4). Reported
        # here so the gate does not have to re-derive the rule.
        "blockingCount": sum(1 for item in open_questions if item["blocking"] and item["state"] == "open"),
    }


class ApprovalBlocked(Exception):
    """Discovery cannot be approved yet. Carries every reason, not the first.

    A gate that reports one blocker at a time turns a review into a queue of
    round trips; the consultant should see the whole list once.
    """

    def __init__(self, reasons: list[dict[str, Any]]) -> None:
        super().__init__(f"{len(reasons)} blocker(s)")
        self.reasons = reasons


def readiness(*, tenant_id: str, user_id: str, run_id: str) -> dict[str, Any]:
    """Whether an approved discovery version could be created right now."""
    plan = question_plan(tenant_id=tenant_id, user_id=user_id, run_id=run_id, locale="en_US")
    view = derived_view(tenant_id=tenant_id, user_id=user_id, run_id=run_id)

    reasons: list[dict[str, Any]] = []

    outstanding = plan["progress"]["outstandingRequired"]
    if outstanding:
        reasons.append({
            "reason": "outstanding_required_questions",
            "questionKeys": outstanding,
        })

    blocking = [
        item for item in view["openQuestions"]
        if item["blocking"] and item["state"] == "open"
    ]
    if blocking:
        # Discovery §16.4: no blocking item may remain. This is why open
        # questions carry `blocking` as a property rather than the gate
        # deciding severity for itself at approval time.
        reasons.append({
            "reason": "blocking_open_questions",
            "topics": [item["topic_key"] for item in blocking],
        })

    red = [item for item in view["requirements"] if item["confidence"] == "red"]
    if red:
        reasons.append({
            "reason": "red_confidence_requirements",
            "requirements": [item["requirement_ref"] for item in red],
        })

    return {
        "ready": not reasons,
        "reasons": reasons,
        "answered": plan["progress"]["answered"],
        "applicable": plan["progress"]["applicable"],
    }


def approve(*, tenant_id: str, user_id: str, actor_role: str, run_id: str) -> dict[str, Any]:
    """Create an immutable approved discovery version.

    The snapshot holds the answers as given plus everything derived from them,
    and its digest is computed with the shared canonicalizer, so anyone holding
    the snapshot can recompute the hash in either language and confirm nothing
    changed (ADR-015).
    """
    state = readiness(tenant_id=tenant_id, user_id=user_id, run_id=run_id)
    if not state["ready"]:
        raise ApprovalBlocked(state["reasons"])

    run = _run(tenant_id, user_id, run_id)
    answers = current_answers(tenant_id=tenant_id, user_id=user_id, run_id=run_id)
    view = derived_view(tenant_id=tenant_id, user_id=user_id, run_id=run_id)

    with db.transaction(tenant_id=tenant_id, user_id=user_id) as cursor:
        cursor.execute(
            """
            SELECT coalesce(max(version), 0) + 1 AS next
              FROM discovery.discovery_versions
             WHERE workspace_id = %s
            """,
            (run["workspace_id"],),
        )
        version = cursor.fetchone()["next"]

        cursor.execute(
            """
            SELECT question_key, raw_value, answer_source, confidence, answered_by, created_at
              FROM discovery.answers
             WHERE run_id = %s AND superseded_at IS NULL
          ORDER BY question_key
            """,
            (run_id,),
        )
        answer_rows = [
            {
                "questionKey": row["question_key"],
                "value": row["raw_value"],
                "source": row["answer_source"],
                "confidence": row["confidence"],
                "answeredBy": row["answered_by"],
                # Timestamps are RFC 3339 in the snapshot, so the digest does
                # not depend on how a driver renders a datetime.
                "answeredAt": row["created_at"].isoformat(),
            }
            for row in cursor.fetchall()
        ]

        content = {
            "kind": "DiscoveryPackage",
            "schemaVersion": "1.0.0",
            "workspaceId": run["workspace_id"],
            "runId": run_id,
            "mode": run["mode"],
            "definitionVersion": run["version"],
            "answers": answer_rows,
            "facts": view["facts"],
            "requirements": view["requirements"],
            "openQuestions": view["openQuestions"],
        }
        content_digest = digest(content)

        # Re-approving is how a corrected answer reaches the Blueprint Engine:
        # a new version, never an edit of the approved one (Constitution §7.6).
        # Identical content produces no version, because a version that records
        # no change is noise in the history a customer later reads.
        cursor.execute(
            """
            SELECT version, content_digest FROM discovery.discovery_versions
             WHERE workspace_id = %s
          ORDER BY version DESC LIMIT 1
            """,
            (run["workspace_id"],),
        )
        previous = cursor.fetchone()
        if previous is not None and previous["content_digest"] == content_digest:
            raise DiscoveryError(
                f"discovery version {previous['version']} already records this content; "
                "nothing has changed since it was approved"
            )

        version_id = new_id("dsv")
        cursor.execute(
            """
            INSERT INTO discovery.discovery_versions
              (id, tenant_id, workspace_id, run_id, version, content, content_digest,
               definition_key, definition_version, approved_by, approved_role)
            VALUES (%s, %s, %s, %s, %s, %s::jsonb, %s, %s, %s, %s, %s)
         RETURNING id, version, content_digest, approved_at
            """,
            (
                version_id, tenant_id, run["workspace_id"], run_id, version,
                json.dumps(content, ensure_ascii=False), content_digest,
                "quick_start", run["version"], user_id, actor_role,
            ),
        )
        row = cursor.fetchone()

        cursor.execute(
            """
            UPDATE discovery.interview_runs
               SET state = 'approved_for_blueprint', completed_at = now()
             WHERE id = %s
            """,
            (run_id,),
        )

    return dict(row)


def approved_versions(*, tenant_id: str, user_id: str, workspace_id: str) -> list[dict[str, Any]]:
    with db.transaction(tenant_id=tenant_id, user_id=user_id) as cursor:
        cursor.execute(
            """
            SELECT id, version, content_digest, definition_version,
                   approved_by, approved_role, approved_at
              FROM discovery.discovery_versions
             WHERE workspace_id = %s
          ORDER BY version DESC
            """,
            (workspace_id,),
        )
        return [dict(row) for row in cursor.fetchall()]


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

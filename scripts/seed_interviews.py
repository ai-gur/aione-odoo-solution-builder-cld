#!/usr/bin/env python
"""Load versioned interview definitions.

Definitions are content, not schema, so they load through a seed rather than a
migration. Loading is idempotent by (definition_key, version): re-running
changes nothing.

A published version is immutable. Editing questions means publishing a new
version, because a workspace pins the version it started with and a customer's
history must not change because the questionnaire improved (Portfolio §5).

Rules are validated here, at load time. A typo in an applicability rule fails
the seed rather than silently hiding a question from a customer months later.

    python scripts/seed_interviews.py [path.json ...]
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "apps" / "domain-api"))

from aione_domain.rules import RuleError, validate  # noqa: E402
from scripts.db import psql  # noqa: E402

SEED_DIR = ROOT / "database" / "seeds"


def canonical_digest(document: dict) -> str:
    """Digest over the canonical form, using the same construction as every
    other content hash in the platform (ADR-015)."""
    sys.path.insert(0, str(ROOT / "packages" / "contracts" / "python"))
    from aione_contracts import canonical_bytes

    return "sha256:" + hashlib.sha256(canonical_bytes(document)).hexdigest()


def sql_literal(value: str | None) -> str:
    if value is None:
        return "NULL"
    return "'" + value.replace("'", "''") + "'"


def json_literal(value: object) -> str:
    return sql_literal(json.dumps(value, ensure_ascii=False)) + "::jsonb"


def load(path: pathlib.Path) -> None:
    document = json.loads(path.read_text(encoding="utf-8"))
    key = document["definitionKey"]
    version = int(document["version"])
    questions = document["questions"]

    known = {question["questionKey"] for question in questions}
    for question in questions:
        rule = question.get("applicability", {"always": True})
        try:
            validate(rule, known)
        except RuleError as error:
            raise SystemExit(f"{path.name}: {question['questionKey']}: {error}") from error

    existing = psql(
        "SELECT id FROM discovery.interview_definitions "
        f"WHERE definition_key = {sql_literal(key)} AND version = {version};"
    )
    if existing:
        print(f"{key} v{version} already loaded ({existing})")
        return

    digest = canonical_digest(document)
    definition_id = "idf_" + hashlib.sha256(f"{key}:{version}".encode()).hexdigest()[:26].upper()

    statements = [
        "BEGIN;",
        f"""INSERT INTO discovery.interview_definitions
              (id, definition_key, version, mode, title, status, content_digest, published_at)
            VALUES ({sql_literal(definition_id)}, {sql_literal(key)}, {version},
                    {sql_literal(document['mode'])}, {json_literal(document['title'])},
                    'published', {sql_literal(digest)}, now());""",
    ]

    for index, question in enumerate(questions):
        question_id = (
            "qdf_"
            + hashlib.sha256(f"{key}:{version}:{question['questionKey']}".encode())
            .hexdigest()[:26]
            .upper()
        )
        statements.append(
            f"""INSERT INTO discovery.question_definitions
                  (id, definition_id, question_key, order_index, domain, concept, prompt,
                   help_text, answer_type, options, applicability, required_policy,
                   risk_weight, complexity_weight, evidence_policy)
                VALUES ({sql_literal(question_id)}, {sql_literal(definition_id)},
                        {sql_literal(question['questionKey'])}, {index},
                        {sql_literal(question['domain'])}, {sql_literal(question.get('concept'))},
                        {json_literal(question['prompt'])},
                        {json_literal(question.get('helpText', {}))},
                        {sql_literal(question['answerType'])},
                        {json_literal(question.get('options', []))},
                        {json_literal(question.get('applicability', {'always': True}))},
                        {sql_literal(question.get('requiredPolicy', 'optional'))},
                        {int(question.get('riskWeight', 0))},
                        {int(question.get('complexityWeight', 0))},
                        {sql_literal(question.get('evidencePolicy', 'optional'))});"""
        )

    statements.append("COMMIT;")
    psql("\n".join(statements))
    print(f"loaded {key} v{version}: {len(questions)} questions, {digest[:23]}…")


if __name__ == "__main__":
    paths = [pathlib.Path(arg) for arg in sys.argv[1:]] or sorted(SEED_DIR.glob("interview-*.json"))
    if not paths:
        raise SystemExit("no interview seed files found")
    for path in paths:
        load(path)

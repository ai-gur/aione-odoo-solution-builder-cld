#!/usr/bin/env python
"""Load a capability set into the control database.

Idempotent by content digest: loading the same file twice changes nothing, and
an edited file becomes a new set rather than mutating the one blueprints
already reference.

    python scripts/run.py catalogue-load
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "packages" / "contracts" / "python"))

from aione_contracts import canonical_bytes  # noqa: E402
from localenv import load as load_local_env  # noqa: E402
from scripts.db import psql  # noqa: E402

load_local_env()

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CAPABILITIES = ROOT / "catalogue" / "capabilities"


def literal(value) -> str:
    if value is None:
        return "NULL"
    return "'" + str(value).replace("'", "''") + "'"


def json_literal(value) -> str:
    return literal(json.dumps(value, ensure_ascii=False)) + "::jsonb"


def array_literal(values: list[str]) -> str:
    if not values:
        return "'{}'::text[]"
    inner = ",".join(literal(v) for v in values)
    return f"ARRAY[{inner}]::text[]"


def load(path: pathlib.Path) -> None:
    document = json.loads(path.read_text(encoding="utf-8"))
    digest = "sha256:" + hashlib.sha256(canonical_bytes(document)).hexdigest()
    set_id = "cps_" + hashlib.sha256(digest.encode()).hexdigest()[:26].upper()

    existing = psql(
        f"SELECT id FROM catalogue.capability_sets WHERE content_digest = {literal(digest)};"
    )
    if existing:
        print(f"{document['scopeKey']} already loaded ({existing})")
        return

    statements = [
        "BEGIN;",
        f"""INSERT INTO catalogue.capability_sets (id, scope_key, baseline_key, content_digest)
            VALUES ({literal(set_id)}, {literal(document['scopeKey'])},
                    {literal(document['baselineKey'])}, {literal(digest)});""",
    ]

    for capability in document["capabilities"]:
        capability_id = "cap_" + hashlib.sha256(
            f"{set_id}:{capability['capabilityKey']}".encode()
        ).hexdigest()[:26].upper()
        # Who confirmed this against the pinned revision, and when. A verified
        # row that names nobody is rejected by the database (migration 0010),
        # so a file that flips status without recording the review fails here
        # rather than producing a green assessment nobody stands behind.
        verification = capability.get("verification") or {}
        statements.append(
            f"""INSERT INTO catalogue.capabilities
                  (id, set_id, capability_key, domain, description, addresses_topics, modules,
                   edition, coverage, activation, security_surfaces, evidence, limitations,
                   residual_gap, status, verified_by, verified_role, verified_on,
                   verification_note)
                VALUES ({literal(capability_id)}, {literal(set_id)},
                        {literal(capability['capabilityKey'])}, {literal(capability['domain'])},
                        {json_literal(capability['description'])},
                        {array_literal(capability.get('addressesTopics', []))},
                        {array_literal(capability.get('modules', []))},
                        {literal(capability.get('edition', 'community'))},
                        {literal(capability.get('coverage', 'full'))},
                        {json_literal(capability.get('activation', {}))},
                        {array_literal(capability.get('securitySurfaces', []))},
                        {json_literal(capability.get('evidence', []))},
                        {json_literal(capability.get('limitations', []))},
                        {literal(capability.get('residualGap'))},
                        {literal(capability.get('status', 'draft'))},
                        {literal(verification.get('reviewer'))},
                        {literal(verification.get('role'))},
                        {literal(verification.get('date'))},
                        {literal(verification.get('note'))});"""
        )

    for unresolved in document.get("unresolvedTopics", []):
        unresolved_id = "unr_" + hashlib.sha256(
            f"{set_id}:{unresolved['topic']}".encode()
        ).hexdigest()[:26].upper()
        statements.append(
            f"""INSERT INTO catalogue.unresolved_topics
                  (id, set_id, topic, finding, reason, candidates, treatment)
                VALUES ({literal(unresolved_id)}, {literal(set_id)},
                        {literal(unresolved['topic'])}, {literal(unresolved.get('finding'))},
                        {literal(unresolved['reason'])},
                        {json_literal(unresolved.get('candidatesRequiringVerification', []))},
                        {literal(unresolved.get('treatment'))});"""
        )

    for decision in document.get("topicDecisions", []):
        decision_id = "tdc_" + hashlib.sha256(
            f"{set_id}:{decision['topic']}".encode()
        ).hexdigest()[:26].upper()
        statements.append(
            f"""INSERT INTO catalogue.topic_decisions
                  (id, set_id, topic, preferred_capability_key, reason, decided_by,
                   decided_role, decided_on, alternative_note)
                VALUES ({literal(decision_id)}, {literal(set_id)},
                        {literal(decision['topic'])},
                        {literal(decision['preferredCapabilityKey'])},
                        {literal(decision['reason'])}, {literal(decision['decidedBy'])},
                        {literal(decision.get('role'))}, {literal(decision['date'])},
                        {literal(decision.get('alternativeNote'))});"""
        )

    statements.append("COMMIT;")
    psql("\n".join(statements))

    verified = sum(1 for c in document["capabilities"] if c.get("status") == "verified")
    print(
        f"loaded {document['scopeKey']}: {len(document['capabilities'])} capabilities "
        f"({verified} verified, {len(document['capabilities']) - verified} draft), "
        f"{len(document.get('unresolvedTopics', []))} unresolved topic(s)"
    )
    print(f"  digest {digest[:23]}…")


if __name__ == "__main__":
    paths = [pathlib.Path(a) for a in sys.argv[1:]] or sorted(CAPABILITIES.glob("*.json"))
    if not paths:
        raise SystemExit("no capability files found")
    for path in paths:
        load(path)

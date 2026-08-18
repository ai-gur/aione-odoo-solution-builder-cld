"""Blueprint generation: requirements to Odoo capabilities.

Reads an approved discovery version and nothing else (Blueprint §2), maps each
requirement to catalogue capabilities, and records a fit assessment with its
rationale and the alternatives that were rejected.

The mapping is deterministic and evidence-bound:

- Requirements join to capabilities on an explicit **topic**, not on keyword
  similarity. Similarity may suggest candidates; it may never establish fit
  (Blueprint §9.1).
- A topic with no capability produces `unresolved` with the catalogue's
  recorded reason — never a guess at which module might do it. This is the
  behaviour Blueprint §27 describes: a sound design direction that refuses to
  invent Odoo internals.
- A capability marked `partial` produces `partial_fit` and a residual gap,
  because a partial fit that records no gap silently loses the unmet part.
- A capability still in `draft` lowers the confidence of the assessment. Draft
  catalogue content may inform a blueprint; it may not carry one to approval.
"""

from __future__ import annotations

import json
import secrets
from typing import Any

from . import db

VERSION = "blueprint_v1"


class BlueprintError(Exception):
    """The blueprint cannot be generated from the state given."""


def new_id(prefix: str) -> str:
    return f"{prefix}_" + secrets.token_hex(13).upper()


def _capability_set(cursor, baseline_key: str, scope_key: str | None = None) -> dict[str, Any]:
    cursor.execute(
        """
        SELECT id, scope_key, baseline_key, content_digest
          FROM catalogue.capability_sets
         WHERE baseline_key = %s AND (%s::text IS NULL OR scope_key = %s)
      ORDER BY loaded_at DESC
         LIMIT 1
        """,
        (baseline_key, scope_key, scope_key),
    )
    row = cursor.fetchone()
    if row is None:
        raise BlueprintError(f"no capability set loaded for baseline {baseline_key}")
    return dict(row)


def _capabilities(cursor, set_id: str) -> list[dict[str, Any]]:
    cursor.execute(
        """
        SELECT capability_key, domain, description, addresses_topics, modules, edition,
               coverage, activation, security_surfaces, evidence, limitations,
               residual_gap, status, verified_by, verified_on
          FROM catalogue.capabilities
         WHERE set_id = %s
      ORDER BY capability_key
        """,
        (set_id,),
    )
    return [dict(row) for row in cursor.fetchall()]


def _unresolved(cursor, set_id: str) -> dict[str, dict[str, Any]]:
    cursor.execute(
        "SELECT topic, finding, reason, candidates, treatment "
        "FROM catalogue.unresolved_topics WHERE set_id = %s",
        (set_id,),
    )
    return {row["topic"]: dict(row) for row in cursor.fetchall()}


def classify(
    requirement: dict[str, Any],
    candidates: list[dict[str, Any]],
    unresolved: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Decide the fit for one requirement. Pure, so it is testable alone."""
    topic = requirement.get("topic") or ""

    if not candidates:
        note = unresolved.get(topic)
        return {
            "classification": "unresolved",
            "capability_key": None,
            "modules": [],
            "confidence": "red",
            "rationale": {
                "en_US": (
                    note["reason"] if note else
                    f"No capability in this catalogue addresses {topic}."
                ),
                "he_IL": (
                    "אין יכולת מאומתת בקטלוג שמכסה נושא זה; נדרשת הכרעה מקצועית."
                ),
            },
            # Candidates that need verification are carried through, so a
            # reviewer sees what was considered rather than starting again.
            "alternatives": (note or {}).get("candidates", []),
            "residual_gap": (note or {}).get(
                "treatment", f"{topic} is not satisfied by the current catalogue."
            ),
        }

    # Prefer a verified capability over a draft, and full coverage over partial.
    ranked = sorted(
        candidates,
        key=lambda c: (c["status"] != "verified", c["coverage"] != "full", c["capability_key"]),
    )
    chosen = ranked[0]

    def rank_key(capability: dict[str, Any]) -> tuple[bool, bool]:
        return (capability["status"] != "verified", capability["coverage"] != "full")

    # Two capabilities the evidence ranks equally are a consulting decision,
    # not a sort order. Odoo often offers a second way to do something — a
    # purchase threshold on the order, or an approval request the order is
    # created from — and which one suits a business is not a property of the
    # catalogue. Picking alphabetically and calling it green would hide that.
    contested = [
        other for other in ranked[1:] if rank_key(other) == rank_key(chosen)
    ]
    rejected = [
        {
            "capabilityKey": other["capability_key"],
            "reason": (
                "equally ranked; the choice between them is a consulting decision"
                if other in contested
                else "lower coverage" if other["coverage"] != chosen["coverage"]
                else "draft, where the selected capability is verified"
            ),
        }
        for other in ranked[1:]
    ]

    activation = chosen["activation"] or {}
    needs_configuration = bool(activation.get("settingField"))

    if chosen["coverage"] == "partial":
        classification = "partial_fit"
    elif chosen["domain"] == "FIN" and "l10n_il" in (chosen["modules"] or []):
        classification = "localization_fit"
    elif needs_configuration:
        classification = "configuration_fit"
    else:
        classification = "standard_fit"

    # A draft capability cannot support a green assessment: the claim it rests
    # on has not been reviewed by anyone who knows Odoo.
    confidence = "green" if chosen["status"] == "verified" else "amber"
    if chosen["coverage"] == "partial" or contested:
        confidence = "amber"

    rationale_en = (
        f"{chosen['description'].get('en_US', '')} "
        f"Implemented by {', '.join(chosen['modules'])}."
    )
    if needs_configuration:
        rationale_en += f" Activated through the {activation['settingField']} setting."
    if contested:
        others = ", ".join(other["capability_key"] for other in contested)
        rationale_en += (
            f" {len(contested) + 1} capabilities address this requirement equally well"
            f" ({others} is the alternative); which one suits this business is a"
            " decision for the review."
        )
    if chosen["status"] != "verified":
        rationale_en += " Catalogue entry is draft and needs functional verification."
    elif chosen.get("verified_by"):
        # A green assessment rests on a person's review, so the assessment
        # names them. The record is immutable, so it keeps naming them even
        # after a later catalogue release replaces the capability.
        rationale_en += (
            f" Catalogue entry verified by {chosen['verified_by']}"
            f" on {chosen['verified_on']}."
        )

    return {
        "classification": classification,
        "capability_key": chosen["capability_key"],
        "modules": chosen["modules"],
        "confidence": confidence,
        "rationale": {
            "en_US": rationale_en.strip(),
            "he_IL": chosen["description"].get("he_IL", ""),
        },
        "alternatives": rejected,
        # A partial fit that records no gap silently loses the unmet part.
        "residual_gap": chosen["residual_gap"] if chosen["coverage"] == "partial" else None,
    }


def generate(*, tenant_id: str, user_id: str, workspace_id: str) -> dict[str, Any]:
    """Generate a blueprint from the workspace's latest approved discovery."""
    with db.transaction(tenant_id=tenant_id, user_id=user_id) as cursor:
        cursor.execute(
            """
            SELECT id, version, content, content_digest
              FROM discovery.discovery_versions
             WHERE workspace_id = %s
          ORDER BY version DESC
             LIMIT 1
            """,
            (workspace_id,),
        )
        discovery_version = cursor.fetchone()
        if discovery_version is None:
            # Blueprint §2: the engine consumes an approved version only.
            raise BlueprintError(
                "this workspace has no approved discovery version; "
                "a blueprint may only be generated from one"
            )

        content = discovery_version["content"]
        requirements = content.get("requirements", [])

        # The baseline the catalogue was built from. A blueprint records it so
        # a later manifest pins the same source revisions (ADR-007).
        baseline_key = content.get("baselineKey", "odoo19-baseline-2026-08-17")

        capability_set = _capability_set(cursor, baseline_key)
        capabilities = _capabilities(cursor, capability_set["id"])
        unresolved = _unresolved(cursor, capability_set["id"])

        by_topic: dict[str, list[dict[str, Any]]] = {}
        for capability in capabilities:
            for topic in capability["addresses_topics"]:
                by_topic.setdefault(topic, []).append(capability)

        cursor.execute(
            "SELECT coalesce(max(version), 0) + 1 AS next FROM app.blueprints WHERE workspace_id = %s",
            (workspace_id,),
        )
        version = cursor.fetchone()["next"]

        blueprint_id = new_id("bp")
        cursor.execute(
            """
            INSERT INTO app.blueprints
              (id, tenant_id, workspace_id, version, discovery_version_id, capability_set_id,
               baseline_key, generator_version, created_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
         RETURNING id, version, state, created_at
            """,
            (blueprint_id, tenant_id, workspace_id, version, discovery_version["id"],
             capability_set["id"], baseline_key, VERSION, user_id),
        )
        blueprint = dict(cursor.fetchone())

        assessments = []
        selected_modules: dict[str, set[str]] = {}

        for requirement in requirements:
            topic = requirement.get("topic") or ""
            decision = classify(requirement, by_topic.get(topic, []), unresolved)
            assessments.append({**decision, "requirement_ref": requirement["requirement_ref"],
                                "topic": topic})

            cursor.execute(
                """
                INSERT INTO app.fit_assessments
                  (id, tenant_id, blueprint_id, requirement_ref, topic, classification,
                   capability_key, modules, rationale, alternatives, confidence, residual_gap)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb, %s, %s)
                """,
                (
                    new_id("fit"), tenant_id, blueprint_id, requirement["requirement_ref"],
                    topic, decision["classification"], decision["capability_key"],
                    decision["modules"], json.dumps(decision["rationale"], ensure_ascii=False),
                    json.dumps(decision["alternatives"], ensure_ascii=False),
                    decision["confidence"], decision["residual_gap"],
                ),
            )

            for module in decision["modules"]:
                selected_modules.setdefault(module, set()).add(requirement["requirement_ref"])

        for module, justified_by in sorted(selected_modules.items()):
            cursor.execute(
                """
                INSERT INTO app.blueprint_modules
                  (id, tenant_id, blueprint_id, technical_name, inclusion, justified_by)
                VALUES (%s, %s, %s, %s, 'business_selected', %s)
                ON CONFLICT (blueprint_id, technical_name) DO NOTHING
                """,
                (new_id("bpm"), tenant_id, blueprint_id, module, sorted(justified_by)),
            )

    return {
        **blueprint,
        "discoveryVersion": discovery_version["version"],
        "capabilitySetDigest": capability_set["content_digest"],
        "assessments": assessments,
        "summary": summarise(assessments),
    }


def summarise(assessments: list[dict[str, Any]]) -> dict[str, Any]:
    counts: dict[str, int] = {}
    for assessment in assessments:
        counts[assessment["classification"]] = counts.get(assessment["classification"], 0) + 1
    return {
        "requirements": len(assessments),
        "byClassification": counts,
        "unresolved": counts.get("unresolved", 0),
        "gaps": [a["requirement_ref"] for a in assessments if a["residual_gap"]],
        # Every Must requirement needs a fit or an explicit blocker
        # (Blueprint §30.3). Reported so a review gate does not have to
        # recompute it.
        "readyForReview": counts.get("unresolved", 0) == 0,
    }


def read(*, tenant_id: str, user_id: str, blueprint_id: str) -> dict[str, Any]:
    with db.transaction(tenant_id=tenant_id, user_id=user_id) as cursor:
        cursor.execute(
            """
            SELECT b.id, b.version, b.state, b.baseline_key, b.created_at,
                   d.version AS discovery_version, d.content_digest AS discovery_digest
              FROM app.blueprints b
              JOIN discovery.discovery_versions d ON d.id = b.discovery_version_id
             WHERE b.id = %s
            """,
            (blueprint_id,),
        )
        blueprint = cursor.fetchone()
        if blueprint is None:
            raise BlueprintError("blueprint not found")

        cursor.execute(
            """
            SELECT requirement_ref, topic, classification, capability_key, modules,
                   rationale, alternatives, confidence, residual_gap
              FROM app.fit_assessments
             WHERE blueprint_id = %s
          ORDER BY requirement_ref
            """,
            (blueprint_id,),
        )
        assessments = [dict(row) for row in cursor.fetchall()]

        cursor.execute(
            """
            SELECT technical_name, inclusion, justified_by, runs_hooks
              FROM app.blueprint_modules
             WHERE blueprint_id = %s
          ORDER BY technical_name
            """,
            (blueprint_id,),
        )
        modules = [dict(row) for row in cursor.fetchall()]

    return {
        **dict(blueprint),
        "assessments": assessments,
        "modules": modules,
        "summary": summarise(assessments),
    }


def list_for_workspace(*, tenant_id: str, user_id: str, workspace_id: str) -> list[dict[str, Any]]:
    with db.transaction(tenant_id=tenant_id, user_id=user_id) as cursor:
        cursor.execute(
            """
            SELECT id, version, state, baseline_key, created_at
              FROM app.blueprints
             WHERE workspace_id = %s
          ORDER BY version DESC
            """,
            (workspace_id,),
        )
        return [dict(row) for row in cursor.fetchall()]

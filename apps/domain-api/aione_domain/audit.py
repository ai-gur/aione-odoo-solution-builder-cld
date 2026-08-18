"""Append-only audit events (ADR-011).

Audit is not logging. Logs exist to debug a failure; audit events exist to
prove who authorized what against which version. They are written through this
module only, and the database grants make them impossible to amend afterwards —
the integration suite proves the API's own role cannot UPDATE or DELETE them.

Denials are recorded as well as successes. An attempt to reach another tenant's
data is exactly the event an investigation needs, and it is the one most easily
lost by only writing the happy path.
"""

from __future__ import annotations

import json
import secrets
from typing import Any, Literal

from . import db

Outcome = Literal["succeeded", "denied", "failed"]

# Keys never written into an audit detail payload, whatever the caller passes.
_FORBIDDEN_DETAIL_KEYS = frozenset(
    {"password", "token", "secret", "authorization", "api_key", "credential"}
)


def new_event_id() -> str:
    # A ULID generator arrives with the shared identifier utility; until then
    # the shape is right and the value is unique and unguessable.
    return "evt_" + secrets.token_hex(13).upper()


def _sanitise(detail: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in detail.items()
        if key.lower() not in _FORBIDDEN_DETAIL_KEYS
    }


def record(
    *,
    tenant_id: str,
    action: str,
    correlation_id: str,
    outcome: Outcome,
    actor_id: str | None = None,
    actor_role: str | None = None,
    subject_type: str | None = None,
    subject_id: str | None = None,
    subject_version: str | None = None,
    detail: dict[str, Any] | None = None,
) -> str:
    """Append one event and return its identifier."""
    event_id = new_event_id()
    payload = json.dumps(_sanitise(detail or {}), ensure_ascii=False)

    with db.transaction(tenant_id=tenant_id) as cursor:
        cursor.execute(
            """
            INSERT INTO audit.events
              (id, tenant_id, actor_id, actor_role, action, subject_type,
               subject_id, subject_version, correlation_id, outcome, detail)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb)
            """,
            (
                event_id,
                tenant_id,
                actor_id,
                actor_role,
                action,
                subject_type,
                subject_id,
                subject_version,
                correlation_id,
                outcome,
                payload,
            ),
        )
    return event_id

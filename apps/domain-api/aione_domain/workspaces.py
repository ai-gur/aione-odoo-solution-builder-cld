"""Customer organizations and solution workspaces.

The Solution Workspace is where a customer's engagement lives: discovery,
requirements, blueprints, manifests, environments and approvals all attach to
it (Constitution §7.1 as amended by Option A, ADR-013).

State transitions are guarded here rather than left to whoever writes the next
route. `ENUMS.md` names the states; this module names which moves are legal
between them, and refuses the rest.
"""

from __future__ import annotations

import secrets
from typing import Any

from . import db

# Legal transitions. Anything absent is refused — an unlisted move is a bug or
# an attempt, and both should fail loudly rather than quietly succeed.
TRANSITIONS: dict[str, frozenset[str]] = {
    "proposed": frozenset({"discovering", "closed", "suspended"}),
    "discovering": frozenset({"clarification_required", "designing", "suspended", "closed"}),
    "clarification_required": frozenset({"discovering", "designing", "suspended", "closed"}),
    "designing": frozenset({"blueprint_review", "clarification_required", "suspended", "closed"}),
    "blueprint_review": frozenset({"approved_for_sandbox", "revision_required", "designing", "suspended"}),
    "approved_for_sandbox": frozenset({"provisioning", "revision_required", "suspended"}),
    "provisioning": frozenset({"sandbox_active", "validation_failed", "suspended"}),
    "validation_failed": frozenset({"provisioning", "revision_required", "suspended", "closed"}),
    "sandbox_active": frozenset({"customer_review", "revision_required", "provisioning", "suspended"}),
    "customer_review": frozenset({"accepted", "revision_required", "suspended"}),
    "revision_required": frozenset({"discovering", "designing", "suspended", "closed"}),
    "accepted": frozenset({"operating", "change_in_progress", "suspended", "archived"}),
    "operating": frozenset({"change_in_progress", "suspended", "archived", "closed"}),
    "change_in_progress": frozenset({"operating", "designing", "suspended"}),
    "suspended": frozenset({"discovering", "designing", "operating", "closed", "archived"}),
    "archived": frozenset({"closed"}),
    "closed": frozenset(),
}


class TransitionError(Exception):
    def __init__(self, current: str, requested: str) -> None:
        super().__init__(f"cannot move a workspace from {current} to {requested}")
        self.current = current
        self.requested = requested


class ConflictError(Exception):
    """A uniqueness rule would be violated."""


def new_id(prefix: str) -> str:
    return f"{prefix}_" + secrets.token_hex(13).upper()


def create_customer(
    *, tenant_id: str, user_id: str, legal_name: str, customer_code: str,
    trading_name: str | None = None, countries: list[str] | None = None,
) -> dict[str, Any]:
    customer_id = new_id("cus")
    with db.transaction(tenant_id=tenant_id, user_id=user_id) as cursor:
        cursor.execute(
            """
            INSERT INTO app.customer_organizations
              (id, tenant_id, legal_name, trading_name, customer_code, countries)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (tenant_id, customer_code) DO NOTHING
            RETURNING id, legal_name, trading_name, customer_code, countries, status, created_at
            """,
            (customer_id, tenant_id, legal_name, trading_name, customer_code,
             countries or ["IL"]),
        )
        row = cursor.fetchone()
        if row is None:
            raise ConflictError(f"customer_code {customer_code} already exists in this tenant")
    return dict(row)


def list_customers(*, tenant_id: str, user_id: str) -> list[dict[str, Any]]:
    with db.transaction(tenant_id=tenant_id, user_id=user_id) as cursor:
        cursor.execute(
            """
            SELECT c.id, c.legal_name, c.trading_name, c.customer_code, c.status,
                   c.countries, c.created_at,
                   count(w.id) AS workspace_count
              FROM app.customer_organizations c
         LEFT JOIN app.solution_workspaces w ON w.customer_id = c.id
          GROUP BY c.id
          ORDER BY c.legal_name
            """
        )
        return [dict(row) for row in cursor.fetchall()]


def create_workspace(
    *, tenant_id: str, user_id: str, actor_role: str, customer_id: str, name: str,
    business_scope: str | None = None, primary_locale: str = "he_IL",
    discovery_mode: str | None = None,
) -> dict[str, Any]:
    workspace_id = new_id("wsp")
    with db.transaction(tenant_id=tenant_id, user_id=user_id) as cursor:
        cursor.execute(
            "SELECT id FROM app.customer_organizations WHERE id = %s", (customer_id,)
        )
        if cursor.fetchone() is None:
            # Either it does not exist or it belongs to another tenant. The
            # caller learns the same thing in both cases, deliberately.
            raise ConflictError("customer not found")

        cursor.execute(
            """
            INSERT INTO app.solution_workspaces
              (id, tenant_id, customer_id, name, business_scope, primary_locale, discovery_mode)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (tenant_id, customer_id, name) DO NOTHING
            RETURNING id, customer_id, name, state, primary_locale, discovery_mode, created_at
            """,
            (workspace_id, tenant_id, customer_id, name, business_scope,
             primary_locale, discovery_mode),
        )
        row = cursor.fetchone()
        if row is None:
            raise ConflictError(f"a workspace named {name} already exists for this customer")

        cursor.execute(
            """
            INSERT INTO app.workspace_state_history
              (tenant_id, workspace_id, from_state, to_state, actor_id, actor_role, reason)
            VALUES (%s, %s, NULL, 'proposed', %s, %s, 'created')
            """,
            (tenant_id, workspace_id, user_id, actor_role),
        )
    return dict(row)


def list_workspaces(*, tenant_id: str, user_id: str, customer_id: str | None = None) -> list[dict[str, Any]]:
    with db.transaction(tenant_id=tenant_id, user_id=user_id) as cursor:
        cursor.execute(
            """
            SELECT w.id, w.customer_id, c.legal_name AS customer_name, w.name, w.state,
                   w.primary_locale, w.discovery_mode, w.current_baseline_id, w.created_at,
                   count(m.id) AS member_count
              FROM app.solution_workspaces w
              JOIN app.customer_organizations c ON c.id = w.customer_id
         LEFT JOIN app.workspace_members m ON m.workspace_id = w.id
             WHERE (%s::text IS NULL OR w.customer_id = %s)
          GROUP BY w.id, c.legal_name
          ORDER BY w.created_at DESC
            """,
            (customer_id, customer_id),
        )
        return [dict(row) for row in cursor.fetchall()]


def transition(
    *, tenant_id: str, user_id: str, actor_role: str, workspace_id: str,
    to_state: str, reason: str | None = None,
) -> dict[str, Any]:
    """Move a workspace to a new state, or refuse."""
    with db.transaction(tenant_id=tenant_id, user_id=user_id) as cursor:
        # Locked for the duration, so two concurrent transitions cannot both
        # read the same current state and both consider themselves legal.
        cursor.execute(
            "SELECT id, state FROM app.solution_workspaces WHERE id = %s FOR UPDATE",
            (workspace_id,),
        )
        workspace = cursor.fetchone()
        if workspace is None:
            raise ConflictError("workspace not found")

        current = workspace["state"]
        if to_state not in TRANSITIONS.get(current, frozenset()):
            raise TransitionError(current, to_state)

        cursor.execute(
            """
            UPDATE app.solution_workspaces
               SET state = %s, updated_at = now()
             WHERE id = %s
         RETURNING id, name, state, updated_at
            """,
            (to_state, workspace_id),
        )
        row = cursor.fetchone()

        cursor.execute(
            """
            INSERT INTO app.workspace_state_history
              (tenant_id, workspace_id, from_state, to_state, actor_id, actor_role, reason)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (tenant_id, workspace_id, current, to_state, user_id, actor_role, reason),
        )
    return dict(row)


def add_member(
    *, tenant_id: str, user_id: str, workspace_id: str, member_user_id: str, role_key: str,
) -> dict[str, Any]:
    member_id = new_id("wsm")
    with db.transaction(tenant_id=tenant_id, user_id=user_id) as cursor:
        cursor.execute(
            """
            INSERT INTO app.workspace_members (id, tenant_id, workspace_id, user_id, role_key)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (workspace_id, user_id, role_key) DO NOTHING
            RETURNING id, workspace_id, user_id, role_key, created_at
            """,
            (member_id, tenant_id, workspace_id, member_user_id, role_key),
        )
        row = cursor.fetchone()
        if row is None:
            raise ConflictError("member already holds that role in this workspace")
    return dict(row)


def workspace_history(*, tenant_id: str, user_id: str, workspace_id: str) -> list[dict[str, Any]]:
    with db.transaction(tenant_id=tenant_id, user_id=user_id) as cursor:
        cursor.execute(
            """
            SELECT from_state, to_state, actor_id, actor_role, reason, occurred_at
              FROM app.workspace_state_history
             WHERE workspace_id = %s
          ORDER BY occurred_at
            """,
            (workspace_id,),
        )
        return [dict(row) for row in cursor.fetchall()]

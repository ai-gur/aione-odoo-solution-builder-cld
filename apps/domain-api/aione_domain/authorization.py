"""Authority checks.

`docs/20-domain/ROLES-AND-PERMISSIONS.md` defines roles, authorities and the
default mapping between them. This module is that document in executable form,
and it is the only place an authority decision is made — a check written inline
in a route is a check nobody can audit.

Three layers, all required (ADR-014 §Authorization):

1. role — resolved from tenant membership, never from the request;
2. authority — what this role may do;
3. scope — tenant, workspace, and the record's current state.

A denial is an audited event, not a silent 403: an attempt to reach another
customer's engagement is exactly what an investigation needs to find later.
"""

from __future__ import annotations

from dataclasses import dataclass

from .identity import Principal

# Authority → roles that hold it by default. Tenant policy may narrow this;
# nothing may widen it at runtime.
AUTHORITIES: dict[str, frozenset[str]] = {
    "customer.manage": frozenset({"platform_administrator", "account_owner", "solution_owner"}),
    "customer.read": frozenset({
        "platform_administrator", "account_owner", "solution_owner",
        "consultant", "solution_architect", "auditor",
    }),
    "workspace.create": frozenset({"platform_administrator", "account_owner", "solution_owner"}),
    "workspace.read": frozenset({
        "platform_administrator", "account_owner", "solution_owner",
        "consultant", "solution_architect", "provisioning_operator", "auditor",
    }),
    "workspace.manage": frozenset({"platform_administrator", "account_owner", "solution_owner"}),
    "workspace.complete": frozenset({"account_owner"}),
    "membership.manage": frozenset({
        "platform_administrator", "solution_owner", "account_owner",
    }),
    "discovery.conduct": frozenset({"account_owner", "consultant"}),
    "discovery.approve": frozenset({"consultant"}),
}

# Roles a customer may hold. A customer role never holds an AIOne authority,
# and that constraint is not configurable.
CUSTOMER_ROLES = frozenset({
    "customer_sponsor", "customer_process_owner", "customer_technical_contact",
})


class AuthorizationError(Exception):
    """The caller is authenticated but not permitted."""

    def __init__(self, authority: str, reason: str) -> None:
        super().__init__(f"{authority}: {reason}")
        self.authority = authority
        self.reason = reason


@dataclass(frozen=True)
class Decision:
    allowed: bool
    authority: str
    role_used: str | None
    reason: str


def evaluate(principal: Principal, tenant_id: str, authority: str) -> Decision:
    """Decide whether a principal may exercise an authority in a tenant."""
    permitted_roles = AUTHORITIES.get(authority)
    if permitted_roles is None:
        # An unknown authority denies. A typo in a route must not become an
        # unguarded endpoint.
        return Decision(False, authority, None, "unknown_authority")

    held = principal.roles_in(tenant_id)
    if not held:
        return Decision(False, authority, None, "not_a_member")

    if held & CUSTOMER_ROLES and not held - CUSTOMER_ROLES:
        # Customer roles are confined to their own workspace-scoped
        # interactions and hold no AIOne authority.
        return Decision(False, authority, None, "customer_role")

    granted = held & permitted_roles
    if not granted:
        return Decision(False, authority, None, "role_lacks_authority")

    # Record the specific role the action was taken under: approval events must
    # name it (Constitution §5), and "they were an admin" is not an answer.
    return Decision(True, authority, sorted(granted)[0], "granted")


def require(principal: Principal, tenant_id: str, authority: str) -> str:
    """Return the role used, or raise. Callers audit the denial."""
    decision = evaluate(principal, tenant_id, authority)
    if not decision.allowed:
        raise AuthorizationError(authority, decision.reason)
    return decision.role_used or "unknown"

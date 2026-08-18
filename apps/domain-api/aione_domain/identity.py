"""Identity resolution.

The rule this module exists to enforce (ADR-014, story I0-04): the caller
supplies a credential and nothing else. Tenant, workspace and role are read
from the control database using the verified subject. A client-supplied tenant
identifier is ignored — not validated, ignored — because validating it would
imply there are circumstances in which it is trusted.
"""

from __future__ import annotations

from dataclasses import dataclass

from . import db


class AuthenticationError(Exception):
    """The credential is missing, malformed or unverifiable."""


@dataclass(frozen=True)
class Membership:
    tenant_id: str
    tenant_name: str
    role_key: str


@dataclass(frozen=True)
class Principal:
    user_id: str
    auth_subject: str
    email: str
    display_name: str
    memberships: tuple[Membership, ...]

    def tenant_ids(self) -> frozenset[str]:
        return frozenset(m.tenant_id for m in self.memberships)

    def roles_in(self, tenant_id: str) -> frozenset[str]:
        return frozenset(m.role_key for m in self.memberships if m.tenant_id == tenant_id)


def subject_from_authorization(header: str | None, auth_mode: str) -> str:
    """Extract a verified subject from the Authorization header.

    In `dev` mode the bearer value is the subject itself. That is only reachable
    when APP_ENVIRONMENT=local, which config.py enforces at startup.

    In `oidc` mode the token must be verified against the provider's key set —
    signature, issuer, audience, expiry and an algorithm allowlist — before its
    subject may be used. That verifier arrives with the identity provider
    decision; until then the mode refuses rather than accepting anything.
    """
    if not header or not header.lower().startswith("bearer "):
        raise AuthenticationError("missing bearer credential")

    token = header[len("bearer ") :].strip()
    if not token:
        raise AuthenticationError("empty bearer credential")

    if auth_mode == "dev":
        return token

    raise AuthenticationError(
        "oidc verification is not configured; see docs/00-governance/DEFERRED-DECISIONS.md"
    )


def resolve_principal(auth_subject: str) -> Principal:
    """Load the user and their memberships for a verified subject.

    Runs without tenant context: the caller's tenants are what this query
    determines, so it cannot be scoped by them. Instead the transaction carries
    the verified user, and the policies from migration 0002 permit a person to
    read their own memberships in any tenant while still confining everything
    else (ADR-014).
    """
    with db.transaction() as cursor:
        cursor.execute(
            """
            SELECT u.id, u.auth_subject, u.email, u.display_name
            FROM app.users u
            WHERE u.auth_subject = %s
            """,
            (auth_subject,),
        )
        user = cursor.fetchone()
        if user is None:
            raise AuthenticationError("no user for the presented subject")

        # Establish user context, then read. The memberships policy permits
        # own-user rows in any tenant; it permits nothing else.
        cursor.execute("SELECT set_config('app.user_id', %s::text, true)", (user["id"],))
        cursor.execute(
            """
            SELECT m.tenant_id, t.name AS tenant_name, m.role_key
            FROM app.memberships m
            JOIN app.tenants t ON t.id = m.tenant_id
            WHERE m.user_id = %s
            ORDER BY m.tenant_id, m.role_key
            """,
            (user["id"],),
        )
        memberships = tuple(
            Membership(
                tenant_id=row["tenant_id"],
                tenant_name=row["tenant_name"],
                role_key=row["role_key"],
            )
            for row in cursor.fetchall()
        )

    return Principal(
        user_id=user["id"],
        auth_subject=user["auth_subject"],
        email=user["email"],
        display_name=user["display_name"],
        memberships=memberships,
    )

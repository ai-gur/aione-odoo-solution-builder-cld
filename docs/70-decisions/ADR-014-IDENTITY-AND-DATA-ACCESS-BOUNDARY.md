# ADR-014: Identity, Session and Data-Access Boundary

**Status:** Accepted  
**Accepted:** 18 August 2026  
**Approved by:** Nir Bar, founding partner, AIOne  
**Date:** 18 August 2026
**Proposed by:** Claude implementation authority, for Codex design review
**Resolves:** readiness blockers B3 (web-to-data path), B4 (row-level security enforcement), B5 (service-to-service authentication)
**Amends:** ADR-002 (adds a data-access boundary), ADR-003 (adds the policy enforcement mechanism), ADR-010 (adds service-to-service authentication)

## Context

ADR-002 places domain state transitions, approvals and provisioning authorization in the Python application layer. ADR-003 requires application authorization with PostgreSQL row-level security as defense in depth. MVP Architecture §4 nevertheless draws the Next.js application connecting directly to PostgreSQL, authentication and storage, and §19 requires complete authorization at the service layer. These cannot all be true at once.

Two mechanisms are also unspecified. First, nothing states which database identity the domain API uses or how a verified tenant claim reaches PostgreSQL; if the API connects with a provider service-role key, row-level security is bypassed and every policy test is vacuous. Second, `.env.example` defines a static `DOMAIN_API_INTERNAL_TOKEN` shared between web and API, which is the long-lived shared credential ADR-010 exists to prevent.

Increment 0 stories I0-04 and I0-05 cannot be implemented, and its stop condition "row-level security conflicts with the authentication approach" cannot be evaluated, until these are decided.

## Decision

### Identity

Use one OIDC-compatible identity provider, integrated through an adapter so the provider remains replaceable. Supabase Auth satisfies the MVP requirement. The provider issues user identity only. It is never the source of authorization.

### Data-access boundary

The web tier holds the authenticated session and nothing else. All domain reads and writes go through the Python domain API. The web tier holds no database connection string, no service-role key and no direct storage client. Object storage is reached only through short-lived scoped grants issued by the domain API after an authorization check.

### Authorization

The domain API verifies the provider token on every request — signature against the published key set, issuer, audience, expiry and an algorithm allowlist — then resolves tenant, customer, project and role membership from the control database. A tenant, customer, project or role supplied by the client is ignored.

### Database identities

Four distinct roles:

| Role | Rights |
| --- | --- |
| `app_migrator` | Schema owner. DDL and policy definition. Used by migrations only |
| `app_api` | DML on domain tables. Not superuser, not `BYPASSRLS`, no DDL |
| `app_worker` | DML limited to the tables its jobs own, plus outbox and job tables |
| `app_support` | Read-only, scoped, time-bounded, audited |

The provider service-role key is restricted to migration and break-glass use and is absent from API and worker runtime configuration.

### Policy context

Each request opens a transaction and sets `app.tenant_id`, `app.actor_id` and the project scope with `SET LOCAL` before any statement. Policies read them through `current_setting(..., true)`. `SET LOCAL` is used rather than session-level `SET` because transaction-mode connection pooling reuses sessions across requests; a session-level setting leaks the previous request's tenant to the next one.

### Service-to-service authentication

Web, API, worker and runner hold separate identities. Calls between them carry a short-lived signed token bound to issuer, audience and an expiry of no more than five minutes, obtained from the platform's workload identity where available. A static shared token is permitted only in local development and is named to make that unmistakable.

### Step-up authentication

Blueprint approval, manifest authorization, provisioning start, deviation acceptance and scoped export require re-authentication within a policy-defined window. The approval event records the authentication time and method. Consultant, architect and provisioning roles require MFA.

## Rules

- No client-supplied tenant, customer, project or role is ever trusted.
- Audit tables grant `INSERT` only to application roles; `UPDATE` and `DELETE` are revoked.
- A migration that adds a customer-owned table without a tenant key and a policy is a blocking review defect.
- Every protected workflow has a negative test proving cross-tenant denial at both the API and the database layer.
- Policy tests connect as `app_api`, never as the migrator or a provider service role, or they prove nothing.

## Alternatives considered

**Web tier reads PostgreSQL directly through the provider client.** Rejected. It duplicates authorization in two languages, makes approval and provisioning authority reachable from the browser tier, and contradicts ADR-002.

**Application-layer authorization only, without row-level security.** Rejected. ADR-003 requires defense in depth, and a single missed service-layer check would expose another customer's discovery data.

**Row-level security as the primary control.** Rejected. Policies cannot express workflow-state and approval-role conditions, and ADR-003 already assigns primary authority to application services.

## Consequences

- The Next.js application cannot use provider client libraries for data; the typed API client is the only path.
- Connection pooling configuration becomes security-relevant and must be covered by a test that proves context does not leak between pooled requests.
- Local development needs a documented substitute for workload identity.
- Cross-tenant negative tests become meaningful rather than symbolic, because the API's own role cannot bypass policy.

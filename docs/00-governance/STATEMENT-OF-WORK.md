# Statement of Work — AIOne Odoo Solution Builder

**Version:** 1.0
**Date:** 18 August 2026
**Status:** Proposed
**Prepared by:** Claude implementation authority
**For acceptance by:** Nir Bar, founding partner, AIOne

## 1. Purpose

This document states what is being built, how it is delivered and reviewed, what is excluded, and what must be true for the work to be accepted. It governs the build of the AIOne Odoo Solution Builder itself. It is not a customer engagement SOW; the pilot customer engagement is a separate document.

Where this document and an accepted specification disagree, the specification governs and this document is amended (`DESIGN-AUTHORITY.md` §Authority order).

## 2. What is being built

A standalone AIOne control plane that interviews a business, produces an approved Odoo Enterprise 19 solution blueprint, and provisions a validated development or demonstration sandbox.

Three connected capabilities, per `ODOO-SOLUTION-BUILDER-PRODUCT-CONSTITUTION.md` §2:

1. **Discovery** — adaptive interviews at three depths, evidence-assisted, producing source-linked facts, requirements, assumptions and open questions.
2. **Blueprint generation** — requirements mapped against a verified Odoo 19 capability catalogue into explainable, versioned decisions.
3. **Sandbox provisioning** — deterministic configuration of a fresh Odoo 19 Enterprise sandbox from an approved, immutable deployment manifest.

Supported throughout by the customer portfolio: customers, solution workspaces, accepted baselines, change requests and audit history.

## 3. Scope

### 3.1 In scope

| Area | Included |
| --- | --- |
| Discovery | Quick Start, Guided and Comprehensive interview definitions; deterministic branching; document-assisted extraction; conflict detection; confidence, completeness and risk assessment; consultant review and approval |
| Requirements | Deterministic normalisation into facts, requirements and open questions, each traceable to its source answer |
| Catalogue | Verified Odoo 19 capability catalogue built from pinned core, Enterprise, localization and approved-addon source, for the pilot archetype scope |
| Blueprint | Fit assessment, decision generation with alternatives and rationale, gap register, phase planning, versioning and approval |
| Manifest | Compilation of an approved blueprint into an immutable, checksummed deployment manifest |
| Provisioning | Docker sandbox driver, runner, allowlisted versioned handlers, current-state inspection, idempotent reruns, validation suites, deviation management |
| Portfolio | Customer organizations, solution workspaces, membership and authority model, accepted baselines, change requests, timeline and audit |
| Interface | Hebrew RTL primary and English US secondary, WCAG 2.2 AA, IS 5568 part 1 for customer-facing surfaces |
| Platform | Tenant isolation, append-only audit, durable jobs, governed AI gateway, secrets by reference, CI quality gates |

### 3.2 Out of scope

From Constitution §4 and MVP Architecture §32. These are excluded from this SOW and require a new ADR and a separate agreement to introduce:

- automatic deployment to production, and live cutover orchestration;
- complete financial or historical data migration execution;
- automatic deployment of AI-generated custom modules;
- modification of Odoo core or Enterprise source;
- Odoo.sh or additional hosting-provider drivers;
- broad marketplace-addon selection; every Odoo application and vertical;
- complex manufacturing, payroll processing, regulated clinical implementation;
- autonomous customer acceptance; commercial estimation and contract generation;
- onboarding of existing live Odoo customers (no specification exists — `DEFERRED-DECISIONS.md` D-02).

## 4. Delivery model

Nine increments. Each is demonstrable and tested before the next depends on it, per MVP Architecture §29. An increment is complete when its exit criteria are met and its tests pass in CI.

| # | Increment | Status |
| --- | --- | --- |
| 0 | Foundation and architecture | **Delivered** |
| 1 | Tenancy and workspace | **Delivered** |
| 2 | Quick Start discovery | **Delivered** |
| 3 | Guided discovery and evidence | Not started |
| 4 | Odoo catalogue and blueprint MVP | Not started |
| 5 | Manifest and Docker sandbox bootstrap | Not started |
| 6 | Configuration handlers and validation | Not started |
| 7 | Customer sandbox review | Not started |
| 8 | Comprehensive discovery baseline | Not started |

### 4.1 Delivered to date

Fourteen commits, 7 migrations, 4 web routes, **132 automated tests green**, CI running the same commands a developer runs.

**Increment 0 — Foundation.** Workspace and toolchain; RFC 8785 canonicalization and SHA-256 digests shared by TypeScript and Python with cross-language fixtures; local control-plane stack (PostgreSQL, Redis, object storage, mail capture); migrations with row-level security enabled and forced; domain API with health, readiness and server-side identity; durable job path with transactional outbox, leases and idempotent effects; bilingual accessible shell; CI with secret scanning.

**Increment 1 — Tenancy and workspace.** Customer organizations, solution workspaces, workspace membership and state history; the authority layer implementing `ROLES-AND-PERMISSIONS.md`; guarded state transitions with the Account Manager holding engagement completion.

**Increment 2 — Quick Start discovery.** Versioned interview definitions with the 18 canonical Quick Start goals in Hebrew and English; deterministic branching with recorded reasons; answers preserving original wording, author, source and revision history; deterministic normalisation into facts, requirements and open questions; consultant review screen; the discovery approval gate producing an immutable, digest-verified approved version.

### 4.2 Remaining increments

Each remaining increment delivers the scope and exit criteria stated in MVP Architecture §29. No estimate is given here: MVP Architecture §33 states the plan should be estimated only after ADRs, pilot scope and team availability are confirmed, and calendar dates must not be committed from the architecture document alone.

## 5. Acceptance

### 5.1 Per increment

An increment is accepted when its exit criteria are demonstrated, its automated tests pass in CI, and a completion report is delivered in the format required by the handoff packet: delivered scope, changed files, commands to run, test and CI results, security checks, known limitations, deviations from accepted ADRs, and decisions required before the next increment.

### 5.2 MVP acceptance

The MVP is complete when all fourteen conditions in Constitution §14 and MVP Architecture §34 hold. In summary: a consultant can create and isolate a customer workspace; a customer can complete discovery in Hebrew or English; the system produces reviewed source-linked requirements; an approved catalogue release covers the pilot scope; the engine generates explainable decisions and an approved blueprint; the blueprint compiles into an approved immutable manifest; the manifest provisions a fresh isolated sandbox; rerunning is idempotent; mandatory validations pass; failing sandboxes are not released; the customer can review and submit classified feedback; every configuration change traces to requirement, decision, manifest and approval; cross-customer and sandbox-isolation tests pass; and no production deployment capability is active.

### 5.3 Non-negotiable release conditions

An increment is not released while any of the following holds (`SECURITY-BASELINE.md` §Stop conditions):

- a Critical or High isolation defect remains;
- secrets appear in repository history or logs;
- an approval can be bypassed;
- a sandbox runner can target more than one authorized environment;
- cross-tenant negative tests are missing or failing.

## 6. Governance

- **Design authority** is held by Codex; implementation follows accepted packets. Architecture changes require an ADR or change request (`DESIGN-AUTHORITY.md`).
- **Approval states** are Draft, Proposed, Accepted, Superseded, Rejected. Only Accepted documents authorize implementation.
- **ADR-001 through ADR-015** were accepted on 18 August 2026 and are binding.
- **Product invariants** — approval gates, tenant isolation, immutable approved versions, allowlisted handlers, no production provisioning — may not be weakened by implementation. A conflict is raised as a written question, not resolved in code.
- **Deferred decisions** are tracked in `DEFERRED-DECISIONS.md`, each with the concrete event that ends the deferral. Reaching a trigger blocks the dependent work.

## 7. Assumptions and dependencies

AIOne provides, and delay in any of these directly delays the dependent increment:

| # | Dependency | Needed by |
| --- | --- | --- |
| A-01 | Pinned Odoo 19 core, Enterprise and Foundation checkouts, and confirmation of which are authoritative | Increment 4 (currently outstanding) |
| A-02 | Shared AIOne addons repository, or confirmation that none exists yet | Increment 4 |
| A-03 | Docker infrastructure for sandbox hosting, isolated per environment | Increment 5 |
| A-04 | Odoo Enterprise licensing valid for provisioned sandboxes | Increment 5 |
| A-05 | Authorized finance reviewer for Israeli accounting boundaries | Increment 4 |
| A-06 | Approved pilot customer, or a realistic sanitized pilot dataset | Increment 7 |
| A-07 | Data residency and privacy position before real customer data is stored | Increment 3 (D-01) |
| A-08 | Named accessibility coordinator and contact for the accessibility statement | Before the portal reaches a real customer (D-06) |
| A-09 | Identity provider selection and tenant for deployed environments | First deployed environment |
| A-10 | Review of the Hebrew interview wording by an AIOne consultant who runs these conversations | Increment 3 |

The pilot archetype remains Israeli B2B wholesale distribution with CRM, Sales, Purchase, Inventory and approved accounting boundaries.

## 8. Responsibilities

| Party | Responsibility |
| --- | --- |
| Product owner (AIOne) | Outcomes, priorities, scope decisions, pilot selection, acceptance |
| Design authority (Codex) | Specifications, ADRs, cross-domain and security review, bounded handoff packets |
| Implementation (Claude) | Implements accepted packets, adds tests, reports blockers, proposes changes, never silently alters approved architecture |
| Odoo functional and finance reviewers | Capability fit, business behaviour, Israeli accounting boundaries, role and approval design |

Named specialist review is additionally required for security, financial localization, destructive data handling, production connectivity and cross-customer access.

## 9. Quality commitments

- **Testing** — every increment adds tests for success, failure and authorization paths. Cross-tenant negative tests are mandatory for every protected workflow. A skipped mandatory validation cannot pass readiness.
- **Security** — tenant isolation enforced at the service layer with row-level security as defense in depth; append-only audit; secrets by reference only; no production credentials in sandbox configuration.
- **Accessibility** — WCAG 2.2 AA throughout; IS 5568 part 1 Level AA and a published accessibility statement for customer-facing surfaces.
- **Language** — Hebrew RTL is the primary experience and is tested as such, not retrofitted.
- **Traceability** — every applied configuration traces to an approved blueprint decision, a versioned manifest and a recorded approval.

## 10. Change control

A change to scope, an accepted ADR, a product invariant or an increment's exit criteria is handled as a written change request naming the affected documents and the impact on delivery. Implementation does not absorb scope changes silently.

Amendments to this SOW are versioned; the superseding version identifies the prior one and the reason.

## 11. Open items before this SOW can be finalized

These are the decisions this document cannot state on AIOne's behalf. Each blocks the increment named.

| # | Open item | Blocks |
| --- | --- | --- |
| O-01 | Which Odoo checkouts are authoritative: `_odoo-source`, `AIOne Odoo Vendor/odoo`, and whether `AIOne Odoo Platform` is the Foundation | Increment 4 |
| O-02 | Whether a shared AIOne addons repository exists | Increment 4 |
| O-03 | Data residency and privacy position (D-01) | Increment 3 |
| O-04 | Accessibility coordinator appointment and contact (D-06) | Customer-facing release |
| O-05 | Step-up authentication window (300 seconds proposed) | Increment 5 |
| O-06 | How an engagement that ends without customer acceptance leaves the delivery queue (`workspace.close`) | Increment 7 |
| O-07 | Whether existing live Odoo customers are in scope for this product (D-02) | Tenancy model finalization |
| O-08 | Commercial terms: fees, payment schedule, term, IP ownership, warranty and support | Signature |

Item O-08 is deliberately absent from this document. It is a commercial matter for AIOne to state, and no assumption has been made about it.

## 12. Sign-off

| Role | Name | Date |
| --- | --- | --- |
| Product owner | Nir Bar, founding partner, AIOne | |
| Design authority | | |

Acceptance of this SOW authorizes the delivery model, scope and acceptance criteria described above. It does not accept any deferred decision or open item; those are closed individually as their triggers are reached.

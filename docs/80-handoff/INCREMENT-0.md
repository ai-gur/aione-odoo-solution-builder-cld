# Implementation Handoff: Increment 0

**Status:** Accepted  
**Accepted:** 18 August 2026  
**Approved by:** Nir Bar, founding partner, AIOne  
**Increment:** Foundation and Architecture  
**Product:** AIOne Odoo Solution Builder

## Objective

Create a runnable, testable repository foundation for the control plane without implementing customer discovery or provisioning behavior prematurely.

## Preconditions

- Product design documents are present in `docs/10-product/`.
- ADR-001 through ADR-015 are Accepted.
- The domain vocabulary in `docs/20-domain/` is Accepted: canonical enumerations, roles and authorities, naming.
- Existing Odoo 19 Enterprise Foundation, Odoo core and Enterprise repositories are available as separate workspace checkouts.
- Pilot scope remains Israeli B2B wholesale distribution.

## In scope

### Repository and tooling

- Initialize git repository and protected default branch workflow.
- Create workspace structure from the architecture specification.
- Select and pin JavaScript and Python package-management tools.
- Add formatting, linting, type checking, unit testing and secret scanning.
- Add commit and CI conventions.

### Web skeleton

- Next.js TypeScript application.
- Tailwind and shadcn/ui baseline.
- Hebrew RTL and English locale routing.
- Accessible application shell with placeholder authenticated and portal areas.
- Typed API client placeholder generated from shared contracts.

### Python skeleton

- FastAPI domain service with health and readiness endpoints.
- Worker process with durable example job.
- Structured logging and correlation identifiers.
- Configuration loading with secret-safe errors.

### Data and auth

- PostgreSQL migration framework.
- Initial tables for tenants, users, memberships and audit events.
- Authentication-provider integration skeleton.
- Tenant authorization service and defense-in-depth row-level policies.
- Local seed containing AIOne test tenant and sanitized users.

### Durable work

- PostgreSQL job and outbox tables.
- Transactional outbox publisher.
- Redis-compatible queue adapter.
- Worker lease, heartbeat and duplicate-delivery behavior.
- Job status endpoint and minimal UI status view.

### Shared contracts

- Select canonical schema format.
- Add an example `HealthJob` or equivalent cross-process contract.
- Generate or validate TypeScript and Python types.
- Add compatibility and unsupported-version tests.

### Odoo workspace integration

- Validate configured local paths for Foundation, Odoo core and Enterprise.
- Record source revisions without copying repositories.
- Add non-mutating workspace health command.
- Do not install business applications or create customer databases in this increment.

### CI and documentation

- CI for web, Python, contracts, migrations and security checks.
- Local setup instructions.
- Architecture and dependency overview.
- Troubleshooting for common local failures.
- Decision and change-request templates.

## Explicitly out of scope

- Customer and project product screens beyond placeholders
- Interview questions or discovery rules
- AI model calls
- Evidence upload or parsing
- Capability catalogue ingestion
- Blueprint generation
- Deployment manifest compilation
- Odoo database provisioning
- Production hosting or credentials

## Required stories

### I0-01 Repository initialization

As a developer, I can clone the repository, copy `.env.example` to a local environment file, run the bootstrap command and receive actionable validation of missing prerequisites.

### I0-02 Local stack

As a developer, I can start web, API, worker, PostgreSQL, queue and local storage through one documented command.

### I0-03 Bilingual shell

As a reviewer, I can switch between Hebrew RTL and English and navigate an accessible placeholder shell.

### I0-04 Authentication skeleton

As an invited test user, I can authenticate and the API resolves my tenant membership without trusting a client-supplied tenant identifier.

### I0-05 Isolation proof

As a security reviewer, I can run an automated test proving one tenant cannot read or modify another tenant’s records.

### I0-06 Durable job

As a developer, I can submit an example background job, observe its state and safely redeliver it without duplicate material effect.

### I0-07 Shared contract

As a developer, I can change a shared example schema and see incompatible TypeScript or Python consumers fail CI.

### I0-08 Workspace health

As an Odoo developer, I can verify that the Foundation, AIOne addons, Odoo core and Enterprise paths exist and record their current revisions without modifying them.

### I0-09 Audit baseline

As an auditor, I can see append-only events for login, membership change and durable job submission without secret values.

### I0-10 CI baseline

As a maintainer, every pull request runs required formatting, linting, type, unit, contract, migration, policy and secret checks.

## Acceptance tests

1. Fresh documented setup succeeds on a supported developer machine.
2. `python scripts/run.py stack-up` starts all required control-plane services.
3. Web and API health checks pass.
4. Hebrew shell renders RTL and English shell renders LTR.
5. Keyboard navigation and visible focus work in the shell.
6. User identity is resolved server-side and mapped to tenant membership.
7. Cross-tenant API and direct policy tests fail closed.
8. Database migrations apply from empty and roll back where the selected tool supports it.
9. An outbox event reaches a worker.
10. Duplicate delivery does not duplicate the example effect.
11. Worker interruption produces a recoverable job state.
12. TypeScript and Python contract fixtures agree.
13. Unsupported contract version is rejected.
14. Audit events contain actor, tenant, action and correlation identifier.
15. Logs and test output contain no configured secret values.
16. Workspace health reports every pinned repository revision, or clear missing-path errors. Satisfied by `python scripts/run.py workspace-health` against `catalogue/pinned-sources.json`.
17. CI passes from a clean checkout.

## Required deliverables

- Running repository skeleton
- Canonical developer commands
- Local environment documentation
- Database migrations and policies
- Web, API and worker health paths
- Shared contract pipeline
- Durable example job
- Tenant-isolation tests
- CI workflow
- Security and dependency baseline
- Increment 0 completion report

## Completion report format

- Delivered scope
- Changed files and major components
- Commands to run
- Test and CI results
- Security checks
- Known limitations
- Deviations from accepted ADRs
- Decisions required before Increment 1

## Stop conditions

Stop and request design review if:

- the selected stack cannot support the approved trust boundaries;
- row-level security conflicts with the authentication approach;
- shared schema generation would create two authoritative sources;
- a queue platform requires treating its state as authoritative;
- local Odoo integration requires copying or modifying Odoo source;
- any requested shortcut weakens tenant isolation or approval integrity.


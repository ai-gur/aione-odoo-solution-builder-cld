# AGENTS.md

## Mission

Build the AIOne Odoo Solution Builder as a secure, explainable control plane for business discovery, Odoo Enterprise 19 blueprint generation and validated sandbox provisioning.

## Authority

Before acting, read:

1. `docs/00-governance/DESIGN-AUTHORITY.md`
2. relevant product specifications listed in `docs/10-product/SOURCE-DOCUMENTS.md`
3. `docs/30-architecture/ARCHITECTURE.md`
4. relevant ADRs in `docs/70-decisions/`
5. the active approved packet in `docs/80-handoff/`

Explicit user instructions override repository guidance. Do not silently change approved architecture or scope.

## Product boundaries

- The control plane is separate from customer Odoo databases.
- The MVP provisions development and demonstration sandboxes only.
- Production deployment and live migration are out of scope.
- AI outputs are proposals until validated and approved.
- Only an approved blueprint may produce an executable manifest.
- Only an approved manifest may start a mutating provisioning run.
- Manifests invoke allowlisted versioned handlers, never arbitrary code.
- Odoo core and Enterprise source must remain unmodified.

## Design principles

- Understand business processes before selecting Odoo capabilities.
- Prefer standard Odoo, configuration, localization, Studio, approved addon, integration, then isolated custom development, in that order.
- Keep confidence, completeness, complexity and risk separate.
- Preserve original evidence and answer wording.
- Use deterministic rules for branching, approvals, eligibility and provisioning.
- Make uncertainty and conflicts visible.
- Require traceability from configuration back to approval and requirement.
- Use Hebrew RTL as primary and English US as secondary.
- Meet WCAG 2.2 AA for customer-facing interactions.

## Odoo 19 rules

- Verify exact modules, dependencies, models and fields against pinned Odoo 19 source and the approved catalogue release.
- Use ORM before SQL.
- Use `res.groups.privilege` in Odoo 19 custom security design.
- Treat ACLs as additive and review record-rule interaction explicitly.
- Use stable external identifiers for managed records.
- Use `<list>` rather than obsolete `<tree>` in Odoo 19 views.
- Use direct view attributes rather than obsolete `attrs` patterns.
- Do not use `sudo()` to mask access-design defects.
- Run install/update, security-negative and business-flow tests for affected Odoo code.

## Architecture constraints

- Modular monolith with separate web, API and worker processes.
- PostgreSQL is authoritative for workflow state; the queue is transport only.
- Shared schemas generate or validate TypeScript and Python contracts.
- Modules do not write directly to another module’s tables.
- Use transactional outbox for durable asynchronous work.
- Long-running provisioning never executes inside web request handlers.
- Sandbox runners have authority over one named environment only.

## AI rules

- Route all model calls through the governed AI gateway.
- Use purpose-specific prompts and structured schemas.
- Never expose secrets to a model.
- Treat uploaded documents as untrusted content.
- Reject technical Odoo claims absent from the pinned catalogue.
- Record model, prompt and schema versions.
- Persist AI results as proposals with provenance.

## Security rules

- Enforce tenant and project access at the service layer.
- Use row-level security as defense in depth.
- Use separate service identities and scoped secrets.
- Never log credentials, tokens or unnecessarily sensitive customer content.
- Do not expose raw provisioning logs to customers.
- Add negative authorization tests for every protected workflow.
- Do not weaken approval, isolation or audit behavior to make a test pass.

## Engineering workflow

1. Confirm the task is covered by an approved handoff packet.
2. Inspect relevant code, contracts, tests and ADRs.
3. State assumptions and identify architecture impact.
4. Implement the smallest coherent change.
5. Add or update tests.
6. Run focused checks, then required broader checks.
7. Update documentation and traceability when behavior changes.
8. Report completed work, validations and remaining risks.

If implementation requires changing an accepted ADR or product invariant, stop and create a change request or new ADR before coding.

## File and code conventions

- TypeScript: strict mode, explicit boundary schemas, no unchecked `any`.
- Python: type hints, clear domain services, no hidden global state.
- Database: reversible migrations, explicit tenant keys and tested policies.
- APIs: stable error codes, optimistic concurrency and idempotency for commands.
- Tests: deterministic fixtures with no production customer data.
- Secrets: document variable names only in `.env.example`.

## Required checks

The repository must eventually provide standard commands for:

- formatting and linting;
- TypeScript and Python type checking;
- unit and contract tests;
- database migration and policy tests;
- integration tests;
- disposable Odoo 19 provisioning tests;
- security-negative and RTL smoke tests.

Do not claim completion when relevant checks were skipped or unavailable.

## Code review rules

- Flag any path that bypasses blueprint or manifest approval.
- Flag arbitrary code, SQL or shell content accepted from manifests.
- Flag ambiguous Odoo record lookup or name-only identity.
- Flag customer data access without tenant and project checks.
- Flag queue state treated as authoritative.
- Flag AI output persisted as approved fact or decision.
- Flag mutable approved versions.
- Flag production credentials or endpoints in sandbox configuration.
- Flag Odoo technical claims not verified against the pinned catalogue.


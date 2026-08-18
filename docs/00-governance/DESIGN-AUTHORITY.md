# Design Authority

## Authority order

1. Explicit current user instruction
2. Approved product constitution and specifications
3. Accepted Architecture Decision Records
4. Approved implementation handoff packet
5. Repository guidance in `AGENTS.md` and `CLAUDE.md`
6. Existing implementation behavior and tests

When sources conflict, stop and document the conflict rather than choosing the easiest implementation.

## Responsibilities

### Product owner

- Defines outcomes, scope and priorities
- Approves material product changes
- Selects pilot customers and acceptance authority

### Codex design authority

- Maintains product and architecture specifications
- Reviews cross-domain and security consequences
- Creates bounded implementation packets
- Approves or rejects architecture change proposals

### Claude implementation authority

- Implements approved packets
- Adds tests and implementation documentation
- Reports blockers and proposes changes
- Does not change approved architecture without review

### Odoo functional and finance reviewers

- Verify Odoo capability fit and business behavior
- Approve Israeli accounting boundaries and configuration
- Review role, approval and process design

## Change control

A new ADR or change request is required when changing:

- service or trust boundaries;
- tenancy or authorization;
- immutable version and approval behavior;
- AI authority or data access;
- catalogue evidence rules;
- manifest schema semantics;
- provisioning handler execution;
- sandbox isolation;
- source-revision policy;
- production scope.

Implementation details inside an accepted boundary may be recorded as ordinary design notes.

## Approval states

Documents use Draft, Proposed, Accepted, Superseded or Rejected. Only Accepted documents authorize implementation. A superseding record must identify the prior version and migration impact.

## Sensitive changes

Security, financial localization, destructive data handling, production connectivity and cross-customer access require named specialist review in addition to ordinary approval.


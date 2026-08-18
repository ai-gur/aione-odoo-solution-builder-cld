# Testing Standards

## Test pyramid

### Unit

- Discovery branching and scoring
- Requirement generation templates
- Fit and dependency rules
- Approval invalidation
- Manifest compilation
- Handler compare and plan behavior

### Contract

- Shared schema fixtures in TypeScript and Python
- Unsupported schema rejection
- Worker and sandbox job envelopes
- Handler and validation registration

### Integration

- PostgreSQL migrations and row-level policies
- Authentication and invitation flows
- Transactional outbox and worker recovery
- Object storage and evidence processing
- AI gateway structured outputs and failure handling
- Odoo catalogue extraction from fixture addons

### Odoo

- Clean module installation and update
- ORM handler transaction behavior
- Idempotent record reconciliation
- ACL, record rule, company and prohibited-action tests
- Browser tours for critical pilot journeys
- Query-count checks for material custom logic

### End to end

- Quick Start to approved discovery
- Guided wholesale pilot to approved blueprint
- Approved manifest to validated sandbox
- Same-manifest rerun without duplicates
- Failed sandbox followed by rebuild
- Customer review and change request

## Test rules

- Test both authorized and forbidden behavior.
- Test retries and duplicate delivery for every durable command.
- Use frozen time and stable identifiers where necessary.
- Never use production customer data.
- A skipped mandatory validation cannot pass readiness.
- Keep golden fixtures versioned with their contract and catalogue release.

## Increment 0 minimum

- TypeScript and Python consume the same example contract.
- Database migration and tenant-policy tests run in CI.
- A durable worker job survives duplicate delivery.
- Authentication smoke test passes.
- Repository secret scan passes.


# ADR-011: Audit-Event Integrity and Retention

**Status:** Accepted  
**Accepted:** 18 August 2026  
**Approved by:** Nir Bar, founding partner, AIOne  
**Date:** 18 August 2026

## Context

Approvals, AI proposals, provisioning and deviations require proof of who authorized what version and what changed.

## Decision

Record material events in an append-only audit model separate from troubleshooting logs. Each event includes actor or service identity, tenant, project, action, subject version, timestamp, correlation identifier and outcome. Sensitive payloads are referenced or redacted.

## Rules

- Application users cannot update or delete audit events.
- Approval events include immutable content hash.
- Retention policy depends on data classification and contractual need.
- Audit export is scoped and itself audited.
- Tamper-evident storage or chained hashes will be evaluated during implementation.

## Consequences

- Additional storage and privacy governance
- Reliable traceability and incident investigation


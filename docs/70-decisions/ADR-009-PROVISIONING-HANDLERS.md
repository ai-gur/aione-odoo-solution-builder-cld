# ADR-009: Allowlisted Versioned Provisioning Handlers

**Status:** Proposed  
**Date:** 18 August 2026

## Context

Allowing arbitrary Python, SQL or shell commands in a deployment manifest would make approval meaningless and create a critical code-execution path.

## Decision

Manifests may invoke only registered, allowlisted handlers with pinned versions and schema-validated parameters. Handlers implement inspect, compare, plan, apply, validate and declared compensation behavior.

## Rules

- Current-state inspection precedes every write.
- Stable external identity is required for managed Odoo records.
- Ownership is Controlled, Mergeable, Observe-only or Unmanaged.
- Destructive handlers are disabled by default in MVP.
- Handler releases require contract, idempotency and security tests.

## Consequences

- New configuration types require intentional handler development
- Provisioning is auditable, testable and reproducible


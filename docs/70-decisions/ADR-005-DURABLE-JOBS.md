# ADR-005: Durable Jobs, Transactional Outbox and Queue

**Status:** Accepted  
**Accepted:** 18 August 2026  
**Approved by:** Nir Bar, founding partner, AIOne  
**Date:** 18 August 2026

## Context

Evidence extraction, blueprint generation and Odoo provisioning may outlive requests and must recover from process or queue failure.

## Decision

PostgreSQL stores authoritative job, workflow and checkpoint state. A transactional outbox records state changes and events atomically. A Redis-compatible queue transports jobs to workers. Workers use leases, heartbeats and idempotency keys.

## Rules

- Queue acknowledgement is not proof of business completion.
- Retried jobs reuse the same idempotency identity.
- Stale leases are detected and reconciled.
- Provisioning operations persist bounded checkpoints.

## Consequences

- Additional outbox relay and reconciliation code
- Recoverable workflows without requiring a complex orchestration platform for MVP


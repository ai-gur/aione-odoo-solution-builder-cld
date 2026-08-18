# ADR-003: PostgreSQL Tenancy and Authorization

**Status:** Accepted  
**Accepted:** 18 August 2026  
**Approved by:** Nir Bar, founding partner, AIOne  
**Date:** 18 August 2026

## Context

The control plane contains confidential discovery, evidence and credentials for multiple unrelated customers.

## Decision

Use one control-plane PostgreSQL service with explicit tenant, customer and project keys. Enforce authorization in application services and use PostgreSQL row-level security as defense in depth. Store each customer Odoo database outside the control database and isolate it by environment.

## Rules

- Every customer-owned aggregate carries tenant and project context.
- Service identities have separate permissions.
- Cross-tenant access is denied by default and covered by negative tests.
- Support access is explicit, scoped and audited.

## Consequences

- Efficient MVP operations without one control database per customer
- Authorization and migration reviews must treat missing tenant keys as critical defects


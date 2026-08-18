# ADR-002: Next.js and Python Service Boundary

**Status:** Proposed  
**Date:** 18 August 2026

## Context

The product needs a strong bilingual web experience and deep Python integration with Odoo, document processing, rules and workers.

## Decision

Use Next.js with TypeScript for the web interface and BFF. Use Python with FastAPI for domain operations, AI orchestration, catalogue processing and provisioning. Long-running work executes in Python workers, never web request handlers.

## Boundary

The web layer may validate presentation input and manage sessions. Domain state transitions, approvals, scoring and provisioning authorization belong to the Python application layer.

## Consequences

- Best-fit ecosystems for UI and Odoo work
- Shared contracts are mandatory to prevent semantic drift
- Deployment and local development include two language toolchains


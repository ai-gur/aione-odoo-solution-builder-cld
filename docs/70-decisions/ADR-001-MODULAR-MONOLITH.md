# ADR-001: Modular Monolith with Separate Workers

**Status:** Accepted  
**Accepted:** 18 August 2026  
**Approved by:** Nir Bar, founding partner, AIOne  
**Date:** 18 August 2026

## Context

Discovery, requirements, blueprinting and provisioning share one lifecycle and require consistent version and approval behavior. Premature microservices would add distributed transactions, duplicated schemas and operational overhead.

## Decision

Build a modular monolith with independently deployed Next.js web, Python API and Python worker processes. Domain modules own their data and expose application services. They communicate asynchronously through durable domain events where required.

## Consequences

- One coherent control database and easier cross-domain traceability
- Web and long-running workers scale independently
- Internal boundaries must be enforced in code review and tests
- A module may be extracted later only with a new ADR and measured need


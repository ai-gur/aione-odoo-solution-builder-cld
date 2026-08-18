# ADR-008: Docker Sandbox Driver and Runner Trust Boundary

**Status:** Accepted  
**Accepted:** 18 August 2026  
**Approved by:** Nir Bar, founding partner, AIOne  
**Date:** 18 August 2026

## Context

The MVP needs repeatable sandboxes and already has a Docker-based Odoo 19 Enterprise Foundation. Odoo.sh and other hosting platforms have different controls.

## Decision

Implement one Docker sandbox driver first. Execute provisioning through a runner inside the isolated environment boundary. The runner receives short-lived authorization for one environment and cannot access another sandbox or approve manifests.

## Rules

- Pin Odoo core, Enterprise, Foundation and addon revisions.
- Separate compute, database, storage and credentials per workspace environment.
- Keep the driver contract provider-neutral.
- Prefer rebuilding disposable failed sandboxes.

## Amendment 1 — delivery routes share one pinned source (18 August 2026)

Two customer delivery routes are planned: a remote server, and an offline package for an on-premise installation activated with the customer's own Odoo licence key. They are two drivers, not two sources. Both resolve to the revisions pinned in `catalogue/pinned-sources.json`, and the offline package is a release artifact built from those revisions with a recorded digest — never a separately maintained copy of files.

The licence key is a secret resolved by reference at deployment (ADR-010). It appears in no manifest, no artifact and no repository file.

## Consequences

- Fast path using the existing Foundation
- Future hosting providers require separate drivers
- Runner packaging and isolation require security testing


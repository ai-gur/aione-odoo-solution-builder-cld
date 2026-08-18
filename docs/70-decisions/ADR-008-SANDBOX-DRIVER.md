# ADR-008: Docker Sandbox Driver and Runner Trust Boundary

**Status:** Proposed  
**Date:** 18 August 2026

## Context

The MVP needs repeatable sandboxes and already has a Docker-based Odoo 19 Enterprise Foundation. Odoo.sh and other hosting platforms have different controls.

## Decision

Implement one Docker sandbox driver first. Execute provisioning through a runner inside the isolated environment boundary. The runner receives short-lived authorization for one environment and cannot access another sandbox or approve manifests.

## Rules

- Pin Odoo core, Enterprise, Foundation and addon revisions.
- Separate compute, database, storage and credentials per project environment.
- Keep the driver contract provider-neutral.
- Prefer rebuilding disposable failed sandboxes.

## Consequences

- Fast path using the existing Foundation
- Future hosting providers require separate drivers
- Runner packaging and isolation require security testing


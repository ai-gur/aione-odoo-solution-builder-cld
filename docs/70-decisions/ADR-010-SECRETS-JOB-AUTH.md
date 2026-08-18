# ADR-010: Secrets and Short-Lived Job Authorization

**Status:** Accepted  
**Accepted:** 18 August 2026  
**Approved by:** Nir Bar, founding partner, AIOne  
**Date:** 18 August 2026

## Context

Provisioning requires privileged infrastructure and Odoo access. Long-lived shared credentials would enlarge compromise impact.

## Decision

Store secret values only in an approved secret provider. Manifests use logical secret references. Workers and runners receive scoped, short-lived authorization bound to tenant, project, environment, manifest checksum, operation class and expiry.

## Rules

- Never place secret values in repository, manifests, logs or model prompts.
- Separate control-plane, worker and sandbox identities.
- Validate job envelope signature and expiry before mutation.
- Rotation does not require manifest modification.

## Consequences

- Requires secret-broker integration and local development substitutes
- Stronger containment and clearer audit trail


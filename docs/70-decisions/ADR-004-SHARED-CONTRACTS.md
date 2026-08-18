# ADR-004: Shared Schema and Type Generation

**Status:** Accepted  
**Accepted:** 18 August 2026  
**Approved by:** Nir Bar, founding partner, AIOne  
**Date:** 18 August 2026

## Context

TypeScript, Python, workers and sandbox runners exchange versioned domain and provisioning payloads.

## Decision

Define authoritative machine-readable schemas for cross-process contracts. Generate or validate TypeScript and Python types from those schemas. Every asynchronous envelope declares its schema version.

## Rules

- Breaking changes create a new schema version.
- Consumers reject unsupported versions.
- Contract fixtures run in both ecosystems.
- Approved domain versions remain immutable even when schemas evolve.

## Consequences

- More up-front schema discipline
- Reduced silent disagreement between services
- Compatibility testing becomes a release gate


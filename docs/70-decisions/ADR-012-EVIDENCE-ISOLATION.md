# ADR-012: Isolated Evidence Processing

**Status:** Proposed  
**Date:** 18 August 2026

## Context

Customer uploads may contain malware, sensitive data, malformed files or prompt-injection content.

## Decision

Upload evidence to scoped object storage, scan it, and process it in an isolated worker without provisioning authority. Extracted claims retain source locations and remain proposed until reviewed.

## Rules

- Quarantine scan failures.
- Limit file type, size and processing resources.
- Treat document instructions as content, never control commands.
- Apply data classification before AI processing.
- Provide minimum extracted content to the AI gateway.
- Enforce retention and deletion policy.

## Consequences

- More infrastructure than direct in-process parsing
- Reduced risk to the control plane and clearer evidence provenance


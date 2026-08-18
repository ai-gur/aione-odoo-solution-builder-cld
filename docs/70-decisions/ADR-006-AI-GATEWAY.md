# ADR-006: Governed AI Gateway

**Status:** Proposed  
**Date:** 18 August 2026

## Context

AI assists with interpretation and drafting but must not become an untracked decision authority or gain provisioning credentials.

## Decision

Route all model use through a single AI gateway with purpose-specific prompts, structured schemas, data-access policy, provenance, evaluation and a kill switch.

## Rules

- AI output is a proposal until deterministic validation and required human approval.
- The model receives minimum necessary project data and no secrets.
- Uploaded content is untrusted and cannot redefine system instructions.
- Odoo technical claims must reference the pinned catalogue.
- Model, prompt, tool and schema versions are recorded.

## Consequences

- Centralized policy and observability
- Additional gateway and evaluation work
- Easier provider or model change without altering domain authority


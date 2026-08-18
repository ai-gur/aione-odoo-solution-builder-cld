# ADR-015: Contract Format, Canonical Serialization and Identity Conventions

**Status:** Accepted  
**Accepted:** 18 August 2026  
**Approved by:** Nir Bar, founding partner, AIOne  
**Date:** 18 August 2026
**Proposed by:** Claude implementation authority, for Codex design review
**Resolves:** readiness blocker B9 (no canonical schema format, hashing or identifier convention)
**Amends:** ADR-004 (names the schema language and versioning rules), ADR-011 (names the hash construction for approval events)

## Context

ADR-004 mandates authoritative machine-readable schemas without naming a language. Increment 0 defers the choice to implementation. Meanwhile the specifications already assume three incompatible conventions: the manifest uses `apiVersion: aione.odoo/v1alpha1`, blueprints use an integer `version: 1`, and catalogue releases use `odoo19_catalogue_2026_08`.

More consequentially, ADR-011 requires an "immutable content hash" on approval events and Provisioning §4.2 requires a "canonical content checksum", but no canonicalization algorithm or hash function is defined anywhere. Two correct implementations of the same manifest would therefore produce different checksums, and approval verification — the mechanism the entire provisioning safety chain rests on — would not be reproducible.

## Decision

### Schema language

JSON Schema 2020-12 is the authoritative contract language. Schemas live in `packages/contracts` and are the single source. TypeScript types and Python models are generated from them; generated artifacts are never hand-edited, and an edited generated file is a review defect.

### Canonical form and hashing

The canonical form of any hashed document is UTF-8 JSON canonicalized per RFC 8785 (JCS). The digest is SHA-256, rendered lowercase as `sha256:<hex>`.

YAML is a presentation format only. The manifest may be rendered and reviewed as YAML, but the hash is always computed over its canonical JSON form.

The hash covers the entire document except the checksum field itself and the `approvals` collection, which is appended after the hash exists. The excluded paths are declared in the schema so exclusion cannot drift between implementations.

### Identifiers

Entity identifiers are ULIDs, stored as text and rendered with a type prefix: `ten_`, `cus_`, `wsp_`, `prj_`, `dsc_`, `req_`, `bp_`, `mf_`, `env_`, `run_`, `evt_`. ULIDs are lexicographically sortable by creation time and carry no tenant information.

Identifiers used by humans and in Odoo external identities are separate stable keys — `REQ-ORG-001`, `BP-ORG-001`, `company.main` — and are never derived from a ULID.

### Versions

| Subject | Format | Example |
| --- | --- | --- |
| Contract schema | Semantic version; major means breaking | `2.0.0` |
| Approved domain version | Monotonic integer per version line | `3` |
| Catalogue release | `odoo<major>-catalogue-<yyyy>-<mm>-<nn>` | `odoo19-catalogue-2026-08-01` |
| Handler release | Semantic version | `1.2.0` |

Every asynchronous envelope declares `schemaVersion`. A consumer accepts an equal major version and a minor version it recognizes, and rejects anything else with a stable error code rather than a best-effort parse. Minor versions are additive only.

`apiVersion: aione.odoo/v1alpha1` in Provisioning §4.3 is replaced by `kind` plus `schemaVersion` so that one versioning rule governs every contract. That specification requires a corresponding amendment.

### Primitive conventions

- Timestamps: RFC 3339 in UTC with a `Z` suffix, microsecond precision. Durations: ISO 8601.
- Locale codes: `he_IL` and `en_US` in contracts, storage and Odoo. BCP-47 (`he-IL`) exists only at the web presentation boundary.
- Money: integer minor units with an ISO 4217 code. Never a floating-point amount.
- Enumerations: `lower_snake_case`, closed by default; an open enumeration must say so and define unknown-value handling.
- Checksums, revisions and digests are opaque strings, never numbers.

## Rules

- A breaking change creates a new major schema version; the previous version remains published until its consumers are retired.
- Contract fixtures execute in both TypeScript and Python in CI, including an unsupported-version rejection case.
- Golden fixtures are versioned alongside their contract and catalogue release.
- Approved domain versions remain immutable even when the schema that described them evolves.
- Any code path that computes a hash uses the shared canonicalization utility. A second implementation is a review defect.

## Alternatives considered

**Protocol Buffers or Avro.** Rejected for the MVP. Stronger evolution tooling, but the contracts are also human-reviewed approval artifacts, and a binary schema language makes the manifest unreadable in review.

**Pydantic models as the source with schema emitted from Python.** Rejected. It makes Python authoritative and TypeScript derived, which reintroduces the semantic drift ADR-004 exists to prevent.

**UUIDv4 identifiers.** Rejected. Not time-ordered, which hurts index locality and audit reading. UUIDv7 would be acceptable if a ULID library becomes a maintenance concern.

## Consequences

- Canonicalization and hashing become shared utilities in both ecosystems, with cross-language fixtures proving identical digests for identical input.
- Manifest review remains human-readable while verification stays deterministic.
- The Provisioning specification requires the `apiVersion` amendment named above.
- Schema discipline becomes a release gate rather than a convention.

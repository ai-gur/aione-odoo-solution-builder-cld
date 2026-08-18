# Canonical Enumerations

**Version:** 0.1
**Date:** 18 August 2026
**Status:** Proposed
**Purpose:** One home for every closed value set in the product. Specifications describe these enumerations in prose; contracts, migrations and code must agree on exactly one spelling.

Conventions per ADR-015: values are `lower_snake_case`, closed unless stated, and never reordered — a value's meaning is fixed once published. Adding a value is a minor schema change; removing or redefining one is breaking.

Where a specification's prose differs from the value here, this file is the resolution and the specification requires amendment. Those cases are marked **[resolves]**.

## Document and approval states

`draft` · `proposed` · `accepted` · `superseded` · `rejected`

Source: `docs/00-governance/DESIGN-AUTHORITY.md`. Applies to specifications, ADRs and handoff packets. Only `accepted` authorizes implementation.

**[resolves]** The six product specifications currently carry `Initial design baseline`, which is not a member of this set.

## Workspace and engagement

**[resolves]** Blocker B2 is decided: the **Solution Workspace replaces the Implementation Project** as the bounded engagement aggregate (Option A). There is one aggregate and one state machine. Constitution §7.1, §8, §9 and §13 require the corresponding rename, and every table and contract uses `workspace_id`.

### Workspace lifecycle state

`proposed` · `discovering` · `clarification_required` · `designing` · `blueprint_review` · `approved_for_sandbox` · `provisioning` · `validation_failed` · `sandbox_active` · `customer_review` · `revision_required` · `accepted` · `operating` · `change_in_progress` · `suspended` · `archived` · `closed`

Merged from Constitution §9 (project lifecycle) and Customer Portfolio §2.2 (workspace states). The Constitution contributed the delivery states through first acceptance; the Portfolio contributed the long-lived states that follow it — `operating`, `change_in_progress`, `suspended`, `archived`.

Mapping for the amendment: Constitution `initiated` → `proposed`; `blueprint_drafting` → `designing`; `sandbox_ready` → `sandbox_active`. Portfolio `sandbox_active` is unchanged and now also covers the former `sandbox_ready`.

Two transitions carry a named authority rather than being derived from other state:

- `accepted` → `operating` requires `workspace.complete`, held by the Account Manager. This is the transition that releases a workspace from the delivery team's active queue.
- `accepted` is reached through `baseline.accept`, which sets the Current Accepted baseline.

## Discovery

### Discovery mode

`quick_start` · `guided` · `comprehensive`

### Discovery run state

`draft` · `invited` · `in_progress` · `waiting_for_others` · `clarification_required` · `ready_for_review` · `under_consultant_review` · `changes_requested` · `approved_for_blueprint` · `superseded` · `cancelled`

Source: Discovery §20.

### Question outcome

`answered` · `not_applicable` · `deferred` · `skipped_with_reason` · `unanswered`

Source: Discovery §11. A hidden question is never `answered`.

### Claim verification state

`proposed` · `confirmed` · `inferred` · `conflicting` · `superseded` · `unverified`

Source: Constitution §7.2, Discovery §12.

## Assessment

### Confidence

`green` · `amber` · `red`

`green` — verified by an appropriate owner or authoritative evidence, no unresolved conflict. `amber` — usable only with an explicit approved assumption. `red` — consultant resolution required before configuration.

### Completeness

`incomplete` · `complete_for_mode` · `complete`

### Risk

`low` · `medium` · `high` · `critical`

Confidence, completeness and risk are separate measurements and must never be collapsed into one score (Constitution §10).

### Requirement priority

`must` · `should` · `could` · `wont_this_release`

### Effort class

`xs` · `s` · `m` · `l` · `xl`

Source: Blueprint §21. An effort class is not a quotation.

## Blueprint

### Blueprint state

`draft` · `under_review` · `changes_requested` · `approved` · `superseded` · `withdrawn`

### Decision state

`proposed` · `evidence_required` · `under_review` · `changes_requested` · `accepted` · `rejected` · `approved` · `superseded`

### Fit classification

`standard_fit` · `configuration_fit` · `localization_fit` · `studio_fit` · `approved_addon_fit` · `integration_fit` · `custom_development_gap` · `process_change_candidate` · `partial_fit` · `unsupported` · `unresolved`

Source: Blueprint §10. Every `partial_fit` must produce a residual gap.

### Module inclusion reason

`business_selected` · `technical_dependency` · `platform_baseline`

Source: Blueprint §13.

## Environments and provisioning

### Environment type

`development` · `sandbox` · `staging` · `production`

The MVP may create `development` and `sandbox` only.

### Environment purpose

`automated_test` · `project_development` · `customer_demonstration`

**[resolves]** blocker B7. "Demonstration sandbox" is a *purpose* applied to an environment of type `sandbox`, not a fourth type. MVP Architecture §21, ADR-008 and `README.md` describe it as a type and require amendment.

### Environment lifecycle state

`requested` · `allocating` · `bootstrapping` · `configuring` · `validating` · `ready` · `ready_with_warnings` · `failed` · `suspended` · `expired` · `rebuilding` · `archived` · `destroyed`

Source: Provisioning §7.

### Provisioning run state

`planned` · `awaiting_authorization` · `queued` · `running` · `paused` · `blocked` · `cancelling` · `cancelled` · `failed` · `completed_with_warnings` · `completed` · `superseded`

Source: Provisioning §23.

### Operation class

`inspect` · `install` · `configure` · `upsert` · `assign` · `load` · `validate` · `connect` · `restart` · `remove` · `uninstall`

Source: Provisioning §11. `remove` and `uninstall` are excluded from MVP automation by default.

### Operation result

`pending` · `running` · `applied` · `already_compliant` · `skipped` · `failed` · `rolled_back` · `manually_resolved`

Source: Constitution §7.5.

### Management policy (ownership)

`controlled` · `mergeable` · `observe_only` · `unmanaged`

Source: ADR-009 and Provisioning §14. Conditional policies are expressed as `{policy, condition}`, never as a compound value name.

### Validation status

`passed` · `failed` · `warning` · `skipped` · `unable_to_evaluate`

Source: Provisioning §21. `skipped` and `unable_to_evaluate` are never equivalent to `passed`.

### Deviation severity

`critical` · `high` · `medium` · `low`

### Deviation resolution

`corrected_environment` · `new_manifest_version` · `accepted_bounded` · `rebuilt` · `false_positive`

Source: Provisioning §22.

### Error classification for retry

`transient_infrastructure` · `transient_db_concurrency` · `dependency_unavailable` · `invalid_desired_state` · `unsupported_current_state` · `access_denied` · `business_validation_failed` · `module_installation_failed` · `unknown`

Source: Provisioning §16. Only the two `transient_*` classes retry automatically.

## Change and portfolio

### Change request state

`submitted` · `triaging` · `clarification_required` · `discovery_active` · `impact_assessment` · `awaiting_approval` · `approved` · `implementation_active` · `sandbox_validation` · `customer_review` · `accepted` · `rejected` · `deferred` · `cancelled` · `superseded`

### Change triage class

`defect_against_baseline` · `configuration_correction` · `new_capability` · `capability_expansion` · `process_change` · `integration_change` · `data_or_migration_change` · `security_or_compliance_change` · `software_maintenance` · `training_or_documentation`

### Customer feedback class

`defect_against_blueprint` · `configuration_correction` · `discovery_correction` · `new_requirement` · `usability_or_training` · `accepted_behavior` · `deferred_enhancement`

### Repository class

`solution_builder` · `odoo_foundation` · `aione_shared_addons` · `customer_custom_code` · `external_approved_addon`

Source: Customer Portfolio §4.1 and §7.

## Security and data

### Data classification

`public` · `aione_internal` · `customer_confidential` · `sensitive_personal_or_financial` · `secret`

Source: `docs/40-security/SECURITY-BASELINE.md` and MVP Architecture §23.3. Classification determines storage, access, AI eligibility, logging, export and retention.

### Locale

`he_IL` · `en_US`

Canonical in contracts, storage and Odoo. BCP-47 (`he-IL`, `en-US`) exists only at the web presentation boundary (ADR-015).

### Catalogue release status

`draft` · `verifying` · `approved` · `deprecated` · `withdrawn`

Source: Blueprint §6.1.

## Roles and authorities

Role keys and authority keys are canonical enumerations too, but they carry enough policy to need their own document. See `docs/20-domain/ROLES-AND-PERMISSIONS.md`, which reconciles Constitution §5, Provisioning §25 and Customer Portfolio §12.

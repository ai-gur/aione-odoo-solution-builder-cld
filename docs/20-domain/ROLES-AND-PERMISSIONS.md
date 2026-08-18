# Roles, Authorities and Segregation of Duties

**Version:** 0.1
**Date:** 18 August 2026
**Status:** Proposed
**Resolves:** readiness blocker B6 (three incompatible role vocabularies)
**Sources reconciled:** Constitution §5, Provisioning §25, Customer Portfolio §12

## 1. Why three lists existed

The three specifications were describing different things in the same words.

- Constitution §5 lists **who a person is** in an engagement.
- Provisioning §25 lists **what a person is authorized to do** at a specific gate. "Manifest Compiler" is not a job; it is an authority that must be held separately from "Manifest Approver".
- Customer Portfolio §12 lists **portfolio-management responsibilities** over the long-lived customer relationship.

Collapsing them into one list produces either twenty roles or a role that means nothing. This document separates the two concepts that were conflated and keeps one list of each.

## 2. The model

Access requires all three layers. A role alone never grants access to anything (ADR-003 §10.2).

1. **Role** — a stable assignment held by a person within a tenant. Answers "who is this".
2. **Authority** — a named permission to perform one consequential action. Answers "may this action be taken". Roles hold default authorities; tenant policy may remove or add them.
3. **Scope** — tenant, customer, workspace, environment, or interview section assignment, plus current workflow state. Answers "on which record, right now".

A person may hold several roles. Every approval event records the **role under which the action was taken** and the authority exercised (Constitution §5).

## 3. Canonical roles

### 3.1 AIOne roles

| Role key | Purpose | Reconciles |
| --- | --- | --- |
| `platform_administrator` | Tenants, policies, catalogue releases, interview templates, platform access. Explicitly not a business approver | Constitution "Platform Administrator", Portfolio "Portfolio Administrator" |
| `account_owner` | **AIOne Account Manager.** Owns the customer relationship and is the interface between the customer and delivery. Conducts customer interviews, invites and chases respondents, carries customer requests into the delivery team, and works directly with the `solution_owner` | Portfolio "Account Owner" |
| `solution_owner` | **AIOne Team Lead.** Leads the team performing development and implementation. Owns one or more workspaces end to end, approves manifests and changes, and accepts baselines | Portfolio "Solution Owner" |
| `consultant` | Leads discovery, validates requirements, proposes and approves blueprint decisions | Constitution "AIOne Consultant", Portfolio "Consultant" |
| `solution_architect` | Reviews architecture, security, integrations, custom development and repository use | Constitution "AIOne Solution Architect", Portfolio "Solution Architect" |
| `provisioning_operator` | Authorizes and monitors provisioning runs; administers sandbox infrastructure | Constitution "Provisioning Operator", Provisioning "Provisioning Operator" and "Environment Administrator" |
| `repository_maintainer` | Manages approved code releases and software provenance | Portfolio "Repository Maintainer" |
| `auditor` | Read-only access to scoped immutable history and evidence. Never writes | Portfolio "Auditor" |

`environment_administrator` is folded into `provisioning_operator` for the MVP, where the same small team performs both. Splitting it later requires only an authority reassignment, not a data migration.

### 3.2 Customer roles

| Role key | Purpose | Reconciles |
| --- | --- | --- |
| `customer_sponsor` | Defines outcomes, priorities and scope; gives business acceptance | Constitution and Portfolio "Customer Sponsor" |
| `customer_process_owner` | Describes processes, rules and exceptions for assigned sections | Constitution and Portfolio "Customer Process Owner" |
| `customer_technical_contact` | Provides integration, data, identity and environment information | Constitution "Customer Technical Contact" |

Provisioning's "Customer Reviewer" is not a role. Sandbox review access is an authority (`sandbox.review`) granted to a customer role through workspace assignment, so that reviewing a released sandbox does not require inventing a fourth customer identity.

## 4. Authorities

| Authority key | Action | Default roles | Step-up | Notes |
| --- | --- | --- | --- | --- |
| `discovery.conduct` | Run interviews, assign sections, review answers | `account_owner`, `consultant` | — | The Account Manager normally runs the interview |
| `discovery.approve` | Approve an immutable discovery version | `consultant` | yes | |
| `requirement.approve` | Confirm normalized requirements | `consultant` | — | |
| `assumption.approve` | Approve an amber assumption affecting configuration | `consultant`, `solution_architect` | — | |
| `blueprint.propose` | Create and revise blueprint decisions | `consultant`, `solution_architect` | — | |
| `blueprint.approve` | Approve a specific blueprint version | `consultant` | yes | Constitution §11 gate 3 |
| `architecture.review` | Sign off integrations, custom development, complex security, multi-company | `solution_architect` | — | Blueprint §25 gate 3 |
| `manifest.compile` | Produce a candidate manifest | `consultant`, `provisioning_operator` | — | **Cannot approve it** |
| `manifest.approve` | Authorize a manifest for a named environment | `provisioning_operator`, `solution_owner` | yes | Constitution §11 gate 4 |
| `provisioning.execute` | Start, monitor, pause and retry an authorized run | `provisioning_operator` | yes | |
| `environment.administer` | Allocate, suspend, expire, rebuild, archive an environment | `provisioning_operator` | yes | Destroy stays out of MVP automation |
| `validation.review` | Review validation results | `consultant`, `solution_architect`, `provisioning_operator` | — | |
| `deviation.accept` | Accept a bounded deviation with owner, reason and expiry | `solution_architect`, `solution_owner` | yes | Constitution §11 gate 5 |
| `sandbox.review` | Access a released sandbox and complete review scenarios | `customer_sponsor`, `customer_process_owner`, `account_owner`, `consultant` | — | |
| `baseline.accept` | Set the Current Accepted baseline for a workspace | `solution_owner`, `customer_sponsor` | yes | AIOne and customer, per policy |
| `workspace.complete` | Confirm the engagement is delivered and release the workspace from the delivery team's active queue | `account_owner` | — | Transitions `accepted` → `operating`. Audited. Requires the workspace to already hold a Current Accepted baseline |
| `change.submit` | Raise and triage a change request against a baseline | `account_owner`, `consultant`, `solution_owner` | — | The customer's request reaches the system through the Account Manager |
| `change.approve` | Approve a change request for delivery | `solution_owner` | — | Delivery commitment belongs to the Team Lead |
| `repository.register` | Register a repository or software release | `repository_maintainer`, `solution_architect` | — | |
| `repository.release` | Mark a release approved for use in a manifest | `repository_maintainer` | yes | |
| `catalogue.publish` | Approve an immutable catalogue release | `platform_administrator`, `solution_architect` | yes | |
| `policy.manage` | Create and version tenant policies | `platform_administrator` | yes | |
| `membership.manage` | Invite, assign and remove members | `platform_administrator`, `solution_owner`, `account_owner` | — | Audited. The Account Manager invites customer respondents |
| `support.access.grant` | Grant time-bounded scoped support access | `platform_administrator` | yes | Expires automatically |
| `history.export` | Export scoped solution history or audit records | `auditor`, `solution_owner` | yes | The export is itself audited |

"Step-up" means re-authentication within the window set by `AUTH_STEP_UP_MAX_AGE_SECONDS`, recorded on the resulting event (ADR-014).

MFA is required for `consultant`, `solution_architect`, `provisioning_operator`, `repository_maintainer` and `platform_administrator`.

## 5. Segregation of duties

These are tenant policy defaults, enforced by the authorization service and covered by negative tests. A tenant may tighten them; it may not silently disable one.

| Constraint | Default | Basis |
| --- | --- | --- |
| The holder of `manifest.compile` may not exercise `manifest.approve` on the same manifest | Enforced, not configurable | Provisioning §25 |
| The person exercising `blueprint.approve` may not exercise `manifest.approve` for the same version line | **Off** for environment types `development` and `sandbox`; **enforced and not configurable** for any other type | Constitution §11 |
| The person exercising `provisioning.execute` may not exercise `deviation.accept` for that run | Configurable, on by default | Provisioning §25 |
| A customer role may never hold an AIOne authority | Enforced, not configurable | Customer isolation |
| `auditor` may hold no authority that writes | Enforced, not configurable | ADR-011 |
| No role may set approval, audit, confidence or calculated risk fields directly | Enforced, not configurable | Security baseline |

Self-approval of one's own proposal is permitted only where the same specification already contemplates it (a consultant approving a blueprint they assembled), and the approval event records both the proposer and the approver so the case is visible in audit.

**Segregation scales to blast radius, not to org chart.** A sandbox is disposable and the MVP prefers rebuilding one over repairing it, so requiring a second AIOne signature to provision one buys nothing and slows the team down daily. The same constraint is non-negotiable the moment an environment type outside `development` and `sandbox` enters scope, because the failure there is not recoverable by rebuilding. This is why the second constraint above is keyed to environment type rather than to a policy toggle a busy team would simply switch off.

There is no constraint requiring `account_owner` and `solution_owner` to confirm each other's actions. The two roles coordinate continuously outside the system, and a mandatory handshake between them would record consent that was already given verbally — audit theatre rather than control. The single exception is `workspace.complete`, which is not a check on the Team Lead's work but a distinct decision about the customer relationship: whether the engagement is finished from the customer's side and the workspace may leave the delivery queue.

## 6. Scope rules

- Authority is evaluated against tenant, customer, workspace and — for provisioning — one named environment.
- A respondent reaches only the interview sections assigned to them.
- Customer roles cannot enumerate other customers, workspaces or portfolio-wide data.
- Support access is time-bounded, scoped and audited; it expires without manual revocation.
- Workflow state is part of the check: approving a blueprint version that has been superseded fails on state, not on role.

## 7. Repository access is separate

Portal role does not grant source-code access (Portfolio §12). A `consultant` receives no repository permission by default. Git access is provisioned in the hosting provider against the repository registration, and `repository_maintainer` is the role accountable for it. The portal records who holds access; it is not the system that grants it.

## 8. Implementation notes

- Roles, authorities and their default mapping are seeded data with stable keys, versioned like any other policy.
- The client never supplies a role. It is resolved server-side from membership (ADR-014).
- Every authority check produces an audit event on denial as well as on success where the action is material.
- Increment 0 seeds `platform_administrator` and one `consultant` for the AIOne test tenant only; the full matrix arrives with Increment 1.
- Negative tests are required for: customer role attempting an AIOne authority, compiler attempting approval, auditor attempting any write, cross-workspace access, and expired support access.

## 9. Decisions and open items

**Decided 18 August 2026.** `account_owner` and `solution_owner` are distinct people at AIOne — Account Manager and Team Lead respectively. The eight-role AIOne set stands. Because the Account Manager conducts interviews and fronts the customer, that role holds `discovery.conduct`, `membership.manage`, `change.submit` and `sandbox.review`; it holds no approval authority. An Account Manager who also owns requirement quality holds the `consultant` role in addition, and the approval event records which role was used.

**Decided 18 August 2026.** The Team Lead may authorize a sandbox manifest alone. No second AIOne signature is required for `development` or `sandbox` environments, and no cross-confirmation exists between Account Manager and Team Lead. The two work together daily; a system-enforced handshake would add delay without adding control.

**Decided 18 August 2026.** The Account Manager confirms engagement completion (`workspace.complete`), which is what removes a workspace from the delivery team's active queue and moves it to `operating`. This is a relationship decision, not a review of the delivery work.

Open:

1. Confirm whether `baseline.accept` requires both an AIOne and a customer signature, or whether AIOne may accept on the customer's behalf with recorded evidence.
2. Confirm the step-up window. 300 seconds is proposed.
3. Confirm what happens to an engagement that ends without customer acceptance — abandoned, disputed or cancelled. `workspace.complete` currently requires an accepted baseline, so those workspaces would sit in the delivery queue indefinitely. A `workspace.close` authority with a recorded reason is the likely answer.

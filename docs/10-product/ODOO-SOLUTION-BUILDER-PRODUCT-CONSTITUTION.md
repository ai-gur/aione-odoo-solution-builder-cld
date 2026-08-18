# AIOne Odoo Solution Builder

## Product Constitution and Core Domain Model

**Version:** 0.1  
**Date:** 18 August 2026  
**Status:** Accepted  
**Accepted:** 18 August 2026  
**Approved by:** Nir Bar, founding partner, AIOne  
**Target platform:** Odoo Enterprise 19  

## 1. Purpose

The AIOne Odoo Solution Builder is a multi-customer control plane that helps AIOne interview a business, understand its operating model, generate an evidence-based Odoo solution blueprint, and provision a fresh, validated Odoo Enterprise 19 sandbox.

The product converts business discovery into structured, reviewable and traceable implementation decisions. It does not treat an AI-generated recommendation as authorization to change a production ERP system.

## 2. Initial product scope

The first release contains three connected capabilities:

1. **Discovery**: adaptive customer interviews, document-assisted discovery, structured requirements, assumptions, open questions and confidence scoring.
2. **Blueprint generation**: recommended Odoo applications, organizational structure, roles, workflows, localization, integrations, migration scope, gaps and implementation phases.
3. **Sandbox provisioning**: creation and deterministic configuration of a fresh Odoo Enterprise 19 sandbox from an approved, versioned deployment manifest.

## 3. Product principles

### 3.1 Business before software

The system first establishes how the organization operates, what problems it needs to solve, who performs and approves work, and how success will be measured. Odoo configuration follows that understanding.

### 3.2 Progressive discovery

Customers may begin with the shortest interview and provide more detail only where uncertainty, risk or complexity requires it.

The supported discovery modes are:

| Mode | Typical effort | Intended result |
| --- | ---: | --- |
| Quick Start | 10–15 minutes | Initial blueprint and demonstration sandbox |
| Guided Discovery | 35–60 minutes | Reliable blueprint and validated sandbox for a typical customer |
| Comprehensive Discovery | 2–4 workshops | Detailed architecture for complex implementations |

All modes write to the same domain model. Moving to a deeper mode enriches the existing discovery record rather than starting again.

### 3.3 Adaptive relevance

Questions are selected using prior answers, business type, identified processes, risk and confidence. The product must not require customers to answer irrelevant sections.

### 3.4 Standard Odoo first

Each requirement is evaluated in this order:

1. Standard Odoo Enterprise capability
2. Standard configuration
3. Approved localization, including Israeli accounting localization
4. Odoo Studio
5. Existing approved addon
6. Automation or integration
7. Isolated custom module

The selected approach, rejected alternatives and rationale are retained.

### 3.5 Evidence and traceability

Every blueprint decision must be traceable to one or more requirements, interview answers, documents, consultant decisions or validated system constraints.

Every applied configuration action must be traceable to an approved blueprint decision and a versioned deployment manifest.

### 3.6 Human authority

AI may ask questions, extract information, detect inconsistencies, propose requirements and recommend solutions. It may not approve its own blueprint or authorize provisioning.

An authorized AIOne consultant must approve a blueprint before sandbox provisioning.

### 3.7 Deterministic provisioning

Provisioning is performed by versioned, testable and idempotent configuration operations. A repeated run must converge on the approved state without creating duplicate records or silently overwriting protected customer data.

### 3.8 Honest uncertainty

The system must identify missing, conflicting, inferred and unverified information. It must not convert uncertainty into an undocumented assumption.

### 3.9 Separation of environments and customers

The control plane is separate from all provisioned Odoo databases. Customer tenants, credentials, artifacts and logs are isolated. Development, sandbox, staging and production environments are distinct.

### 3.10 Hebrew and English

The product supports Hebrew as a primary interface and discovery language with complete RTL behavior, and English US as a secondary language. Customer-facing Hebrew must be professional, direct, accessible and inclusive.

## 4. Explicit MVP boundaries

The MVP will:

- create and manage customer discovery projects;
- run Quick Start, Guided and Comprehensive interviews;
- accept relevant supporting documents;
- generate and version solution blueprints;
- require consultant review and approval;
- generate a machine-readable deployment manifest;
- provision fresh development or demonstration sandboxes;
- install approved Odoo 19 Enterprise applications and dependencies;
- apply supported baseline configuration;
- execute automated validation checks;
- retain logs, results and audit history.

The MVP will not:

- deploy automatically to production;
- execute a complete live data migration;
- deploy unreviewed AI-generated custom code;
- infer legal, tax or accounting policy without authorized confirmation;
- modify Odoo core or Enterprise source code;
- use one customer database to control another customer environment;
- represent a short interview as sufficient for a complex production implementation.

## 5. Users and responsibilities

| Role | Primary responsibility |
| --- | --- |
| Customer Sponsor | Defines outcomes, priorities, scope and final business acceptance |
| Customer Process Owner | Describes processes, rules, exceptions and operational needs |
| Customer Technical Contact | Provides integration, data, identity and environment information |
| AIOne Consultant | Leads discovery, validates requirements and approves blueprint decisions |
| AIOne Solution Architect | Reviews gaps, integrations, security and custom-development architecture |
| AIOne Provisioning Operator | Authorizes and monitors sandbox creation and configuration |
| Platform Administrator | Manages tenants, catalogues, policies, templates and platform access |

One person may hold several roles, but approval events must record the role under which the action was taken.

The canonical role keys, their authorities and the segregation-of-duties constraints are in `docs/20-domain/ROLES-AND-PERMISSIONS.md`, which reconciles this table with the Provisioning and Portfolio role lists.

## 6. End-to-end lifecycle

1. Create customer and solution workspace.
2. Select or recommend a discovery mode.
3. Conduct adaptive interview and collect supporting evidence.
4. Normalize answers into facts, processes, requirements, constraints and open questions.
5. Assess completeness, complexity, conflicts, risk and confidence.
6. Escalate only the necessary topics to deeper discovery.
7. Map approved requirements to the Odoo capability catalogue.
8. Generate blueprint decisions and implementation phases.
9. Review, revise and approve the blueprint.
10. Compile a versioned deployment manifest.
11. Authorize sandbox provisioning.
12. Apply configuration operations and record results.
13. Run automated validation.
14. Resolve failures or blueprint deviations.
15. Release the sandbox for consultant and customer review.

## 7. Core domain model

### 7.1 Tenant and engagement

#### AIOne Tenant

The organization operating the control plane. Owns global policies, catalogues, templates and platform users.

#### Customer Organization

The business being interviewed and implemented. Stores identity, countries, industries, size indicators and primary contacts. It does not itself contain the full implementation design.

#### Solution Workspace

The bounded engagement for a customer, and the long-lived container for one customer solution lifecycle. It owns discovery, requirements, blueprints, manifests, environments, baselines, change requests, approvals and audit history.

A customer may hold several workspaces when separate programmes have materially different scope, governance or Odoo environments. Workspaces are not created to represent ordinary implementation phases.

Amended 18 August 2026: the Solution Workspace replaces the former Implementation Project as this aggregate. The two described the same bounded engagement, and the Customer Solution Portfolio specification is the authority for its long-lived behaviour.

Key fields:

- workspace identifier and name;
- customer organization;
- lifecycle state;
- target Odoo version and edition;
- primary and secondary languages;
- countries and localization needs;
- selected discovery mode;
- responsible consultant and architect;
- scope, objectives and success measures;
- target dates and implementation phase;
- current accepted baseline and active change set;
- overall confidence, risk and completeness.

### 7.2 Discovery

#### Interview Definition

A versioned template describing a discovery mode, sections, questions, branching rules, validation rules and scoring behavior.

#### Interview Run

An execution of an interview definition within a solution workspace. A workspace may contain several runs, workshops or follow-up sessions.

#### Interview Section

A business domain such as sales, inventory, accounting, projects, HR, integrations or data migration. Sections may be skipped only with a recorded reason.

#### Question Definition

A versioned question with:

- stable question key;
- localized wording and help text;
- answer type and allowed options;
- applicability and branching conditions;
- whether it may be answered by a customer, consultant, document or system;
- importance, risk and confidence weights;
- linked business concepts and capability areas;
- validation and follow-up rules.

#### Answer

The response to a question in an interview run. An answer preserves original wording, normalized value, source, author, timestamp, confidence and verification state.

#### Evidence Item

A supporting file, excerpt, URL, observation or consultant note. Evidence may support or contradict facts, requirements and decisions.

#### Business Fact

A normalized statement about the customer, such as number of legal entities, use of serial numbers or existence of recurring billing. Facts may be confirmed, inferred, conflicting, superseded or unverified.

#### Assumption

A proposition temporarily used to progress the design. It includes rationale, impact, owner, expiry or review point, and approval state.

#### Open Question

Missing or conflicting information that requires customer, consultant or technical resolution. It has severity, owner, due date and blocking status.

### 7.3 Business architecture

#### Business Capability

Something the organization must be able to do, such as manage leads, replenish stock or approve supplier bills.

#### Business Process

A structured As-Is or To-Be flow with trigger, actors, steps, decisions, inputs, outputs, exceptions, controls and KPIs.

#### Organizational Unit

A legal entity, branch, department, site, warehouse, store or operational team relevant to the solution.

#### Business Role

A responsibility-based role independent of a named employee, such as Sales Manager or Inventory Receiver.

#### Approval Rule

A business control defining what requires approval, under which conditions, by which role and with what escalation.

#### Requirement

An atomic, testable need derived from discovery.

Required attributes:

- stable requirement identifier;
- title and unambiguous statement;
- business rationale and expected outcome;
- functional or non-functional classification;
- source and linked evidence;
- affected process, organizational unit and roles;
- priority using Must, Should, Could or Won't for the current release;
- acceptance criteria;
- status, owner and target phase;
- confidence, risk and completeness;
- dependencies and conflicts.

#### Constraint

A condition limiting the solution, including legal, contractual, technical, security, budget, timeline or operating constraints.

#### Success Measure

A baseline, target, measurement method, owner and review period used to determine whether the implementation creates the intended result.

### 7.4 Odoo knowledge and solution mapping

#### Capability Catalogue Entry

A versioned description of an Odoo capability, including:

- Odoo version and edition;
- application, module and dependencies;
- supported business outcomes;
- configuration options and limitations;
- localization relevance;
- required data and security considerations;
- known incompatibilities;
- provisioning handler availability;
- validation rules;
- source and verification date.

#### Solution Pattern

A reusable, versioned mapping for a common operating model, such as project-based professional services or wholesale distribution. A pattern proposes, but never silently approves, requirements and configuration.

#### Fit Assessment

The evaluated relationship between a requirement and Odoo capabilities.

Allowed classifications:

- standard fit;
- configuration fit;
- localization fit;
- Studio fit;
- approved addon fit;
- integration fit;
- custom-development gap;
- process-change candidate;
- unsupported or unresolved.

#### Blueprint

A versioned solution design for a solution workspace. A blueprint contains decisions, dependencies, gaps, phases, assumptions, risks and validation criteria.

Blueprint states:

- draft;
- under review;
- changes requested;
- approved;
- superseded;
- withdrawn.

#### Blueprint Decision

An atomic design decision linking requirements to selected Odoo capabilities and configuration. It records alternatives, rationale, confidence, impact and approver.

#### Gap

A requirement not fully satisfied by the selected standard solution. It records business impact, workaround, recommended treatment, estimate class and target phase.

#### Implementation Phase

A bounded delivery increment containing requirements, decisions, dependencies, acceptance criteria and intended business outcome.

### 7.5 Provisioning

#### Deployment Manifest

The immutable, machine-readable compilation of an approved blueprint for a specified target environment.

The manifest includes:

- schema and manifest version;
- project and blueprint version;
- target Odoo version and Enterprise edition;
- localization and language settings;
- company and organizational structure;
- modules and dependency versions;
- configuration operations in dependency order;
- required secrets by reference, never embedded values;
- baseline master-data packages;
- demonstration-data policy;
- expected validations;
- rollback and recovery metadata;
- content checksum and approval references.

#### Environment

A customer-specific Odoo target with an explicit type: development, sandbox, staging or production. The MVP may provision development and sandbox targets only.

#### Provisioning Plan

The resolved execution plan generated from a deployment manifest and the known current state of an environment.

#### Configuration Operation

An idempotent action such as installing a module, activating a language, creating a company, setting a configuration value or loading an approved data package.

Each operation declares:

- stable operation key;
- handler and handler version;
- prerequisites and dependency order;
- desired state and current-state check;
- input schema;
- sensitivity classification;
- execution and retry policy;
- validation method;
- rollback or compensating action;
- whether additional human authorization is required.

#### Provisioning Run

One execution of a provisioning plan. It records authorizer, timestamps, immutable inputs, operation results, logs and final status.

#### Operation Result

The outcome of one configuration operation: pending, running, applied, already compliant, skipped, failed, rolled back or manually resolved.

#### Validation Rule and Validation Result

A deterministic test of the provisioned environment and its recorded outcome. Validation may verify module state, configuration, access rights, expected records, workflows, language behavior and installation health.

#### Deviation

A difference between the approved manifest and the observed environment. Deviations are never silently accepted. They require correction, explicit acceptance or a new blueprint version.

### 7.6 Governance

#### Approval

A signed platform event recording subject, version, decision, role, person, timestamp and comments. Approval never carries automatically to a changed version.

#### Change Request

A controlled proposal to alter approved scope, requirements, blueprint decisions or provisioning behavior.

#### Audit Event

An append-only record of significant reads, writes, decisions, exports, approvals and provisioning actions.

#### Policy

A versioned AIOne rule governing matters such as approved addons, confidence thresholds, segregation of duties, environment permissions and mandatory validations.

## 8. Key relationships

- A Customer Organization has one or more Solution Workspaces.
- A Solution Workspace has many Interview Runs, but one current approved Blueprint per version line, and at most one Current Accepted baseline.
- Interview Answers and Evidence Items produce or support Business Facts, Requirements, Constraints, Assumptions and Open Questions.
- Requirements belong to business processes and are assessed against Capability Catalogue Entries.
- Fit Assessments produce proposed Blueprint Decisions and Gaps.
- An approved Blueprint compiles into one or more Deployment Manifests for defined environments.
- A Deployment Manifest produces Provisioning Plans and Provisioning Runs.
- Provisioning Runs produce Operation Results, Validation Results and Deviations.
- All approvals and material changes produce Audit Events.

## 9. Workspace lifecycle states

| State | Meaning |
| --- | --- |
| Proposed | Workspace shell exists; discovery has not started |
| Discovering | Interviews and evidence collection are active |
| Clarification Required | Blocking gaps or conflicts prevent reliable design |
| Designing | Requirements are being mapped to a solution |
| Blueprint Review | Consultant or architect review is active |
| Approved for Sandbox | A specific blueprint version is approved |
| Provisioning | An authorized sandbox run is active |
| Validation Failed | One or more blocking validations failed |
| Sandbox Active | Provisioning and mandatory validations succeeded; the sandbox is available |
| Customer Review | Customer testing and feedback are active |
| Revision Required | Discovery or blueprint changes are required |
| Accepted | The sandbox and documented scope were accepted, and a Current Accepted baseline exists |
| Operating | Delivery is complete; the workspace is in support and no longer in the delivery queue |
| Change In Progress | An approved change request is being delivered against the accepted baseline |
| Suspended | Work is paused; access and runtime may be disabled |
| Archived | Required artifacts retained; the workspace is inactive |
| Closed | The engagement is completed or terminated |

Canonical values are in `docs/20-domain/ENUMS.md`.

State transitions require explicit guards. A workspace cannot enter Approved for Sandbox while it has blocking open questions, unapproved red-confidence decisions or unresolved mandatory requirements. The transition from Accepted to Operating requires the `workspace.complete` authority and is what releases the workspace from the delivery team's active queue.

## 10. Confidence, completeness and risk

These are separate measurements and must not be collapsed into one score.

### Confidence

How strongly the available evidence supports a fact or decision:

- Green: sufficient verified information for the proposed action;
- Amber: action is possible with an explicit approved assumption;
- Red: consultant resolution is required before configuration.

### Completeness

Whether mandatory information for the selected scope has been collected. A project can have high-confidence answers but still be incomplete.

### Risk

The impact and likelihood of an incorrect decision or failed change. High-risk topics may require deeper discovery even when confidence appears high.

Provisioning eligibility is determined by policy using all three measures plus blocking status, not by a simple average.

## 11. Approval gates

The MVP requires explicit approval at these points:

1. Confirmation of normalized business requirements.
2. Approval of amber assumptions that affect configuration.
3. Approval of the complete blueprint version.
4. Authorization of a deployment manifest for a named sandbox.
5. Explicit acceptance or correction of any deviation.
6. Customer or consultant acceptance of the provisioned sandbox.

The blueprint approver and provisioning authorizer may be required to be different people according to tenant policy.

## 12. Provisioning safety invariants

1. Only an approved blueprint version may produce an executable manifest.
2. A manifest is immutable after approval; changes create a new version.
3. Secrets are stored and resolved outside the manifest.
4. Every operation checks current state before applying a change.
5. Every operation has a deterministic validation method.
6. Protected or destructive operations require explicit classification and authorization.
7. Failed operations stop dependent operations unless policy explicitly permits continuation.
8. The product never modifies Odoo core or Enterprise source.
9. Provisioning handlers are versioned and compatible with the declared Odoo version.
10. Mandatory validations must pass before an environment can be marked Ready and the workspace can enter Sandbox Active.
11. Logs must avoid exposing credentials or unnecessarily retaining personal data.
12. Production provisioning is prohibited in the MVP.

## 13. Initial aggregate boundaries

To keep the architecture maintainable, transactional consistency should be concentrated within these aggregates:

| Aggregate | Root | Contains |
| --- | --- | --- |
| Customer Engagement | Solution Workspace | scope, roles, objectives, lifecycle, baselines and workspace-level measures |
| Discovery | Interview Run | sections, questions, answers and interview progress |
| Requirements | Requirement | sources, acceptance criteria, dependencies and status |
| Blueprint | Blueprint | decisions, gaps, phases, review and version-specific approvals |
| Deployment | Deployment Manifest | immutable desired state and approval references |
| Provisioning | Provisioning Run | plan snapshot, operation results, validations and deviations |

Evidence, capability catalogue entries, policies and audit events are referenced shared records with their own lifecycle and access rules.

## 14. MVP success criteria

The MVP is successful when an authorized consultant can:

1. create a customer solution workspace;
2. complete any of the three discovery modes without duplicating prior answers;
3. see missing, contradictory and low-confidence information;
4. review structured requirements linked to their sources;
5. generate and revise an explainable Odoo 19 Enterprise blueprint;
6. approve a specific blueprint version;
7. compile a valid deployment manifest;
8. provision a fresh isolated sandbox from that manifest;
9. rerun provisioning safely;
10. inspect configuration and validation results;
11. trace each applied change back to its requirement and approval;
12. prevent an incomplete, unapproved or unsafe project from being provisioned.

## 15. Decisions deferred to the next design packages

The constitution intentionally does not yet fix:

- the exact Quick Start, Guided and Comprehensive question sets;
- question branching and scoring formulas;
- the detailed Odoo capability catalogue schema and initial entries;
- the blueprint document layout;
- the deployment manifest serialization format;
- the provisioning transport and infrastructure provider;
- application technology stack and hosting topology;
- credential-vault implementation;
- commercial packaging and pricing.

These decisions will be made against this constitution and must not weaken its approval, traceability, isolation or safety requirements.

## 16. Next design package

The next package should define the **Discovery Model and Interview Engine**, including:

- shared question taxonomy;
- the three interview definitions;
- branching and follow-up rules;
- answer normalization;
- document-assisted extraction;
- conflict detection;
- confidence, completeness and risk policies;
- escalation between interview modes;
- interview review and approval experience;
- discovery acceptance criteria.

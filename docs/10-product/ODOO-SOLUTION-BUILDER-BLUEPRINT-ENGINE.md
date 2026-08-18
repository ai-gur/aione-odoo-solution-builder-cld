# AIOne Odoo Solution Builder

## Blueprint Engine and Odoo Capability Catalogue

**Version:** 0.1  
**Date:** 18 August 2026  
**Status:** Accepted  
**Accepted:** 18 August 2026  
**Approved by:** Nir Bar, founding partner, AIOne  
**Depends on:** Product Constitution and Discovery Engine specifications  
**Target:** Odoo Enterprise 19

## 1. Objective

The Blueprint Engine converts an approved structured discovery package into an explainable, reviewable and versioned Odoo Enterprise 19 solution design.

It does not select applications from keywords alone. It evaluates each requirement against verified Odoo capabilities, configuration options, localization, security implications, dependencies, operational constraints and approved reusable patterns.

Its approved output is suitable for compilation into a machine-readable Deployment Manifest.

## 2. Inputs

The engine consumes an immutable approved Discovery Version containing:

- customer and implementation-project context;
- organizational units and business roles;
- confirmed facts and approved assumptions;
- business capabilities and As-Is/To-Be processes;
- atomic requirements and acceptance criteria;
- constraints, priorities and success measures;
- data, integration, reporting and security requirements;
- implementation phases and scope boundaries;
- confidence, completeness, complexity and risk metadata;
- evidence and approval references.

The engine may use only the approved version. Later discovery changes create a new candidate blueprint version.

## 3. Outputs

The engine produces:

1. Executive solution summary
2. Scope and assumptions
3. Recommended Odoo applications and modules
4. Organizational and company configuration
5. Process solution designs
6. Business-role to Odoo-access design
7. Approval and control design
8. Data and migration architecture
9. Integration architecture
10. Reporting and KPI design
11. Automation and AI design
12. Fit assessments and blueprint decisions
13. Gap register and custom-development backlog
14. Implementation phases and dependencies
15. Risks, open decisions and validation criteria
16. Estimated configuration and development effort classes
17. Structured blueprint package for manifest compilation

## 4. Non-negotiable decision hierarchy

Every requirement is evaluated in this order:

1. **Standard Odoo Enterprise capability**
2. **Standard Odoo configuration**
3. **Approved localization**, including Israeli localization where applicable
4. **Odoo Studio**
5. **Existing approved addon**
6. **Automation or integration**
7. **Isolated custom module**

An option lower in the hierarchy may be selected only when higher options do not adequately satisfy the requirement or create a demonstrably worse total outcome.

The rationale must consider:

- functional coverage;
- process change required;
- security and data integrity;
- maintainability and Odoo upgrade compatibility;
- performance and operational reliability;
- licensing and ownership;
- implementation and lifecycle cost;
- vendor dependency;
- customer priority and risk.

## 5. Core concepts

### 5.1 Odoo Capability

A business behavior supported by a specific, verified combination of Odoo edition, version, module and configuration.

Examples:

- manage sales opportunities through configurable pipeline stages;
- create quotations with customer-specific price lists;
- replenish products using reorder rules;
- invoice project milestones;
- restrict records by company and user role.

Capabilities are smaller than applications and more stable than screen labels.

### 5.2 Configuration Feature

A supported setting, record structure or operational option that enables or modifies a capability without custom source code.

### 5.3 Solution Pattern

A reusable composition of capabilities, configurations, roles, controls and validations for a common business model. Patterns accelerate design but remain proposals until project approval.

### 5.4 Fit Assessment

The analysis of how well a candidate solution satisfies one requirement in its business context.

### 5.5 Blueprint Decision

The approved or proposed selection of a solution approach for one or more requirements, including rationale, consequences, dependencies and validations.

### 5.6 Gap

The portion of a requirement not met by the selected standard solution.

## 6. Odoo Capability Catalogue architecture

The catalogue is versioned independently from customer projects. Catalogue changes do not silently alter an approved blueprint.

### 6.1 Catalogue release

Every usable catalogue has:

- catalogue release identifier;
- Odoo version and edition;
- compatible Odoo core and Enterprise source revisions;
- verification date;
- supported countries and localization packages;
- included addon repositories and approved revisions;
- status: draft, verifying, approved, deprecated or withdrawn;
- approver and release notes.

### 6.2 Application record

Represents a customer-recognizable Odoo application area.

Required attributes:

- stable application key;
- localized name and description;
- business domains served;
- primary technical modules;
- Enterprise or Community availability;
- licensing notes;
- installation prerequisites;
- common companion applications;
- known scope boundaries.

### 6.3 Module record

Represents an installable Odoo addon.

Required attributes:

- exact technical name;
- source repository and revision;
- manifest metadata;
- version, license and installable state;
- application flag;
- direct dependencies from `depends`;
- transitive dependency graph;
- data, demo and asset characteristics;
- external Python or binary dependencies;
- initialization or uninstall hooks;
- localization and country applicability;
- source authority and verification evidence;
- provisioning support state;
- install, update and uninstall risk classifications;
- automated test coverage metadata.

Module dependency truth must come from verified manifests for the target source revision. It must not be reconstructed from model memory.

### 6.4 Capability record

Required attributes:

- stable capability key;
- localized business description;
- domain and capability hierarchy;
- supported outcomes;
- Odoo version and edition;
- implementing application and modules;
- activation prerequisites;
- required configuration inputs;
- operational limitations;
- supported variations;
- affected models and security surfaces;
- compatibility and incompatibility rules;
- relevant localization;
- provisioning handler keys;
- validation rule keys;
- documentation and source references;
- verification date and status.

### 6.5 Configuration option

Required attributes:

- stable option key;
- owning capability;
- business explanation;
- allowed values and default behavior;
- configuration mechanism;
- required module and dependency state;
- company-specific or database-wide scope;
- required user privilege;
- reversibility and data impact;
- provisioning handler and current-state detector;
- validation method;
- known conflicts.

### 6.6 Localization record

Required attributes:

- country and language applicability;
- responsible publisher and source;
- module set and dependencies;
- accounting, tax, document and regulatory capabilities;
- configuration prerequisites;
- version and verification status;
- known limitations and required expert confirmations;
- supported provisioning operations and validations.

Israeli accounting localization is consumed as an approved capability set. The product must not recreate it as generic custom functionality.

### 6.7 Approved addon record

Third-party or AIOne addons require:

- repository, publisher and ownership;
- exact version or immutable revision;
- license and commercial terms;
- supported Odoo versions;
- security and code-review status;
- maintenance history and responsible owner;
- dependencies and conflicts;
- installation, migration and rollback guidance;
- automated tests and known limitations;
- approval status and expiry/review date.

An addon may not be recommended for provisioning unless its exact release is approved for the selected catalogue release.

### 6.8 Solution-pattern record

Required attributes:

- stable pattern key and version;
- intended business model and applicability rules;
- excluded or risky contexts;
- proposed applications, modules and configuration;
- assumed processes, roles and data;
- optional variants;
- generated discovery follow-ups;
- generated blueprint candidates;
- provisioning bundle references;
- expected validations;
- evidence and owner.

Initial candidate patterns:

- B2B wholesale distribution;
- B2C retail and eCommerce;
- professional services and projects;
- recurring services and subscriptions;
- field service organization;
- customer support operation;
- simple assembly;
- multi-company shared services.

Patterns are not installed as opaque packages. Their individual decisions remain visible and reviewable.

## 7. Catalogue taxonomy

The primary hierarchy is business-oriented:

```text
Domain
  Capability group
    Capability
      Variation
        Configuration option
```

Each capability also links to a technical hierarchy:

```text
Odoo edition and version
  Application
    Module
      Dependency
        Model / configuration surface
          Provisioning handler
          Validation rule
```

The two hierarchies must remain separate. Customers and consultants reason primarily in business capabilities; provisioning requires exact technical identities.

## 8. Catalogue evidence and maintenance

Acceptable sources, in authority order:

1. Verified Odoo 19 core and Enterprise source for the pinned revision
2. Official Odoo 19 documentation
3. Installed-system inspection against a clean reference database
4. Automated capability and configuration tests
5. Approved localization or addon source and documentation
6. AIOne verified implementation guidance

Every material catalogue claim records its source and last verification. AI-generated catalogue content remains draft until verified.

Catalogue maintenance lifecycle:

1. Detect source or module change.
2. Rebuild manifest and dependency facts.
3. Identify affected capabilities, handlers and validations.
4. Run catalogue verification tests.
5. Review changes and compatibility.
6. Publish a new immutable catalogue release.
7. Mark affected older entries deprecated or withdrawn where necessary.

## 9. Requirement-to-capability mapping

### 9.1 Candidate generation

For each approved requirement, the engine identifies candidates using:

- linked business capability and process;
- actors, organizational scope and operating conditions;
- data objects and transaction type;
- acceptance criteria;
- constraints and risks;
- catalogue relationships;
- approved solution patterns;
- related requirements and dependencies.

Semantic similarity may generate candidates but may not establish fit.

### 9.2 Deterministic eligibility filters

Candidates are removed or flagged when:

- they do not support Odoo Enterprise 19;
- required modules or addons are unavailable or unapproved;
- country or localization is incompatible;
- an explicit constraint is violated;
- required security behavior cannot be achieved safely;
- known volume or performance limits are exceeded;
- a dependency conflicts with another approved decision;
- the option cannot be provisioned or validated within the MVP boundary.

### 9.3 Fit evaluation dimensions

Each remaining candidate is evaluated across:

| Dimension | Question |
| --- | --- |
| Functional coverage | Does it satisfy normal flow, exceptions and acceptance criteria? |
| Standardness | How high is it in the decision hierarchy? |
| Process impact | What customer process change is required? |
| Security | Does it preserve access, audit and segregation needs? |
| Data integrity | Does it preserve canonical ownership and transaction integrity? |
| Localization | Does it fit the legal entity and country requirements? |
| Maintainability | Can it be upgraded, tested and supported reliably? |
| Performance | Is it appropriate for expected volume and peaks? |
| Provisionability | Can desired and current states be handled deterministically? |
| Testability | Can acceptance criteria be validated automatically or explicitly? |
| Lifecycle cost | What configuration, license, operation and upgrade cost follows? |
| Risk | What is the consequence of failure or incorrect configuration? |

Scores support review but do not replace rules or expert judgment.

## 10. Fit classifications

| Classification | Meaning |
| --- | --- |
| Standard Fit | Requirement is satisfied by installed standard behavior with no material change |
| Configuration Fit | Standard behavior satisfies it after supported configuration |
| Localization Fit | Approved country localization provides the required behavior |
| Studio Fit | Supported Studio configuration is appropriate and maintainable |
| Approved Addon Fit | An approved pinned addon adequately satisfies it |
| Integration Fit | Responsibility belongs partly or fully to an external system |
| Custom Development Gap | Isolated custom code is required |
| Process Change Candidate | Standard Odoo can meet the outcome if the customer changes its process |
| Partial Fit | Candidate satisfies only a defined portion of the requirement |
| Unsupported | No acceptable solution is currently available |
| Unresolved | Evidence or design authority is insufficient for selection |

Every Partial Fit must produce an explicit residual gap.

## 11. Blueprint decision model

Each Blueprint Decision contains:

- stable decision key and version;
- title and business explanation;
- linked requirements and acceptance criteria;
- affected processes, roles, units and data;
- selected fit classification;
- selected capabilities, applications and exact modules;
- required configuration options;
- localization, addon or integration references;
- alternatives considered;
- selection rationale;
- process changes and customer responsibilities;
- security and access consequences;
- dependencies and incompatibilities;
- provisioning-handler and validation-rule candidates;
- configuration and development effort classes;
- confidence, risk and impact;
- review state, owner and approval evidence.

Decision states:

- proposed;
- evidence required;
- under review;
- changes requested;
- accepted;
- rejected;
- approved;
- superseded.

## 12. Explainability requirements

For every proposed decision, the consultant must be able to answer:

1. Which customer requirement does this solve?
2. What evidence established the requirement?
3. What standard Odoo capability is being used?
4. Which exact modules and configurations are involved?
5. Why was this option selected?
6. Which alternatives were rejected and why?
7. What customer process change is expected?
8. What remains unsupported or uncertain?
9. What security, data or operational risks exist?
10. How will the configured result be validated?

Explanations shown to customers use business language. Technical details remain available to consultants and provisioning operators.

## 13. Dependency resolution

The engine builds a graph containing:

- requirement dependencies;
- process dependencies;
- module manifest dependencies;
- configuration prerequisites;
- organization and localization prerequisites;
- data and integration dependencies;
- security-role dependencies;
- implementation-phase dependencies.

The graph must detect:

- missing prerequisites;
- dependency cycles outside supported module behavior;
- incompatible configuration options;
- duplicate capability coverage;
- decisions made impossible by a later constraint;
- modules included only as transitive dependencies;
- removed modules still required by approved decisions.

The blueprint distinguishes:

- **business-selected modules**, directly justified by requirements;
- **technical dependencies**, installed because another module requires them;
- **platform baseline modules**, supplied by the Foundation.

## 14. Application and module recommendation rules

The blueprint must not recommend an application simply because the customer recognized its name.

An application is included when:

- at least one approved in-scope requirement maps to a verified capability it provides;
- dependencies and localization are compatible;
- its inclusion does not create an unresolved material conflict;
- the intended configuration and validation are understood.

The application is marked optional when it supports a Could requirement or future phase only. Future-phase modules are not installed in the initial sandbox unless explicitly approved for demonstration.

## 15. Security architecture generation

The engine maps Business Roles to Odoo 19 security constructs without equating job titles directly to unrestricted groups.

The design considers:

- privileges and groups;
- implied group relationships;
- model access rights;
- record rules;
- company access;
- field-level restrictions where necessary;
- approval authority;
- portal versus internal access;
- sensitive configuration access;
- segregation-of-duties conflicts.

For Odoo 19 custom security design, privilege definitions use `res.groups.privilege`; group access is additive; record-rule behavior and global-rule intersection must be explicitly reviewed.

Generated security recommendations remain proposed until a consultant validates:

- least privilege;
- multi-company behavior;
- record visibility;
- create, read, write and delete rights;
- approval bypass paths;
- administrator and service-account handling.

The Blueprint Engine must never propose `sudo()` as a general solution to an access-design problem.

## 16. Organizational and company design

The blueprint distinguishes:

- legal companies;
- branches and operating units;
- warehouses and stock locations;
- departments and teams;
- analytic structures;
- websites and sales channels;
- currencies, languages and countries.

It must not create a separate Odoo company merely to represent a department or reporting dimension. The rationale for every company boundary is documented, including accounting, ownership, currency, localization, intercompany and access consequences.

## 17. Data architecture

For every significant object, the blueprint defines:

- business owner;
- system of record;
- Odoo model or conceptual destination;
- required identifiers and duplicate policy;
- company ownership and sharing behavior;
- mandatory fields and validation;
- migration scope and history boundary;
- reconciliation method;
- archive and retention expectations;
- dependent processes and integrations.

The blueprint separates:

- configuration data;
- master data;
- opening balances and open transactions;
- historical transactions;
- documents and attachments;
- demonstration data.

## 18. Integration architecture

Each integration decision defines:

- business purpose and owner;
- source and destination systems;
- authoritative system per data object;
- direction and trigger;
- frequency, latency and volume;
- field and identity mapping;
- authentication and secret references;
- idempotency and duplicate handling;
- error, retry and reconciliation behavior;
- monitoring and support ownership;
- privacy and retention;
- sandbox test approach;
- fallback and continuity behavior.

The MVP blueprint may specify integrations even when the initial sandbox uses a stub or excludes live connectivity. The difference must be explicit.

## 19. Automation and AI design

Automation candidates are evaluated only after the underlying process, owner, data and exception handling are understood.

Every automation or AI decision includes:

- trigger and intended outcome;
- deterministic inputs and output schema;
- decision authority and approval threshold;
- confidence and fallback behavior;
- idempotency and retry policy;
- privacy and allowed data access;
- human review or escalation;
- audit event requirements;
- measurable efficiency or quality target;
- monitoring and disable mechanism.

AI is not allowed unrestricted record access or direct high-impact writes without deterministic validation and explicit policy.

## 20. Gap management

Each Gap records:

- linked requirement and unsupported portion;
- business impact and priority;
- reason standard approaches are insufficient;
- workaround or process-change option;
- recommended treatment;
- affected data, security and integrations;
- effort class and uncertainty;
- target implementation phase;
- acceptance criteria;
- owner and decision deadline.

Custom-development candidates require a separate approved design packet before code generation or deployment.

## 21. Effort classes

The blueprint uses relative effort classes before detailed estimation:

| Class | Meaning |
| --- | --- |
| XS | Minor standard configuration with known validation |
| S | Bounded configuration or data setup in one domain |
| M | Multi-step configuration, Studio work or simple integration |
| L | Cross-domain design, complex integration or bounded custom module |
| XL | Major process, migration, integration or custom-development work requiring separate design |

Effort class is not a commercial quotation. It records complexity and estimation confidence separately.

## 22. Implementation phasing

The engine proposes phases using:

- Must/Should/Could priority;
- business value and success measures;
- prerequisite dependencies;
- process coherence;
- data and integration readiness;
- organizational capacity;
- risk reduction;
- sandbox validation value.

Default phase model:

1. Foundation and organizational baseline
2. Core master data and security
3. Minimum coherent operational flow
4. Supporting operational domains
5. Integrations and migration rehearsal
6. Advanced automation, reporting and optimization

A phase must deliver a coherent business outcome. The engine must not split tightly coupled transactions merely to make phases appear smaller.

## 23. Blueprint document structure

### Part A: Business-facing blueprint

1. Executive summary
2. Objectives and success measures
3. Scope, exclusions and assumptions
4. Future operating model
5. Process solutions
6. Applications and capabilities
7. Roles and approvals
8. Data and integrations
9. Reporting and automation
10. Gaps and decisions required
11. Implementation phases
12. Risks and customer responsibilities

### Part B: Technical blueprint

1. Target platform and catalogue release
2. Exact module and dependency set
3. Company and organizational configuration
4. Configuration specifications
5. Security architecture
6. Data architecture and migration objects
7. Integration contracts
8. Addon and custom-module architecture
9. Provisioning-handler mapping
10. Validation plan
11. Environment and operational requirements
12. Manifest compilation inputs

### Part C: Traceability

- requirement-to-decision matrix;
- decision-to-capability matrix;
- decision-to-module and configuration matrix;
- decision-to-validation matrix;
- assumptions, approvals and change history.

## 24. Blueprint versioning

Every blueprint version records:

- immutable version identifier;
- source discovery version;
- capability-catalogue release;
- solution-pattern versions;
- generation engine and rule-set versions;
- author and reviewers;
- status and timestamps;
- difference from previous version;
- approvals and approval invalidation events.

Changing any decision, requirement mapping, module set, security design or manifest-relevant configuration creates a new blueprint version.

## 25. Review and approval gates

### Gate 1: Automated consistency

- source discovery is approved;
- every Must requirement has a fit assessment;
- partial fits have residual gaps;
- dependency graph resolves;
- all modules exist in the selected catalogue release;
- no withdrawn addon is selected;
- required localization is addressed;
- validation candidates exist for provisioned decisions.

### Gate 2: Functional consultant review

- process solution is coherent;
- requirements and acceptance criteria are satisfied;
- process changes and assumptions are explicit;
- application scope is justified;
- implementation phases are practical.

### Gate 3: Architecture review

Required for integrations, custom development, complex security, multi-company, advanced manufacturing, high-volume operations or high-risk migration.

### Gate 4: Customer review

The sponsor and designated process owners confirm business scope, process changes, gaps, responsibilities and phase priorities.

### Gate 5: Approval for sandbox

An authorized AIOne consultant approves a specific blueprint version for manifest compilation. Approval does not authorize production deployment.

## 26. Change impact analysis

When discovery or a blueprint decision changes, the engine identifies:

- affected requirements and processes;
- invalidated decisions;
- added or removed modules;
- dependency changes;
- security consequences;
- data and integration changes;
- affected phases and estimates;
- validations to add or rerun;
- whether prior approval is invalidated;
- whether an existing sandbox deviates from the new desired state.

The system presents impact before accepting the change.

## 27. Example trace

### Discovery requirement

> The system shall require Sales Manager approval before confirming a quotation with a discount above 10%.

### Candidate evaluation

- Standard quotation behavior: partial fit; quotations supported, threshold approval not yet established.
- Standard configuration or approved approval capability: candidate pending catalogue verification.
- Studio automation: candidate if standard approval capability cannot satisfy the threshold and audit need.
- Custom module: rejected unless higher options cannot meet security, audit and maintainability requirements.

### Proposed blueprint decision

- Use the highest verified standard approval mechanism capable of enforcing the threshold before confirmation.
- Map Salesperson and Sales Manager business roles to reviewed Odoo privileges and groups.
- Configure the 10% threshold as company-specific if supported and required.
- Validate that an ordinary salesperson cannot bypass approval by RPC, import or alternate confirmation path.
- Record an unresolved catalogue verification item rather than inventing the exact technical module or field.

This example demonstrates that the engine may produce a sound design direction while refusing to fabricate unverified Odoo internals.

## 28. Structured blueprint package

The blueprint package passed to the Manifest Compiler contains conceptual sections equivalent to:

```yaml
blueprint:
  id: bp_example
  version: 1
  discovery_version: discovery_3
  catalogue_release: odoo19_catalogue_2026_08
  target:
    edition: enterprise
    version: "19.0"
  scope: {}
  organizations: []
  business_roles: []
  requirements: []
  decisions: []
  applications: []
  modules:
    selected: []
    dependencies: []
  configurations: []
  security_design: {}
  data_design: {}
  integrations: []
  gaps: []
  phases: []
  validations: []
  assumptions: []
  approvals: []
```

This is a conceptual contract, not the final serialization schema.

## 29. Core screens

### Consultant-facing

1. Blueprint overview and readiness
2. Requirement-to-capability workbench
3. Application and module map
4. Process solution editor
5. Organizational design
6. Role, access and approval matrix
7. Data and integration design
8. Gap and custom-development register
9. Phase planner
10. Risk, assumption and open-decision view
11. Traceability matrix
12. Version comparison
13. Review and approval

### Customer-facing

1. Objectives and scope summary
2. Proposed future processes
3. Recommended application capabilities
4. Required customer decisions and process changes
5. Gaps, exclusions and responsibilities
6. Implementation phases
7. Review comments and approval

Technical module names are available but not allowed to overwhelm the customer-facing explanation.

## 30. Blueprint Engine acceptance criteria

The engine is acceptable for MVP when:

1. It consumes only an approved immutable discovery version.
2. It uses a pinned approved Odoo 19 capability-catalogue release.
3. Every Must requirement receives a fit assessment or explicit unresolved blocker.
4. Recommendations follow the mandated solution hierarchy.
5. Every selected application and module is justified by requirements or technical dependencies.
6. Exact technical module claims come from verified catalogue data.
7. Partial fits create residual gaps.
8. Alternatives and rationale are visible.
9. Security, data, localization and integration consequences are represented.
10. Dependency and incompatibility checks are deterministic.
11. The engine proposes coherent implementation phases.
12. Consultant changes preserve reason and audit history.
13. Blueprint versions are immutable after approval.
14. Approval is invalidated by material changes.
15. The approved structured package can be compiled without parsing the narrative document.
16. Unverified Odoo internals remain unresolved rather than fabricated.

## 31. Initial API boundary

The Blueprint Engine must expose operations equivalent to:

- create blueprint from approved discovery;
- select catalogue release;
- generate capability candidates;
- evaluate and compare fit;
- propose or revise blueprint decision;
- resolve dependencies and incompatibilities;
- generate organizational, security, data and integration designs;
- register gaps and process-change candidates;
- propose implementation phases;
- run automated consistency checks;
- compare blueprint versions;
- request functional or architecture review;
- approve or reject blueprint version;
- export customer-facing blueprint;
- export structured blueprint package;
- calculate change impact.

Exact protocol and endpoint design are deferred.

## 32. Next design package

The next package should define the **Deployment Manifest and Sandbox Provisioning Engine**, including:

- manifest schema and compilation;
- environment and credential boundaries;
- module installation planning;
- idempotent configuration operations;
- desired-state and current-state comparison;
- execution, retry and rollback behavior;
- automated Odoo 19 validation;
- deviations and reconciliation;
- sandbox lifecycle and acceptance;
- provisioning security and audit.

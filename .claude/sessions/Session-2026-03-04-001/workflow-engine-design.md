# Unified Workflow Engine: Design Proposal

**Author:** Claude (Orchestrator)
**Date:** 2026-03-04
**Context:** CR-108 Genesis Sandbox — DocuBuilder redesign from document-centric to workflow-centric architecture

---

## 1. The Problem

The QMS manages AI agent orchestration through controlled documents. These documents — Change Records, Investigations, Variance Reports, Verification Records — are not really documents. They are **workflow instances**: structured sequences of steps with ordering constraints, evidence requirements, prerequisite gates, deviation handling, and multi-actor coordination.

The current system works, but it encodes workflow logic in three places that don't talk to each other:

1. **SOP prose** — Human-readable instructions that agents must internalize ("RS must be EFFECTIVE before merge")
2. **Template structure** — Implicit workflow encoded in section ordering, placeholder conventions, and comment blocks
3. **Agent judgment** — The agent remembers (or forgets) ordering constraints, evidence requirements, and cross-document choreography

This distribution means that every workflow execution depends on the agent correctly reading, understanding, and following prose instructions scattered across 12 SOPs, 9 templates, and a 500-line CLAUDE.md. When agents get it wrong — and they do (INV-009: merge before RTM approval; INV-010: CR closed before RTM EFFECTIVE; INV-012/014: direct commits to main) — the failure is discovered during post-review, after the damage is done.

**The core insight:** If the workflow engine enforced ordering constraints, prerequisite gates, and evidence requirements programmatically, the entire category of "agent didn't follow the process" failures would be eliminated by construction.

**The unifying insight:** The interactive prompting pattern — "answer the next prompt" — is itself a workflow. It is the *bootstrap workflow*: the workflow that creates all other workflows. Template authoring, instance drafting, and execution are all the same experience: the system presents a prompt, the agent responds, the system advances. The entire architecture reduces to one primitive operation repeated at every layer.

---

## 2. What We Learned from Research

### 2.1 From the QMS's Own History

Analysis of 100+ CRs, 14 INVs, and all SOPs reveals:

**Recurring failure modes that workflow enforcement would prevent:**
- Merging code before SDLC documents are EFFECTIVE (INV-009, INV-010)
- Modifying production code outside execution branches (INV-006, INV-012, INV-014)
- Closing CRs before child documents reach required state (CR-036 post-review rejection)
- Leaving placeholder content in documents routed for review (CR-043, CR-036-VAR-001)
- Executing work outside pre-approved scope without formal deviation handling

**Workflow complexity that demands automation:**
- CR-036 touched 18 EIs, 5 VARs, RS, RTM, 6 agent files, CI, a PR, and a submodule pointer — all with ordering dependencies
- CR-056 spawned 3 VARs, which spawned 2 child CRs (CR-057, CR-058), creating a 5-document dependency chain
- The SDLC qualification chain (implement → CI → qualified commit → RTM with commit → RTM EFFECTIVE → merge) has 6 links, each dependent on the previous

**The recursive self-improvement pattern works:**
- Each of the 14 INVs produced both corrective and preventive actions
- SOPs evolved from v1.0 to v16.0 through iterative improvement driven by real failures
- The system gets better over time — but only because humans catch the failures during review

### 2.2 From External Research

**From statecharts (XState/Harel):** The QMS document lifecycle is already a state machine. Making it explicit — with hierarchical sub-states for execution phases, guards on transitions for prerequisite gates, and actions for audit trail entries — is the right modeling paradigm.

**From Temporal.io:** The parent-child workflow pattern with lifecycle policies (child must complete before parent can close) directly models VAR Type 1/Type 2 semantics. The event history as source of truth validates our audit trail design.

**From GMP Electronic Batch Records:** The Master Record / Batch Record separation (template defines what should happen, instance records what did happen) is exactly the right two-tier model. Deviation handling should be an embedded sub-process, not a separate document.

**From Dagster:** Evidence should be treated as typed assets with declared upstream dependencies. Each step declares what evidence it produces; downstream steps declare what evidence they consume. The system validates completeness mechanically.

**From van der Aalst workflow patterns:** The key patterns we need are Sequence, Parallel Split, Synchronization (AND-join for multi-reviewer gates), Exclusive Choice (approve vs. reject), Deferred Choice (human decides), and Milestone (prerequisite gates). We need about 10 of the 43 catalogued patterns.

**From 21 CFR Part 11 / ALCOA+:** Our audit trail design is sound. The key principle to preserve: every event carries who, when, what, and why — immutable, contemporaneous, and complete.

### 2.3 From the DocuBuilder Prototype

**What worked:** The data model (JSON-serializable), enforce/locked system, sequential execution with cascade revert, ALCOA+-aligned audit trail, and the checkout/checkin interaction model.

**What didn't work:** The document metaphor constrained workflow thinking. Tables-as-steps, sections-as-phases, and cells-as-evidence are workflow concepts wearing document clothes. Cross-table prerequisites are impossible. The single-command-per-cycle interaction is slow. Navigation overhead (sections, expand/collapse) adds friction without value.

---

## 3. Design Principles

### P1: Workflows, Not Documents

The primary abstraction is a **workflow** — a directed graph of steps with ordering constraints, evidence requirements, and gates. The document is a *rendered view* of the workflow state, not the thing itself.

### P2: Templates Define Workflows, Instances Execute Them

A **workflow template** declares: what steps exist, their ordering, what evidence each step requires, what gates control transitions, and who can perform each step. A **workflow instance** is a running execution of a template that captures actual evidence, actual performers, actual timestamps, and any deviations.

### P3: The Engine Enforces What SOPs Currently Describe

If an ordering constraint exists in SOP prose today, it should be a programmatic gate in the engine tomorrow. The agent shouldn't need to remember that "RS must be EFFECTIVE before RTM can reference it" — the engine should refuse to advance the RTM step until the RS gate is satisfied.

### P4: Inheritance Without Fragility

Base workflow templates define invariant structure (pre-execution commit, post-execution commit). Specialized templates extend the base by inserting steps into declared extension points. Invariant steps cannot be removed or reordered by derived templates.

### P5: Multi-Workflow Orchestration is First-Class

A workflow step can spawn a child workflow in another document. The parent declares a lifecycle policy for each child: must the child complete before the parent can advance? The engine tracks these dependencies and enforces them at the parent's gates.

### P6: Evidence is Typed and Validated

Each step declares what evidence it produces, with a type schema. The engine validates that evidence matches the declared type before allowing the step to complete. "Commit hash" is a type. "Pass/Fail" is a type. "Document ID at EFFECTIVE status" is a type.

### P7: Deviation is a Sub-Workflow, Not a Separate Document

When a step fails, the engine enters a deviation sub-workflow embedded in that step. The deviation has its own lifecycle (classify → investigate → resolve → verify). For minor deviations, the sub-workflow resolves inline. For major deviations, the sub-workflow spawns a formal INV as a child workflow.

### P8: ALCOA+ by Construction

The engine guarantees ALCOA+ compliance structurally:
- **Attributable:** Every event records the performer
- **Contemporaneous:** Evidence is captured at step completion, not retrospectively
- **Original:** The event log is append-only
- **Accurate:** Evidence types are validated against schemas
- **Complete:** Steps cannot complete without all required evidence

### P9: The System Carries Process Knowledge, the Agent Carries Domain Knowledge

An agent executing a workflow should never need to read an SOP, memorize a template convention, or understand the internal mechanics of the engine. The system tells the agent what to do next, what evidence is required, and what gates are blocking progress. The agent's only job is to *do the work* and *provide the evidence*.

This means:
- **No SOP memorization.** SOPs define templates and gate logic. Once encoded, the workflow *is* the SOP — the agent never reads it.
- **No ordering logic.** The engine knows step 7 is gated on steps 5 and 6. The agent sees "blocked — waiting on steps 5, 6." It doesn't need to know why.
- **No command sequencing.** Instead of remembering "checkout, edit, checkin, route review, wait, route approval," the agent sees "Current action: provide evidence for step 3" and the engine handles the plumbing.
- **No error through ignorance.** You can't fill in an RTM commit hash before CI passes, because the gate won't open. You can't skip a step, because the engine tracks completion. You can't merge before qualification, because the merge gate checks signals.

The rendered view is the **entire interface**. An agent sees a list of steps — some completed, one active, some blocked with reasons — and acts on the active one. Template authors encode the process knowledge once; every agent benefits from it forever. The cognitive load shifts from *every executor learning the process* to *one author encoding the process*.

### P10: One Interaction Model, All Layers (The Bootstrap Principle)

The interactive prompting pattern — "system presents a prompt, agent responds, system advances" — is the universal interaction model for the entire engine. It is used at every layer:

- **Template authoring:** "What is the next step? Who performs it? What evidence is needed?"
- **Instance drafting:** "This template has 7 steps. Add custom steps? Fill in descriptions?"
- **Execution:** "Step 4: Run CI pipeline. Evidence needed: CI run URL, pass/fail."
- **Deviation handling:** "Step failed. Classify: minor/major/critical?"

This is not a coincidence — it's the architecture. The prompting system is itself a workflow: a sequence of steps (prompts), with gates (conditional prompts based on previous answers), evidence (the responses), and completion (all prompts answered). It is the **bootstrap workflow** — the one hardcoded workflow that exists before any templates do, and the workflow that creates all other workflows.

The recursive structure:
1. The **bootstrap workflow** (hardcoded) guides an author through defining a workflow template
2. **Workflow templates** (created by the bootstrap) guide an author through drafting a workflow instance
3. **Workflow instances** (created from templates) guide an executor through completing work

Every layer uses the same engine, the same renderer, the same audit trail, the same gate logic. An agent that can answer prompts can operate at any layer. The entire system reduces to one primitive operation: **answer the next prompt**.

---

## 4. Core Model

### 4.1 Primitives

The engine has five primitives:

```
WorkflowTemplate    — defines what a workflow looks like (the "recipe")
WorkflowInstance    — a running execution of a template (the "batch record")
Step                — a unit of work with inputs, outputs, and a performer
Gate                — a condition that must be true before a step can proceed
Signal              — a typed output from one step that feeds into another's gate
```

Everything else — phases, evidence, ordering, prerequisites — is composed from these five primitives.

### 4.2 Step Anatomy

A step is the atomic unit of work:

```yaml
step:
  id: update-rtm
  name: Update RTM with verification evidence
  performer: initiator              # role, not person
  phase: qualification              # grouping (display only)

  # What must be true before this step can start
  gates:
    - signal: qualified-commit      # output from a previous step
      condition: exists
    - signal: rs-status
      condition: equals EFFECTIVE

  # What this step produces
  outputs:
    - signal: rtm-updated
      type: boolean
    - evidence: rtm-commit
      type: commit-hash
      description: "Commit hash of RTM checkin"

  # What evidence the performer must provide
  evidence:
    - field: execution-summary
      type: narrative
      required: true
    - field: commit-hash
      type: commit-hash
      required: true
    - field: outcome
      type: pass-fail
      required: true

  # What happens on failure
  on-failure: deviation             # enters deviation sub-workflow
```

### 4.3 Gate Mechanics

Gates are the enforcement mechanism. A gate evaluates to true or false based on signals:

```yaml
gate:
  name: merge-gate
  description: "All SDLC prerequisites for code merge"
  conditions:
    - signal: rs-status
      condition: equals EFFECTIVE
    - signal: rtm-status
      condition: equals EFFECTIVE
    - signal: ci-status
      condition: equals passing
  mode: all                         # all conditions must be true (AND-join)
```

Gates can also reference external state:

```yaml
gate:
  name: child-closure-gate
  description: "All Type 1 children must be closed"
  conditions:
    - external: children
      filter: { type: VAR, var-type: 1 }
      condition: all-at-state CLOSED
    - external: children
      filter: { type: VAR, var-type: 2 }
      condition: all-at-state PRE_APPROVED  # or later
```

### 4.4 Signals

Signals are typed values that flow between steps:

```yaml
# Step A produces a signal
step: run-ci
outputs:
  - signal: qualified-commit
    type: commit-hash
  - signal: ci-status
    type: enum [passing, failing]

# Step B consumes it via a gate
step: update-rtm
gates:
  - signal: qualified-commit
    condition: exists
  - signal: ci-status
    condition: equals passing
```

Signals are the mechanism that replaces "the agent remembers to copy the commit hash from the CI step into the RTM." The commit hash flows through the workflow as data, not as a manual transcription.

### 4.5 Phases

Phases are display-only groupings of steps. They have no behavioral semantics — they exist purely to organize the rendered view:

```yaml
phases:
  - id: setup
    name: "Test Environment Setup"
    steps: [create-branch, verify-env]

  - id: implementation
    name: "Implementation"
    steps: [implement-code, write-tests]

  - id: qualification
    name: "Qualification"
    steps: [run-ci, update-rs, update-rtm]

  - id: merge
    name: "Merge and Release"
    steps: [merge-pr, update-submodule]
```

The ordering of steps is determined by gates and signal dependencies, not by phase membership. Phases are a human convenience.

### 4.6 The Three-Layer Model: Template → Instance (Drafting) → Instance (Execution)

The relationship between templates and instances has three distinct phases, each with different mutability rules:

**Layer 1: Template (controlled document)**

The workflow template is a QMS-controlled document defining the standard workflow for a document type. It declares:
- Invariant steps (cannot be removed at any layer)
- Standard steps (present by default, cannot be removed at instance level)
- Required metadata fields (cannot be removed at instance level)
- Gates, signals, evidence schemas for all template-defined steps
- Extension points where instances can add custom steps

Changing a template requires its own CR. Template changes do not affect existing instances.

**Layer 2: Instance — Drafting Phase**

When an instance (e.g., CR-XYZ) is created from a template, the author enters a drafting phase where:
- **All template-defined steps are inherited and cannot be deleted.** The author sees them, can fill in their descriptive fields (name, description), but cannot remove them.
- **All template-defined metadata fields are inherited and cannot be deleted.** The author must fill them in (Purpose, Scope, Justification, etc.) but cannot remove the fields themselves.
- **The author CAN add custom steps** at the template's extension points. These are specific to this CR's scope (e.g., "EI-4: Implement the frobnitz handler"). Custom steps have the same structure as template steps — they declare evidence requirements, gates, signals.
- **The author CAN fill in descriptive fields** on all steps (template-defined and custom): task description, VR flag, phase assignment.
- **The author CANNOT fill in execution fields** — outcome, execution summary, performer signature. These do not exist yet.

Drafting ends when the instance is routed for pre-review. The pre-approval review validates the complete workflow: template-inherited steps + author-added steps + all metadata fields filled.

**Layer 3: Instance — Execution Phase (post pre-approval and release)**

After pre-approval and release for execution:
- **The step list is frozen.** No adding, removing, or reordering steps. The workflow definition approved by reviewers is the contract.
- **Step definitions are frozen.** Task descriptions, evidence requirements, VR flags, gates — all immutable.
- **Metadata fields are frozen.** Purpose, Scope, Justification — locked.
- **Only execution fields are writable:** execution summary, outcome (pass/fail), performer signature, evidence values.
- **Execution fields are append-only.** Once a step is completed, its evidence can only be amended through the formal amendment mechanism (which records both the original and the amendment in the audit trail).

If the executor discovers that a step is missing, unnecessary, or incorrectly defined, they cannot modify the frozen workflow. They must create a VAR (deviation) to formally authorize the scope change. The engine enforces this — the `add-step` command is simply not available on a released instance.

**The provenance chain:** Every step in a released instance carries a `source` attribute:
- `source: template` — inherited from the workflow template (undeletable from creation)
- `source: author` — added by the author during drafting (undeletable after pre-approval)

This provenance is visible in the rendered view and auditable in the event log. Reviewers can see exactly which steps came from the standard template and which were added for this specific CR.

---

## 5. Template Inheritance

### 5.1 Base Executable Template

Every executable document (CR, INV, VAR, ADD, TP, ER) shares invariant structure:

```yaml
template: executable-base
type: abstract                      # cannot be instantiated directly

lifecycle:
  pre-phase:
    states: [DRAFT, IN_PRE_REVIEW, PRE_REVIEWED, IN_PRE_APPROVAL, PRE_APPROVED]
  release-gate: true
  post-phase:
    states: [IN_EXECUTION, IN_POST_REVIEW, POST_REVIEWED, IN_POST_APPROVAL, POST_APPROVED, CLOSED]

invariant-steps:
  first:
    - id: pre-execution-commit
      name: "Pre-execution baseline commit"
      performer: initiator
      evidence:
        - field: commit-hash
          type: commit-hash
          required: true
      outputs:
        - signal: pre-execution-baseline
          type: commit-hash

  last:
    - id: post-execution-commit
      name: "Post-execution baseline commit"
      performer: initiator
      evidence:
        - field: commit-hash
          type: commit-hash
          required: true

extension-points:
  - id: execution-body
    position: between first and last invariants
    description: "Derived templates insert their execution steps here"
```

### 5.2 Code CR Template (extends executable-base)

```yaml
template: code-cr
extends: executable-base

metadata:
  - field: target-systems
    type: list[system-id]
    required: true
  - field: execution-branch
    type: string
    required: true

extension-point: execution-body
steps:
  - id: setup-env
    name: "Set up test environment"
    phase: setup
    performer: initiator
    evidence:
      - field: execution-summary
        type: narrative
      - field: outcome
        type: pass-fail

  - id: update-rs
    name: "Update Requirements Specification"
    phase: requirements
    performer: initiator
    outputs:
      - signal: rs-status
        type: document-status
    evidence:
      - field: rs-doc-id
        type: document-id
      - field: outcome
        type: pass-fail

  - id: implement
    name: "Implement changes per Change Description"
    phase: implementation
    performer: initiator
    evidence:
      - field: execution-summary
        type: narrative
      - field: commits
        type: list[commit-hash]
      - field: outcome
        type: pass-fail

  - id: run-ci
    name: "Run tests, verify CI passes"
    phase: qualification
    performer: initiator
    gates:
      - signal: implementation-complete
        condition: exists
    outputs:
      - signal: qualified-commit
        type: commit-hash
      - signal: ci-status
        type: enum [passing, failing]
    evidence:
      - field: qualified-commit
        type: commit-hash
      - field: test-count
        type: string
      - field: outcome
        type: pass-fail

  - id: integration-verification
    name: "Exercise changed functionality in running system"
    phase: qualification
    performer: initiator
    gates:
      - signal: ci-status
        condition: equals passing
    child-workflow:
      type: VR                      # spawns a Verification Record
      policy: REQUIRE_COMPLETE
    evidence:
      - field: vr-id
        type: document-id
      - field: execution-summary
        type: narrative
      - field: outcome
        type: pass-fail

  - id: update-rtm
    name: "Update RTM with verification evidence"
    phase: qualification
    performer: initiator
    gates:
      - signal: qualified-commit
        condition: exists
      - signal: rs-status
        condition: at-state EFFECTIVE
    outputs:
      - signal: rtm-status
        type: document-status
    evidence:
      - field: rtm-doc-id
        type: document-id
      - field: outcome
        type: pass-fail

  - id: merge
    name: "Merge execution branch to main"
    phase: merge
    performer: initiator
    gates:
      - name: merge-gate
        conditions:
          - signal: rs-status
            condition: at-state EFFECTIVE
          - signal: rtm-status
            condition: at-state EFFECTIVE
          - signal: ci-status
            condition: equals passing
        mode: all
    evidence:
      - field: pr-url
        type: url
      - field: merge-commit
        type: commit-hash
      - field: outcome
        type: pass-fail

  - id: update-submodule
    name: "Update submodule pointer in parent repo"
    phase: merge
    performer: initiator
    gates:
      - signal: merge-commit
        condition: exists
    evidence:
      - field: commit-hash
        type: commit-hash
      - field: outcome
        type: pass-fail
```

### 5.3 Document-Only CR Template (extends executable-base)

```yaml
template: document-cr
extends: executable-base

extension-point: execution-body
steps:
  - id: checkout-docs
    name: "Check out target documents"
    performer: initiator
    evidence:
      - field: doc-ids
        type: list[document-id]
      - field: outcome
        type: pass-fail

  - id: make-changes
    name: "Make changes per Change Description"
    performer: initiator
    evidence:
      - field: execution-summary
        type: narrative
      - field: outcome
        type: pass-fail

  - id: route-docs
    name: "Check in and route for review/approval"
    performer: initiator
    gates:
      - signal: changes-complete
        condition: exists
    evidence:
      - field: doc-ids
        type: list[document-id]
      - field: outcome
        type: pass-fail
```

No RS, no RTM, no merge gate — because there is no code.

### 5.4 Template CR (extends code-cr)

```yaml
template: template-cr
extends: code-cr

# Additional steps for template alignment
additional-steps:
  - id: align-templates
    name: "Verify QMS/TEMPLATE and qms-cli/seed/templates match"
    phase: implementation
    after: implement
    performer: initiator
    evidence:
      - field: alignment-check
        type: narrative
      - field: outcome
        type: pass-fail
```

Three levels of inheritance: `executable-base → code-cr → template-cr`. Each level adds steps without modifying the parent's invariants.

---

## 6. Multi-Workflow Orchestration

### 6.1 Child Workflow Spawning

When a step declares a child workflow, the engine creates a new workflow instance linked to the parent:

```yaml
step: integration-verification
child-workflow:
  type: VR
  policy: REQUIRE_COMPLETE       # parent step can't complete until VR closes
  inherit:
    - signal: qualified-commit   # child receives parent's signals
```

### 6.2 Lifecycle Policies

| Policy | Parent Behavior | QMS Mapping |
|--------|----------------|-------------|
| `REQUIRE_COMPLETE` | Parent step blocks until child reaches terminal state | VAR Type 1: must be CLOSED |
| `REQUIRE_APPROVED` | Parent step blocks until child is pre-approved | VAR Type 2: must be PRE_APPROVED |
| `CASCADE_CLOSE` | Child is auto-closed when parent closes | VR: cascade-closed with parent |
| `INDEPENDENT` | Child lifecycle is independent of parent | ADD: parent already closed |

### 6.3 Cross-Workflow Signal Propagation

Signals can propagate across workflow boundaries:

```yaml
# Parent CR's merge step gates on child VR completion
step: merge
gates:
  - child-workflow: integration-vr
    condition: at-state CLOSED

# Parent INV gates closure on child CR completion
step: close-investigation
gates:
  - children:
      filter: { type: CR }
      condition: all-at-state CLOSED
```

### 6.4 The SDLC Coordination Problem

The hardest multi-workflow challenge in the QMS is the SDLC coordination for code CRs. The dependency chain is:

```
CR step: implement
    ↓ (produces code on execution branch)
CR step: run-ci
    ↓ (produces signal: qualified-commit)
RS workflow: checkout → edit → checkin → review → approve → EFFECTIVE
    ↓ (produces signal: rs-status = EFFECTIVE)
RTM workflow: checkout → edit (insert qualified-commit) → checkin → review → approve → EFFECTIVE
    ↓ (produces signal: rtm-status = EFFECTIVE)
    ↓ (gate: rs-status = EFFECTIVE — RTM can't finalize without RS)
    ↓ (gate: qualified-commit exists — RTM must reference the actual commit)
CR step: merge
    ↓ (gate: rs-status = EFFECTIVE AND rtm-status = EFFECTIVE AND ci-status = passing)
CR step: update-submodule
```

In the current system, this chain is enforced by prose instructions and reviewer vigilance. In the workflow engine, it's enforced by gates:

- The RTM update step has a gate requiring `qualified-commit` signal (output from CI step)
- The RTM update step has a gate requiring `rs-status = EFFECTIVE` (output from RS workflow)
- The merge step has a gate requiring both `rs-status = EFFECTIVE` and `rtm-status = EFFECTIVE`
- The merge step has a gate requiring `ci-status = passing`

The agent literally cannot merge until all four conditions are satisfied. Not because it read the SOP and remembers — because the engine refuses to advance the step.

---

## 7. Deviation Handling

### 7.1 Inline Deviation

When a step fails, the engine doesn't stop. It transitions the step into a deviation sub-workflow:

```
Step: implement
  Status: IN_PROGRESS
    ↓ (step fails)
  Status: DEVIATED
    ↓ (deviation sub-workflow begins)
    ├── Classify severity (minor / major / critical)
    ├── Record root cause
    ├── Determine resolution path:
    │   ├── Minor: resolve inline, continue
    │   ├── Major: spawn child VAR, block step
    │   └── Critical: spawn child INV, block workflow
    ↓ (deviation resolved)
  Status: COMPLETED (with deviation record attached)
```

### 7.2 Deviation Records vs. Child Documents

The current system creates a separate VAR document for every execution failure. This is heavyweight for minor issues (a test that fails and is fixed in the same session) and appropriate for major issues (a fundamental design flaw requiring rework).

The workflow engine supports both:

- **Inline deviation:** Recorded as part of the step's audit trail. No separate document. Appropriate for minor issues resolved within the same step.
- **Child workflow deviation:** Spawns a VAR (or INV) as a child workflow. The parent step blocks until the child resolves. Appropriate for issues requiring their own review/approval cycle.

The severity classification determines which path:

```yaml
deviation:
  severity: minor
  resolution: inline
  record:
    description: "Test failed due to missing fixture. Added fixture, re-ran, passed."
    evidence: { commit: abc123 }

deviation:
  severity: major
  resolution: child-workflow
  child:
    type: VAR
    var-type: 1
    policy: REQUIRE_COMPLETE
```

---

## 8. The Rendered View

The workflow engine's internal model is steps, gates, and signals. But agents interact with a **rendered view** — a markdown document that presents the current workflow state in a format designed for AI consumption.

### 8.1 Rendering Philosophy

The rendered view answers three questions:
1. **What has been done?** (completed steps with evidence)
2. **What can be done now?** (steps whose gates are satisfied)
3. **What is blocked and why?** (steps whose gates are not satisfied, with specific unsatisfied conditions)

It does NOT include:
- Navigation infrastructure (no sections to navigate between)
- Document editing commands (no text blocks to edit)
- Structural authoring commands (no tables to add/remove)

### 8.2 Example Rendered View

```markdown
# CR-108: DocuBuilder Genesis Sandbox

## Workflow Status: IN_EXECUTION (Phase: Qualification)

### Completed Steps

| Step | Description | Outcome | Evidence | Performed |
|------|-------------|---------|----------|-----------|
| EI-1 | Pre-execution baseline commit | Pass | `6798bf5` | claude - 2026-03-03 |
| EI-2 | Set up test environment | Pass | docu-builder/ created | claude - 2026-03-03 |
| EI-3 | Implement prototype | Pass | model.py, renderer.py, ... | claude - 2026-03-04 |
| EI-4 | Run CI, verify tests pass | Pass | 20/20 tests, commit `c004388` | claude - 2026-03-04 |

### Ready Steps

| Step | Description | Requirements |
|------|-------------|-------------|
| EI-5 | Integration verification | Provide: VR document ID, execution summary, pass/fail |

### Blocked Steps

| Step | Description | Blocked By |
|------|-------------|------------|
| EI-6 | Update RTM | Waiting: RS at EFFECTIVE (current: DRAFT), qualified-commit signal |
| EI-7 | Merge to main | Waiting: RS EFFECTIVE, RTM EFFECTIVE, CI passing |
| EI-8 | Post-execution baseline | Waiting: EI-7 (merge) |

### Commands

>> complete EI-5 outcome=pass evidence="VR CR-108-VR-001 completed" vr-id=CR-108-VR-001
```

### 8.3 The Command Interface

The command set changes based on the instance's lifecycle phase:

**Drafting Phase (DRAFT):**

| Command | Purpose |
|---------|---------|
| `set <field> <value>` | Set a metadata field value (Purpose, Scope, etc.) |
| `add-step <id> <name>` | Add a custom step at an extension point |
| `edit-step <step-id> <field> <value>` | Edit a step's descriptive fields (description, VR flag, etc.) |
| `delete-step <step-id>` | Delete an author-added step (`source: author` only — template steps cannot be deleted) |
| `inspect <step-id>` | Show step details |
| `status` | Show workflow state and completeness for routing |

**Execution Phase (IN_EXECUTION):**

| Command | Purpose |
|---------|---------|
| `complete <step-id>` | Complete a step with evidence |
| `deviate <step-id>` | Enter deviation sub-workflow for a step |
| `status` | Show current workflow state |
| `inspect <step-id>` | Show detailed step info (gates, evidence schema, signals) |
| `signal <name> <value>` | Manually set a signal value (for external events) |

No `add-step`, `delete-step`, or `edit-step` in execution phase. The workflow structure is frozen after pre-approval. The only thing the executor does is complete steps and provide evidence.

In both phases: no `nav`, no `add_section`, no `add_table`, no `edit_text`. The structural complexity of the DocuBuilder prototype is eliminated.

---

## 9. Template Authoring and Instance Drafting

### 9.1 Template Definition

Templates are authored in YAML. A template defines the standard workflow for a document type:

```yaml
template:
  id: code-cr
  name: "Code Change Record"
  extends: executable-base
  version: 1.0

  # Metadata fields — inherited by all instances, cannot be deleted during drafting
  metadata:
    - field: purpose
      type: narrative
      required: true
    - field: scope
      type: narrative
      required: true
    - field: current-state
      type: narrative
      required: true
    - field: proposed-state
      type: narrative
      required: true
    - field: change-description
      type: narrative
      required: true
    - field: justification
      type: narrative
      required: true
    - field: impact-assessment
      type: narrative
      required: true
    - field: testing-summary
      type: narrative
      required: true
    - field: target-systems
      type: list[system-id]
      required: true
    - field: execution-branch
      type: string
      required: true

  # Steps inserted into the base template's extension point
  # These are inherited by all instances and cannot be deleted during drafting
  steps:
    # ... (as shown in Section 5.2)

  # Deviation handling configuration
  deviation:
    minor: inline
    major: spawn-var
    critical: spawn-inv
```

### 9.2 Template as Controlled Document

Workflow templates are themselves QMS-controlled documents. Changing a template requires a CR. This preserves the recursive governance property: the system that defines workflows is itself governed by workflows.

### 9.3 Instance Creation and Drafting

When a new CR is created from a template, the engine:

1. Reads the template definition
2. Resolves inheritance chain (e.g., `template-cr → code-cr → executable-base`)
3. Assembles the complete step list (invariant + inherited + template-specific)
4. Stamps all template-defined steps with `source: template`
5. Stamps all template-defined metadata fields with `source: template`
6. Creates the workflow instance in DRAFT state
7. Enters the drafting phase

**During drafting, the author can:**
- Fill in metadata field values (Purpose, Scope, Justification, etc.)
- Add custom steps at extension points, with `source: author`
- Fill in descriptive fields on all steps (task description, VR flag, evidence requirements)
- Set gates and signal definitions on custom steps
- Assign custom steps to phases

**During drafting, the author CANNOT:**
- Delete template-defined steps (`source: template`)
- Delete template-defined metadata fields (`source: template`)
- Modify the structure of inherited invariant steps (pre/post execution commits)
- Fill in execution-time fields (outcome, execution summary, performer)

**The engine validates at route-for-review:**
- All required metadata fields have values (no empty required fields)
- All steps have task descriptions
- All custom steps have evidence requirements defined
- Gate references are valid (signals referenced in gates are produced by upstream steps)

### 9.4 The Pre-Approval Lock

When an instance is pre-approved and released for execution:

1. The complete step list (template + author) is frozen
2. All step definitions are frozen (descriptions, evidence schemas, gates, signals)
3. All metadata fields are frozen
4. Each step gains execution fields: outcome, execution-summary, performer-date
5. The instance enters IN_EXECUTION state

From this point forward, the only writable fields are execution fields on individual steps. The workflow structure is the contract that was reviewed and approved.

### 9.5 What Happens When Scope Needs to Change

If during execution the author discovers that:
- A step is unnecessary → Mark it **Fail**, create a Type 2 VAR explaining why
- A step is missing → Create a VAR to authorize the additional work
- A step description is wrong but intent is clear → Execute the intent, document the discrepancy in the execution summary
- A step description is wrong and intent is wrong → Create a Type 1 VAR

The engine does not allow adding or removing steps from a released instance. This matches the current QMS policy: pre-approved scope is a contract, and changing it requires a paper trail.

### 9.6 Template Evolution

When a template is revised (new version), existing instances are NOT automatically migrated. They continue to execute under the template version they were created with. This is deliberate: changing the rules mid-execution would undermine the pre-approval contract.

New instances created after the template revision use the new version. This is the same principle as the current QMS: a running CR follows the SOPs that were in force when it was approved.

---

## 10. What This Replaces

### 10.1 Current → Proposed Mapping

| Current Concept | Proposed Concept |
|----------------|------------------|
| CR sections 1-9 (pre-approved content) | Workflow template + metadata fields |
| CR section 10 (EI table) | Workflow steps with evidence |
| CR section 11 (Execution Summary) | Automatically generated from step outcomes |
| Section lock boundary | Template definition is immutable; evidence is append-only |
| `{{PLACEHOLDER}}` conventions | Metadata field declarations with types |
| `[SQUARE_BRACKET]` execution fields | Step evidence fields with schemas |
| Template comment blocks (usage guides) | Template schema (self-documenting) |
| SOP prose ordering constraints | Gates with signal conditions |
| Agent judgment about step ordering | Engine-enforced dependency resolution |
| Manual evidence transcription (copying commit hashes between documents) | Signal propagation between steps |
| Sections as organizational containers | Phases as display-only groupings |
| Text blocks | Metadata narrative fields |
| Tables with typed columns | Steps with typed evidence fields |
| Prerequisites (`{id} complete`) | Gates with signal conditions |
| Sequential execution | Step ordering derived from gate dependencies |
| Cascade revert on amendment | Deviation sub-workflow with audit trail |
| Enforce/locked system | Template provenance (`source: template` = undeletable) + pre-approval lock (all steps frozen) |
| `qms interact` prompt sequence | Step-by-step evidence collection |
| `checkout/edit/checkin` cycle | `complete <step>` command |

### 10.2 What Stays

- **The QMS CLI** — workflow operations are CLI commands
- **The audit trail** — append-only event log per workflow instance
- **The metadata sidecar** — workflow state in `.meta/`
- **The review/approval cycle** — human judgment gates
- **Role-based permissions** — who can perform which steps
- **ALCOA+ principles** — evidence integrity by construction
- **The recursive governance loop** — workflows govern workflow template changes

### 10.3 What Disappears

- **Document-centric terminology** — no more "sections," "text blocks," "element IDs"
- **Navigation** — no table of contents, no section expand/collapse, no `nav` command
- **Structural authoring commands** — no `add_section`, `add_table`, `add_row`, `add_column`
- **Free-form text editing** — no `edit_text`
- **The two-phase model** (authoring/execution) as a DocuBuilder concept — replaced by the QMS's own lifecycle states
- **Column type system** — replaced by evidence type system
- **Element naming and ID schemes** (TXT-0, TBL-1, SEC-N) — replaced by step IDs
- **The render/parse cycle** for every mutation — replaced by direct step completion

---

## 11. Open Questions

### Q1: How does the rendered view handle pre-approval content?

The CR template's sections 1-9 (Purpose, Scope, Current State, Proposed State, etc.) are currently free-text prose written during drafting. In the workflow model, these become metadata fields. But metadata fields are key-value pairs, not rich documents with subsections.

**Options:**
- (a) Metadata fields can be multi-line narratives (markdown-formatted text). The rendered view presents them as-is. Simple, but loses the structured section layout.
- (b) The template defines a "document structure" alongside the workflow structure. The document structure is a rendering template (Jinja2) that presents metadata fields in a formatted layout. This preserves the current CR's readable structure while keeping the data model clean.
- (c) Pre-approval content is authored as a separate artifact (a markdown document) that accompanies the workflow. The workflow instance references it but doesn't contain it.

**Recommendation:** Option (b). The workflow template includes a Jinja2 rendering template that produces the human-readable document from metadata fields. This connects directly to CR-107's unified document lifecycle.

### Q2: ~~How configurable should step ordering be at instance creation time?~~ RESOLVED

**Answer:** The author can add custom steps during drafting but cannot delete template-defined steps. Template steps carry `source: template` provenance and are undeletable from creation. Author-added steps carry `source: author` and are deletable during drafting but locked after pre-approval. Pre-approval freezes the complete step list. See Section 4.6 (Three-Layer Model) and Section 9.3 (Instance Creation and Drafting) for the full specification.

### Q3: How does this interact with CR-107's unified document lifecycle?

CR-107 introduces universal source files, Jinja2 rendering, and `.meta/` as the data store. The workflow engine's rendered view is exactly the kind of "source + context → rendered output" pipeline that CR-107 defines.

**Integration path:** The workflow engine stores its state in `.meta/` (steps, signals, evidence, deviation records). The Jinja2 rendering template in `.source/` defines how to present that state as a human-readable document. `qms read` renders the workflow state through the Jinja2 template to produce the document view.

### Q4: Can the same engine handle non-executable documents?

SOPs, RS, and RTM have simpler lifecycles (no execution phase). Could the workflow engine model them as workflows with only a "drafting" phase and a review/approval gate?

**Answer:** Yes. A non-executable document is a degenerate workflow with one step: "author the content." The evidence is the document content itself. The gates are the review/approval cycle. This unification means one engine handles all document types.

### Q5: How does the interactive authoring system (VR prompts) fit?

The current `qms interact` system drives a prompt-by-prompt authoring flow for VRs. In the workflow model, each VR prompt becomes a step with an evidence field. The VR's loop construct (`@loop: steps`) becomes a repeatable step group. The gate construct (`@gate: more_steps`) becomes a conditional gate.

This is a natural mapping. The interactive engine IS a workflow engine — it just didn't know it yet.

### Q6: What about the document as a review artifact?

Reviewers currently read a markdown document. The workflow engine must produce a rendered view that is equally readable for review purposes. The rendered view in Section 8.2 shows completed steps, ready steps, and blocked steps — but reviewers also need to see the *plan* (all steps, including future ones) and the *metadata* (purpose, scope, justification).

**Answer:** The rendered view for review includes everything: metadata fields (the plan), the complete step list (the workflow), and evidence (the execution). The difference is that during execution, the rendered view emphasizes what's actionable (ready steps). During review, it presents the complete picture.

---

## 12. Migration Path

### 12.1 From DocuBuilder Prototype

The DocuBuilder prototype code in `docu-builder/` is a genesis sandbox artifact. The workflow engine would be a new implementation, not a refactor of the prototype. However, several prototype components carry forward:

- **The audit trail model** (append-only entries with performer, timestamp, value, reason) — this is sound and maps directly to the workflow event log
- **The enforce/locked concept** — maps to template invariant steps
- **The prerequisite evaluation logic** — maps to gate evaluation, though generalized from "row X complete" to arbitrary signal conditions
- **The cascade revert concept** — maps to deviation handling with automatic downstream impact

### 12.2 From Current QMS

The migration from the current QMS to workflow-engine-driven documents would be incremental:

1. **Phase 1:** Build the workflow engine with support for the code-CR workflow template
2. **Phase 2:** Create a code-CR workflow template that produces the same rendered output as the current TEMPLATE-CR.md
3. **Phase 3:** Run new CRs through the workflow engine while existing CRs complete under the current system
4. **Phase 4:** Add INV, VAR, VR, ADD workflow templates
5. **Phase 5:** Add non-executable document support (SOP, RS, RTM)
6. **Phase 6:** Retire the old template system

Each phase is independently valuable. Phase 1-2 alone would eliminate the "agent forgot the SDLC ordering" class of failures for code CRs.

---

## 13. Relationship to Existing Design Artifacts

### 13.1 CR-107 (Unified Document Lifecycle)

CR-107's Jinja2 render engine, universal source files, and `.meta/` data store are the **infrastructure layer** that the workflow engine runs on. The workflow engine stores its state in `.meta/`, defines its rendering templates as Jinja2 sources in `.source/`, and produces rendered drafts as derived artifacts. CR-107 is not replaced — it becomes the foundation.

### 13.2 CR-106 (System Governance)

CR-106's system checkout/checkin, qualification gate, and RTM metadata propagation are **workflow steps** in the code-CR template. The qualification gate (`check_qualification_gate()`) becomes a gate in the workflow engine, evaluated against signals from the CI step and the RTM workflow.

### 13.3 CR-108 (DocuBuilder Genesis Sandbox)

CR-108's prototype work produced the insights that drive this design. The prototype's table/section/text-block model is replaced by the step/gate/signal model. The prototype's sequential execution, prerequisite blocking, cascade revert, and enforce/locked concepts are preserved but elevated from document primitives to workflow primitives.

---

## 14. Summary

DocuBuilder started as a document editor and evolved into a workflow execution interface. This design proposal completes that evolution by dropping the document metaphor entirely and building from workflow-first principles.

The core bet: **if workflows are defined as steps with typed evidence requirements and gate conditions, and the engine enforces those constraints programmatically, then the entire category of "agent didn't follow the process" failures is eliminated by construction.**

The five primitives (WorkflowTemplate, WorkflowInstance, Step, Gate, Signal) are sufficient to model every document type in the QMS, from a simple SOP (one step: author content) to a complex code CR with SDLC coordination (20+ steps with cross-workflow signal propagation).

The rendered view is a derived artifact — a markdown document generated from workflow state for human and AI consumption. The agent interacts with the workflow by completing steps, not by editing documents.

The template inheritance system (executable-base → code-cr → template-cr) encodes invariant structure (pre/post execution commits) while allowing specialization (SDLC gates for code CRs, alignment verification for template CRs).

The deviation handling model (inline for minor issues, child workflow for major issues) reduces the overhead of formal variance reports for trivial failures while preserving full traceability for significant deviations.

And the ALCOA+ compliance is structural, not procedural. The engine guarantees attribution, contemporaneity, originality, accuracy, and completeness by construction — not by hoping the agent reads the SOP and remembers.

---

**END OF DOCUMENT**

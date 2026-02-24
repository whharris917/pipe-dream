# Unified State Machine Framework — Design Discussion

**Source:** Ghost Session during Session-2026-02-23-002
**Context:** Design discussion about unifying all QMS orchestration — document lifecycles, EI execution, review gates, child document dependencies, SDLC prerequisites, and merge gates — into a single declarative state machine framework.

---

## 1. Problem Statement

Code-changing CRs repeatedly fail at the same procedural steps: missing pre/post execution baselines, incomplete qualification, merge gate violations, silently dropped EIs, out-of-order execution. The root cause is that EIs are freehand markdown rows with no enforcement mechanism. The table is just text. Nothing prevents starting EI-8 before EI-5, or routing for post-review with blank EIs.

The current enforcement model relies on agents reading SOPs, internalizing them, and faithfully executing every step from memory during a long execution phase. This is a human-trust model. For AI agents who lose context across compaction and get focused on implementation work, it doesn't hold. QA catches violations in post-review, but by then the work is already done wrong and remediation is expensive. The enforcement happens too late.

### Specific Recurring Failures

1. **Missing pre/post execution baselines** — agent jumps straight into coding
2. **Qualification skipped or incomplete** — tests run but RS/RTM not updated, or updated but not approved before merge
3. **Merge gate violations** — code merged without PR, or with squash, or before SDLC docs are EFFECTIVE
4. **EIs silently dropped** — planned EIs never get outcomes recorded, caught only in post-review
5. **Out-of-order execution** — agent does merge before qualification, or starts coding before the branch is set up

---

## 2. Current State: Six Enforcement Mechanisms

The QMS currently has at least six distinct enforcement mechanisms, each implemented as ad-hoc procedural checks scattered across the CLI:

| Mechanism | What It Enforces | How It's Implemented |
|-----------|-----------------|---------------------|
| **Document lifecycle** | State transitions with role-based permissions | Procedural checks in each CLI command |
| **Review gates** | request-updates blocks approval; all-responded triggers REVIEWED | Ad-hoc logic in route/review commands |
| **Child document dependencies** | Type 1 VAR must be CLOSED before parent closes | Ad-hoc checks in close command |
| **EI execution** | Nothing — entirely freehand | **Not enforced** |
| **SDLC prerequisites** | RS/RTM must be EFFECTIVE for CR closure | Conceptual only (SOP guidance) |
| **Merge gate** | CI + RS + RTM before code reaches main | Conceptual only (SOP guidance) |

Every single one of these is the same thing: **a state, with transitions, guarded by conditions that may reference the state of other entities.**

---

## 3. The Core Insight

The QMS is already a graph of stateful entities with guarded transitions. It is just implemented as scattered procedural checks that don't know about each other.

A document lifecycle is a state machine. EI execution is a state machine. A review assignment is a state machine (assigned → complete). An SDLC prerequisite is a guard on a transition. A child dependency is a guard on a transition. A merge gate is a guard on a transition. They are all the same pattern, implemented six different ways.

**Unification:** Everything is a node in a directed graph. Each node has a state machine. Transitions between states are guarded by conditions that can reference other nodes' states.

---

## 4. The Unified Abstraction

### Node

```
Node
  id: string                    # "CR-045", "CR-045/EI-3", "CR-045/review/qa"
  type: string                  # "document", "ei", "review_assignment", "sdlc_gate"
  machine: StateMachine         # states + transitions
  state: string                 # current state
  edges: [Node]                 # dependencies (other nodes this one references)
```

### Transition

```
Transition
  from: State
  to: State
  trigger: string               # "route_review", "approve", "start", "complete"
  guards: [Guard]
```

### Guard

```
Guard
  condition: (node, graph) → bool
  description: string           # human-readable: "All reviewers must recommend"
  blocking: (node, graph) → string  # specific: "tu_ui has not reviewed"
```

A guard that currently lives as a procedural `if` statement in `route.py` becomes a declarative condition attached to a transition. A guard that currently lives as ad-hoc logic in `close.py` (checking child document states) becomes the same kind of object — just referencing different nodes.

---

## 5. What Gets Unified

### 5.1 Document Lifecycle

**Currently:** Procedural state checks in each command.

**Unified:**

```
Node: CR-045
Machine:
  DRAFT --[route_review]--> IN_REVIEW
    guards: [not_checked_out]
  IN_REVIEW --[auto]--> REVIEWED
    guards: [all_reviewers_responded(CR-045)]
  REVIEWED --[route_approval]--> IN_APPROVAL
    guards: [no_request_updates(CR-045)]
  IN_APPROVAL --[approve]--> PRE_APPROVED
  PRE_APPROVED --[release]--> IN_EXECUTION
  IN_EXECUTION --[route_review]--> POST_REVIEW
    guards: [all_eis_have_outcomes(CR-045)]        ← NEW enforcement
  ...
  POST_APPROVED --[close]--> CLOSED
    guards: [all_children_resolved(CR-045)]        ← currently ad-hoc
```

The `all_eis_have_outcomes` guard on the IN_EXECUTION → POST_REVIEW transition is the single most impactful addition. It is currently not enforced at all.

### 5.2 EI Execution

**Currently:** No enforcement. Freehand markdown table editing.

**Unified:**

```
Node: CR-045/EI-3
Machine:
  pending --[start]--> in_progress
    guards: [predecessor_complete(EI-2), parent_in_execution(CR-045)]
  in_progress --[complete]--> complete
    guards: [has_evidence, has_outcome]
```

EIs become first-class nodes in the graph with the same guard mechanism as everything else. Sequential dependencies, evidence requirements, gate checks — they all use the same pattern.

### 5.3 EI Classification

EIs are classified at authoring time. Classification determines mutability and positioning.

| Class | Source | Can remove? | Can reorder? | Examples |
|-------|--------|------------|-------------|----------|
| **Fixed** | SOP mandate, always present | No | No | Pre-execution baseline, post-execution baseline |
| **Conditional** | Classification flags from CR authoring | No (once included) | No | RS update, RTM update, template alignment |
| **User-defined** | Author's implementation plan | Yes (via VAR) | Within their slot | "Implement dropdown widget" |

### 5.4 EI Sequencing

The EI table has a fixed skeleton with slots for user-defined work:

```
[EI-1]   Pre-execution baseline           FIXED (always first)
[EI-2]   Test env setup, create branch    FIXED (code CRs)
[EI-3]   RS update                        CONDITIONAL (if adds_requirements)
  ┊
[EI-K]   ← user-defined work slots ←     USER-DEFINED (author fills these)
  ┊
[EI-N-3] Qualification (tests, CI)        FIXED (code CRs)
[EI-N-2] Integration verification         CONDITIONAL (if has_vr)
[EI-N-1] RTM update                       CONDITIONAL (if adds_requirements)
[EI-N]   Merge gate                       FIXED (code CRs)
[EI-N+1] Post-execution baseline          FIXED (always last)
```

User-defined EIs can be reordered within the user slot but cannot displace the fixed/conditional bookends. The skeleton is determined at authoring time by classification flags and is locked at approval.

### 5.5 EI Gating

Gates are checked by the CLI when you try to advance an EI:

| Gate | Condition | Enforced when |
|------|-----------|--------------|
| **Sequential** | Previous EI must be complete | Starting any EI |
| **Qualification** | All tests pass at a recorded commit | Starting merge gate EI |
| **SDLC** | RS and RTM both EFFECTIVE | Starting merge gate EI |
| **Evidence** | Required evidence fields populated | Completing an EI |
| **Post-review readiness** | All EIs have outcomes | `route --review` from IN_EXECUTION |

### 5.6 Review Assignments

**Currently:** Inbox files + procedural checks.

**Unified:**

```
Node: CR-045/review/tu_ui
Machine:
  assigned --[recommend]--> complete
  assigned --[request_updates]--> complete_with_updates
```

The document's IN_REVIEW → REVIEWED transition has a guard: `all(review.state == "complete" for review in node.reviews)`. The REVIEWED → IN_APPROVAL transition has a guard: `none(review.state == "complete_with_updates" for review in node.reviews)`.

Same framework, same guard mechanism.

### 5.7 Child Document Dependencies

**Currently:** Ad-hoc checks in close.py.

**Unified:**

```
Guard on CR-045 CLOSE transition:
  for each child in CR-045.children:
    if child.type == "VAR" and child.var_type == 1:
      require child.state == "CLOSED"
    if child.type == "VAR" and child.var_type == 2:
      require child.state in ["PRE_APPROVED", ...]
    if child.type == "VR":
      require child.state == "CLOSED"
```

Not a separate system. A guard on a transition, reading other nodes' states through the graph.

### 5.8 SDLC Prerequisites

**Currently:** Conceptual only. SOP guidance that agents are trusted to follow.

**Unified:**

```
Node: CR-045/sdlc_gate
Machine:
  unsatisfied --[verify]--> satisfied
    guards: [
      rs_effective(target_system),
      rtm_effective(target_system),
      tests_pass_at_commit(qualified_commit)
    ]

Guard on CR-045/EI-N (merge gate):
  require CR-045/sdlc_gate.state == "satisfied"
```

The SDLC gate becomes a node in the graph. The merge gate EI has a guard that references it. The "merge gate" concept in SOP-005 becomes an enforced prerequisite rather than agent guidance.

---

## 6. The Graph in Practice

A code-change CR with one VR child and SDLC dependencies produces:

```
CR-045 (document lifecycle)
├── CR-045/EI-1 (pending → in_progress → complete)
├── CR-045/EI-2 (pending → ... → complete)
│     prerequisite: EI-1 complete
├── CR-045/EI-3 (pending → ... → complete)
│     prerequisite: EI-2 complete
├── ...
├── CR-045/EI-N (merge gate)
│     prerequisite: EI-N-1 complete
│     guard: CR-045/sdlc_gate satisfied
├── CR-045/EI-N+1 (post-execution baseline)
│     prerequisite: EI-N complete
│
├── CR-045/sdlc_gate
│     guards: RS EFFECTIVE, RTM EFFECTIVE, CI green
│
├── CR-045/review/qa (assigned → complete)
├── CR-045/review/tu_ui (assigned → complete)
│     referenced by: CR-045 IN_REVIEW → REVIEWED guard
│
└── CR-045-VR-001 (document lifecycle, born IN_EXECUTION)
      ├── CR-045-VR-001/EI-1 ... EI-K
      referenced by: CR-045 CLOSE guard
```

Every entity is a node. Every dependency is a guard referencing another node's state. The CLI evaluates guards before allowing transitions. The graph is the single source of truth for "what can happen next."

---

## 7. Inspectable Blocking

One of the most powerful consequences: you can ask "what's blocking this?" and get a complete, machine-generated answer.

```
$ qms blocked CR-045

CR-045 is POST_APPROVED. To close:
  ✓ CR-045-VAR-001 is PRE_APPROVED (Type 2, sufficient)
  ✗ CR-045-VR-001 is IN_EXECUTION (must be CLOSED)
  ✗ CR-045/EI-7 has no outcome recorded
```

This is currently impossible. Today you have to manually check each dependency by running multiple status commands and cross-referencing mentally.

Similarly for EIs:

```
$ qms ei CR-045 --status

EI-1  Pre-execution baseline          ✓ complete    (commit abc123)
EI-2  Set up test env, branch cr-045  ✓ complete    (branch created)
EI-3  RS update                       ✓ complete    (RS v19.0 EFFECTIVE)
EI-4  Implement dropdown widget       ● in_progress
EI-5  Qualification                   ○ pending     (blocked by: EI-4)
EI-6  Integration verification (VR)   ○ pending     (blocked by: EI-5)
EI-7  RTM update                      ○ pending     (blocked by: EI-6)
EI-8  Merge gate                      ○ pending     (blocked by: EI-7, sdlc_gate)
EI-9  Post-execution baseline         ○ pending     (blocked by: EI-8)
```

---

## 8. CLI Interface

### EI Management

```bash
# View EI execution status
qms ei CR-045 --status

# Start an EI (checks prerequisites)
qms ei CR-045 --start EI-3

# Complete an EI with evidence
qms ei CR-045 --complete EI-3 --outcome pass --evidence "SDLC-QMS-RS v19.0 EFFECTIVE"

# Check if a gate is satisfied
qms ei CR-045 --gate merge

# Check what's blocking a document or EI
qms blocked CR-045
```

### Enhanced Existing Commands

```bash
# Route for post-review — blocked if any EI lacks an outcome
qms route CR-045 --review
# Error: Cannot route for post-review: EI-7 has no outcome recorded.

# Close — blocked if children not resolved
qms close CR-045
# Error: Cannot close: CR-045-VR-001 is IN_EXECUTION (must be CLOSED).
```

---

## 9. Relationship to the Interactive Engine Redesign

The interactive engine redesign (Session-2026-02-22-004) proposed two complementary systems:

1. **Authoring layer** — workflow specs (YAML/Python), classification-driven EI table variants, Jinja2 compilation
2. **Process layer** — SOP guidance surfaced at moment of relevance, stage gate enforcement

The unified state machine framework is the **execution-side counterpart** to the authoring layer. Together they form a complete system:

| Phase | System | What It Does |
|-------|--------|-------------|
| **Authoring** | Interactive engine | Classification flags → variant selection → fixed EI skeleton + user slots → compiled CR |
| **Execution** | Unified state machine | EI tracking → sequential gating → evidence validation → post-review readiness check |

The `.source.json` model extends naturally: just as VR prompts are tracked as response entries with cursor state, EI execution is tracked as EI entries with status, evidence, and outcomes. The same data model manages both.

### Authoring Produces the Graph

When the interactive engine compiles a CR, it also produces the graph definition: which EIs exist, which are fixed/conditional/user-defined, what their prerequisites are, and what gates apply. This graph definition is stored alongside the document metadata and drives the execution-phase enforcement.

For freehand CRs (non-interactive authoring), the graph is inferred from the document's EI table at release time. For interactive CRs, the graph is produced explicitly by the authoring engine.

---

## 10. Variant-Based Enforcement

Not every CR needs the same enforcement skeleton. Classification flags (from the interactive engine, or from document metadata for freehand CRs) determine the variant:

| Variant | Applicable To | Fixed EIs | Gates |
|---------|--------------|-----------|-------|
| **code-cr** | CRs modifying governed code | Pre/post baseline, test env, qualification, merge gate | SDLC gate, sequential |
| **document-cr** | CRs modifying only documents/SOPs | Pre/post baseline | Sequential |
| **investigation** | INVs | Pre/post baseline, CAPA implementation | CAPA CRs resolved |
| **test-protocol** | TPs | Pre/post baseline, test execution | Re-execution after ER |
| **vr** | VRs (born IN_EXECUTION) | Step sequence | Sequential, commit-on-evidence |
| **minimal** | Default / fallback | Pre/post baseline only | Sequential |

The variant determines how much enforcement applies. A document-only CR gets lightweight enforcement. A code CR gets the full skeleton. The agent never chooses the enforcement level — the classification flags determine it.

---

## 11. Declarative Lifecycle Definitions

If the state machine definitions are declarative (YAML or Python), they become inspectable, testable, and — importantly — versionable.

### Example: Document Lifecycle as YAML

```yaml
# lifecycles/executable.yaml
name: executable_document
version: 1

states:
  - DRAFT
  - IN_REVIEW
  - REVIEWED
  - IN_APPROVAL
  - PRE_APPROVED
  - IN_EXECUTION
  - POST_REVIEW
  - POST_REVIEWED
  - POST_APPROVAL
  - POST_APPROVED
  - CLOSED
  - RETIRED

transitions:
  - from: DRAFT
    to: IN_REVIEW
    trigger: route_review
    guards:
      - not_checked_out: "Document must be checked in"

  - from: IN_REVIEW
    to: REVIEWED
    trigger: auto
    guards:
      - all_reviewers_responded: "All assigned reviewers must respond"

  - from: REVIEWED
    to: IN_APPROVAL
    trigger: route_approval
    guards:
      - no_request_updates: "No reviewer has outstanding request-updates"

  - from: IN_EXECUTION
    to: POST_REVIEW
    trigger: route_review
    guards:
      - all_eis_have_outcomes: "Every EI must have a recorded outcome"
      - not_checked_out: "Document must be checked in"

  - from: POST_APPROVED
    to: CLOSED
    trigger: close
    guards:
      - all_children_resolved: "All child documents must be in required states"
```

### Example: Code CR EI Variant as YAML

```yaml
# variants/code-cr.yaml
name: code_cr
version: 1
applies_when:
  change_type: code

ei_skeleton:
  - id: pre_baseline
    class: fixed
    position: first
    description: "Pre-execution baseline: commit and push"
    sop_ref: "SOP-004 §5"
    evidence_type: commit_hash

  - id: test_env
    class: fixed
    position: early
    description: "Set up test environment, create execution branch"
    sop_ref: "SOP-005 §7.1"
    evidence_type: branch_name
    prerequisite: pre_baseline

  - id: rs_update
    class: conditional
    condition: adds_requirements
    position: early
    description: "Update RS to EFFECTIVE"
    evidence_type: document_version
    prerequisite: test_env

  - id: user_slot
    class: user_defined
    position: middle
    min: 1
    max: unbounded

  - id: qualification
    class: fixed
    position: late
    description: "Run full test suite, push, CI, record qualified commit"
    sop_ref: "SOP-005 §7.1.2"
    evidence_type: [commit_hash, test_count]
    prerequisite: user_slot_complete

  - id: integration_vr
    class: conditional
    condition: has_vr
    position: late
    description: "Integration verification"
    vr_required: true
    prerequisite: qualification

  - id: rtm_update
    class: conditional
    condition: adds_requirements
    position: late
    description: "Update RTM to EFFECTIVE"
    evidence_type: document_version
    prerequisite: integration_vr_or_qualification

  - id: merge_gate
    class: fixed
    position: late
    description: "Merge gate: PR, merge (--no-ff), submodule update"
    sop_ref: "SOP-005 §7.1.3"
    evidence_type: [pr_url, commit_hash]
    prerequisite: rtm_update_or_qualification
    gates:
      - sdlc_gate: "RS and RTM must both be EFFECTIVE"

  - id: post_baseline
    class: fixed
    position: last
    description: "Post-execution baseline: commit and push"
    sop_ref: "SOP-004 §5"
    evidence_type: commit_hash
    prerequisite: merge_gate
```

### Recursive Governance

The lifecycle definitions and EI variants are themselves artifacts that could be governed under the QMS. A change to a lifecycle — adding a new gate, modifying a guard — would be a CR that modifies a YAML definition. The QMS governs its own state machines using its own state machines.

---

## 12. What This Buys

| Benefit | How |
|---------|-----|
| **Consistent enforcement** | Every transition check is a guard evaluation. No more "this command checks X but that command forgets Y." |
| **Inspectable blocking** | `qms blocked CR-045` gives a complete, machine-generated answer. No manual cross-referencing. |
| **Declarative lifecycles** | Adding a new document type means defining a state machine and its guards, not writing procedural code across multiple CLI commands. |
| **EI enforcement** | EIs become nodes in the graph with the same guard mechanism as everything else. No separate EI system needed. |
| **Recursive governance** | State machine definitions are versionable, reviewable, and governed by the QMS. |
| **Testability** | Each guard is an independent function. Each transition is testable in isolation. The graph structure is inspectable. |
| **Variant-based flexibility** | Code CRs get full enforcement. Document CRs get lightweight enforcement. Classification flags determine the level, not agent choice. |

---

## 13. Risks and Mitigations

### Over-Abstraction

**Risk:** If the framework is too general, simple things become hard. Creating a one-off document-only CR shouldn't require understanding graph theory.

**Mitigation:** Variant-based defaults. When you create a code CR, the graph is instantiated from a variant template with all the right nodes and guards pre-wired. The author never sees the graph — they see prompts and EIs. The graph is the enforcement layer underneath, not the user interface on top.

### Migration Cost

**Risk:** 677 tests against the current procedural implementation. This is a rearchitecture of the CLI's core.

**Mitigation:** Build the framework alongside the current system, prove it on one document type (CRs with EI enforcement), then migrate other types. The guard definitions can be validated against the existing test suite. The existing tests become the acceptance criteria for the new framework.

### Flexibility vs. Rigidity

**Risk:** Over-constraining EIs risks making the system too rigid for novel CRs. Not every CR fits a predictable skeleton.

**Mitigation:** The `minimal` variant provides only pre/post baselines and sequential enforcement. User-defined EIs within the skeleton are fully flexible. The classification system determines enforcement level — novel or unusual CRs get lighter enforcement, not heavier.

### Complexity Budget

**Risk:** The unified framework is more complex to build than ad-hoc checks.

**Mitigation:** It is less complex to maintain and extend. Each new enforcement requirement today means modifying procedural code in multiple CLI commands and hoping nothing is missed. In the unified framework, it means adding a guard to a transition definition.

---

## 14. Implementation Considerations

### Build Order (if incremental)

1. **Guard framework** — the core `Node`, `Transition`, `Guard` abstractions
2. **Document lifecycle migration** — express existing document state machines declaratively; validate against existing tests
3. **EI node model** — EIs as first-class nodes with status tracking in `.meta/`
4. **EI variant system** — code-cr, document-cr, investigation, minimal variants
5. **EI gating enforcement** — sequential prerequisites, evidence validation
6. **Post-review readiness gate** — all-EIs-have-outcomes check on `route --review`
7. **SDLC gate node** — RS/RTM/CI prerequisite enforcement
8. **`qms blocked` command** — inspectable blocking across the graph
9. **`qms ei` command** — EI status, start, complete interface
10. **Interactive engine integration** — authoring produces graph definition; execution enforces it

### Data Model

EI state would be tracked in `.meta/` alongside existing document metadata:

```json
{
  "doc_id": "CR-045",
  "eis": {
    "EI-1": {
      "class": "fixed",
      "status": "complete",
      "description": "Pre-execution baseline",
      "outcome": "pass",
      "evidence": "commit abc123",
      "completed_by": "claude",
      "completed_at": "2026-02-23T10:00:00Z"
    },
    "EI-2": {
      "class": "fixed",
      "status": "in_progress",
      "description": "Set up test environment",
      "prerequisite": "EI-1"
    }
  },
  "variant": "code-cr",
  "sdlc_gate": {
    "status": "unsatisfied",
    "rs": null,
    "rtm": null,
    "qualified_commit": null
  }
}
```

### What Does NOT Get Unified

- **Audit trail** — remains append-only JSONL. The framework emits events; the audit trail records them.
- **Workspace/checkout** — remains a file-system operation. The framework guards the transition; the checkout mechanism is unchanged.
- **Inbox** — remains notification files. The framework triggers inbox creation on review assignment transitions.
- **Interactive engine prompts** — remain a separate cursor-based system within a single phase. The unified framework operates at the EI/document level, not the prompt level.

---

## 15. Key Design Insight

The prompt sequence (interactive engine) follows the **author's thinking** (what → why → how → verify → plan). The compiled document follows the **reader's structure** (Sections 1-12). The EI skeleton follows the **executor's workflow** (setup → implement → qualify → merge → close). The unified state machine follows the **system's invariants** (what must be true before this transition can fire).

These are four different orderings of the same information, each optimized for a different consumer. The three-artifact separation (workflow spec, rendering template, source data) from the interactive engine redesign, combined with the unified state machine framework, gives each consumer its own view while maintaining a single source of truth.

---

**END OF DOCUMENT**

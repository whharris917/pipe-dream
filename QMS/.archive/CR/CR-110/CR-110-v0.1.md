---
title: Workflow engine initial development — requirements and implementation
revision_summary: Initial draft
---

# CR-110: Workflow engine initial development — requirements and implementation

## 1. Purpose

Authorize initial development of the workflow engine within the `qms-workflow-engine` submodule, using a requirements-driven approach. This CR establishes the SDLC namespace, creates a draft Requirements Specification, and authorizes free-form development within explicit containment boundaries that protect the existing QMS and all other submodules.

---

## 2. Scope

### 2.1 Context

Independent improvement. The workflow engine design was finalized across Sessions 2026-03-03 through 2026-03-05 (bedrock primitives: Slot, Node, Edge). CR-109 established the `qms-workflow-engine` repository under formal change control. This CR authorizes building the engine.

- **Parent Document:** None

### 2.2 Changes Summary

Register the WFE SDLC namespace, create a draft RS (SDLC-WFE-RS), and implement the workflow engine to satisfy its requirements. Development is free-form within the `qms-workflow-engine` submodule — individual code changes do not require separate CRs.

### 2.3 Files Affected

- `QMS/SDLC-WFE/SDLC-WFE-RS-draft.md` - New draft Requirements Specification
- `QMS/.meta/sdlc_namespaces.json` - WFE namespace registration
- `qms-workflow-engine/` - All engine source code (via submodule)

---

## 3. Current State

The `qms-workflow-engine` submodule exists (CR-109) but contains only a README.md and .gitignore. No SDLC namespace exists for the workflow engine. No requirements have been formally captured. Design artifacts exist as session notes (bedrock primitives, agent interface research, forward plan).

---

## 4. Proposed State

The WFE SDLC namespace is registered. A draft RS (SDLC-WFE-RS) captures the engine's requirements and evolves as development progresses. The `qms-workflow-engine` submodule contains a working implementation that satisfies the requirements in the RS. The RS remains in DRAFT status — it is not routed for review or approval under this CR. No RTM exists.

---

## 5. Change Description

### 5.1 SDLC Namespace Registration

Register the `WFE` namespace via the CLI's `namespace add` command. This creates:
- `QMS/SDLC-WFE/` directory
- `WFE-RS` and `WFE-RTM` document types available in the CLI
- Namespace persisted to `QMS/.meta/sdlc_namespaces.json`

### 5.2 Requirements Specification (Draft)

Create SDLC-WFE-RS as a draft document. The RS will capture requirements for the workflow engine based on the design work from Sessions 2026-03-03 through 2026-03-05. Requirements will be added iteratively as development proceeds — the RS is a living design document during this CR, not a frozen specification.

The RS will **not** be routed for review or approval under this CR. It remains in DRAFT throughout. A future CR will mature the RS toward EFFECTIVE status when the engine is ready for qualification.

### 5.3 Implementation

Develop the workflow engine within the `qms-workflow-engine` submodule. Development is requirements-driven: requirements are captured in the RS, then implemented and tested in the engine. The implementation follows the bedrock primitives design (Slot, Node, Edge) with:

- DAG scheduler (node readiness, edge evaluation, fork/join, dead path elimination)
- Tool surface (construction and execution tool signatures)
- YAML workflow definitions
- Rendering layer (graph state to agent-readable view)

### 5.4 Containment Boundaries

This CR authorizes free-form development **within** these strict boundaries:

| Boundary | Constraint |
|----------|-----------|
| **Code changes** | Only within `qms-workflow-engine/` submodule |
| **QMS documents** | Only the draft SDLC-WFE-RS may be modified |
| **Existing submodules** | No changes to `qms-cli/`, `flow-state/`, `claude-qms/`, `Quality-Manual/` |
| **Existing QMS docs** | No changes to any SOP, template, or other controlled document |
| **Qualification** | Not attempted — no RTM created, RS stays DRAFT |
| **Submodule pointer** | `qms-workflow-engine` pointer in pipe-dream updated as development progresses |

Any work that would cross these boundaries requires a separate CR.

---

## 6. Justification

- **Requirements-driven development:** Capturing requirements before and during implementation produces better design than writing requirements retroactively. The RS becomes the authoritative specification even before it's formally approved.
- **Containment with freedom:** The explicit boundaries protect the existing QMS while allowing rapid iteration within the engine. No review overhead per code change — the CR authorizes the entire development effort.
- **Deferred qualification:** The engine is new and exploratory. Qualifying prematurely would lock down an immature design. By keeping the RS in DRAFT and deferring RTM creation, we preserve the freedom to refactor aggressively while still maintaining traceability through requirements.
- **Provenance continuity:** CR-109 established the repo. This CR authorizes what goes in it. The full chain of authorization is preserved.

---

## 7. Impact Assessment

### 7.1 Files Affected

| File | Change Type | Description |
|------|-------------|-------------|
| `QMS/.meta/sdlc_namespaces.json` | Create/Modify | Register WFE namespace |
| `QMS/SDLC-WFE/SDLC-WFE-RS-draft.md` | Create | Draft Requirements Specification |
| `qms-workflow-engine/**` | Create | All engine source code |

### 7.2 Documents Affected

| Document | Change Type | Description |
|----------|-------------|-------------|
| SDLC-WFE-RS | Create (DRAFT only) | Requirements Specification for workflow engine |

### 7.3 Other Impacts

None. The workflow engine is independent of all existing systems. No existing build processes, CI pipelines, or QMS operations are affected. The containment boundaries in Section 5.4 ensure isolation.

---

## 8. Testing Summary

<!--
NOTE: Do NOT delete this comment. It provides guidance during document authoring.

For code CRs, address both categories per SOP-002 Section 6.8:
1. Automated verification: unit tests, qualification tests, CI
2. Integration verification: what will be exercised through user-facing levers
   in a running system to demonstrate the change is effective

For document-only CRs, a description of procedural verification is sufficient.
Delete the subsections below and use a simple list.
-->

This CR is pre-qualification. The engine is not yet a qualified system — no CI pipeline, no merge gate, no RTM. Testing during this CR is developmental:

- Unit tests written alongside implementation within `qms-workflow-engine/`
- Tests run locally to validate requirements are met
- Test results are not formally recorded in an RTM (deferred to a future qualification CR)

Integration verification is not applicable — the engine has no integration points with existing systems during this CR.

---

## 9. Implementation Plan

1. Commit and push pre-execution baseline
2. Register the WFE SDLC namespace
3. Create SDLC-WFE-RS and populate with initial requirements
4. Implement the workflow engine in `qms-workflow-engine/`, driven by RS requirements
5. Update SDLC-WFE-RS as new requirements emerge during development
6. Update `qms-workflow-engine` submodule pointer in pipe-dream
7. Commit and push post-execution state

---

## 10. Execution

<!--
EXECUTION PHASE INSTRUCTIONS
============================
NOTE: Do NOT delete this comment block. It provides guidance for execution.

PRE-EXECUTION: After releasing for execution, the first execution item is to
commit and push the project repository (including all submodules) to capture
the pre-execution baseline (per SOP-004 Section 5). Record the commit hash
in EI-1's execution summary.

POST-EXECUTION: The final execution item is to commit and push the project
repository (including all submodules) to capture the post-execution state
(per SOP-004 Section 5). Record the commit hash in the final EI's execution
summary.

- Sections 1-9 are PRE-APPROVED content - do NOT modify during execution
- Only THIS TABLE and the comment sections below should be edited during execution phase

COLUMNS:
- EI: Execution item identifier
- Task Description: What to do (static, from Implementation Plan)
- VR: "Yes" if integration verification required (static, set during planning);
  replaced with VR ID during execution (editable). Blank if no VR needed.
  See SOP-004 Section 9C.
- Execution Summary: Narrative of what was done, evidence, observations (editable)
- Task Outcome: Pass or Fail (editable)
- Performed By - Date: Signature (editable)

TASK OUTCOME:
- Pass: Task completed as planned
- Fail: Task could not be completed as planned - attach VAR with explanation

VAR TYPES (see VAR-TEMPLATE):
- Type 1: Use when the failed task is critical to CR objectives
- Type 2: Use when impact is contained and CR can conceptually close

EXECUTION SUMMARY EXAMPLES:
- "Implemented per plan. Commit abc123."
- "Modified src/module.py:45-67. Unit tests passing."
- "Created SOP-007 (now EFFECTIVE)."
-->

| EI | Task Description | VR | Execution Summary | Task Outcome | Performed By - Date |
|----|------------------|----|-------------------|--------------|---------------------|
| EI-1 | Commit and push pre-execution baseline | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-2 | Register WFE SDLC namespace | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-3 | Create SDLC-WFE-RS and populate with initial requirements | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-4 | Implement workflow engine driven by RS requirements | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-5 | Update SDLC-WFE-RS with requirements discovered during development | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-6 | Update qms-workflow-engine submodule pointer in pipe-dream | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-7 | Commit and push post-execution state | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |

<!--
NOTE: Do NOT delete this comment. It provides guidance during document execution.

Add rows as needed. When adding rows, fill columns 3-5 during execution.
-->

---

### Execution Comments

| Comment | Performed By - Date |
|---------|---------------------|
| [COMMENT] | [PERFORMER] - [DATE] |

<!--
NOTE: Do NOT delete this comment. It provides guidance during document execution.

Record observations, decisions, or issues encountered during execution.
Add rows as needed.

This section is the appropriate place to attach VARs that do not apply
to any individual execution item, but apply to the CR as a whole.
-->

---

## 11. Execution Summary

<!--
NOTE: Do NOT delete this comment. It provides guidance during document execution.

Complete this section after all EIs are executed.
Summarize the overall outcome and any deviations from the plan.
-->

[EXECUTION_SUMMARY]

---

## 12. References

- **SOP-001:** Document Control
- **SOP-002:** Change Control
- **SOP-005:** Code Governance (Section 7.2 — Genesis Sandbox pattern)
- **SOP-006:** SDLC (Section 4 — namespace registration; Section 5 — RS creation)
- **CR-109:** Established qms-workflow-engine submodule
- **CR-108:** Workflow engine design work (prototyping, research)
- **Session-2026-03-05-001:** Bedrock primitives design, agent interface research, forward plan

---

**END OF DOCUMENT**

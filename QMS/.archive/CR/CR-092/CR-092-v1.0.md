---
title: 'INV-012 CAPA-1: Propagate CR-091 Interaction System to Production Submodule'
revision_summary: Initial draft
---

# CR-092: INV-012 CAPA-1: Propagate CR-091 Interaction System to Production Submodule

## 1. Purpose

Corrective action for INV-012 CAPA-1. Propagate the CR-091 interaction system code from the test environment to the production `qms-cli` submodule. This resolves the governance failure where CR-091 was closed with code existing only in `.test-env/qms-cli/`, not in the production submodule.

---

## 2. Scope

### 2.1 Context

INV-012 identified that CR-091's code (5 modules, ~4,500 lines implementing the interaction system engine) was never propagated to the production `qms-cli` submodule. The test environment `.test-env/qms-cli/` contains the merge commit `c83dda0` and qualified commit `7e708fc`, but these are unreachable from the production submodule's main branch.

- **Parent Document:** INV-012 (CAPA-1)

### 2.2 Changes Summary

Push the existing CR-091 commits from the test environment to the GitHub remote, update the production submodule to include them, and update the pipe-dream submodule pointer. No new code is written — this is purely a propagation fix.

### 2.3 Files Affected

- `qms-cli/` — Production submodule pointer updated to include CR-091 code
- No code files are created or modified; the code already exists in the test environment

---

## 3. Current State

The production `qms-cli` submodule points to commit `2c6b826` (CR-089 state). The `qms interact` command does not exist in the production CLI. The RTM v20.0 qualified commit `7e708fc` is unreachable from the production main branch.

---

## 4. Proposed State

The production `qms-cli` submodule points to commit `c83dda0` (the CR-091 merge commit). The `qms interact` command is available in the production CLI. The RTM v20.0 qualified commit `7e708fc` is reachable from the production main branch via `git log`.

---

## 5. Change Description

### 5.1 Propagation Strategy

The test environment's `main` branch is a direct descendant of the remote `main` at `2c6b826`, with four additional commits:

1. `c78198d` — Implement interaction system engine (CR-091 EI-3 through EI-8, EI-10)
2. `d820b05` — Add qms_interact MCP tool (CR-091 EI-9)
3. `7e708fc` — Add qualification tests for REQ-INT-001 through REQ-INT-022 (CR-091 EI-11)
4. `c83dda0` — Merge cr-091-interaction-system (no-ff merge commit)

Pushing the test environment's `main` to `origin/main` is a clean fast-forward that preserves all commit hashes. The production submodule then pulls to update.

### 5.2 Submodule Pointer Update

After the production submodule is updated, `pipe-dream` updates its submodule pointer from `2c6b826` to `c83dda0`.

### 5.3 RTM Verification

After propagation, verify that the qualified commit `7e708fc` is reachable from the production main branch, satisfying SOP-006 Section 7.2.

---

## 6. Justification

- CR-091's code is not available in production, blocking CR-091-ADD-001 and any use of `qms interact`
- The RTM qualified baseline references a commit unreachable from production, breaking the traceability chain required by SOP-006
- This is the minimum corrective action to restore governance integrity

---

## 7. Impact Assessment

### 7.1 Files Affected

| File | Change Type | Description |
|------|-------------|-------------|
| `qms-cli` (submodule pointer) | Modify | Updated from `2c6b826` to `c83dda0` |

### 7.2 Documents Affected

| Document | Change Type | Description |
|----------|-------------|-------------|
| INV-012 | Reference | CAPA-1 implementation evidence |

### 7.3 Other Impacts

Unblocks CR-091-ADD-001 (currently halted in IN_EXECUTION).

---

## 8. Testing Summary

### Automated Verification

No new tests. The existing 611 tests already pass at qualified commit `7e708fc` as verified during CR-091 execution.

### Integration Verification

- Verify `python qms-cli/qms.py --user claude interact --help` produces help output (command exists in production)
- Verify `git log --oneline qms-cli` shows commits through `c83dda0`
- Verify qualified commit `7e708fc` is reachable: `git -C qms-cli log --oneline | grep 7e708fc`

---

## 9. Implementation Plan

1. Pre-execution baseline commit
2. Push test environment main to origin (fast-forward)
3. Update production submodule (fetch + pull)
4. Update pipe-dream submodule pointer
5. Verify integration (command availability, commit reachability)
6. Post-execution commit

---

## 10. Execution

<!--
EXECUTION PHASE INSTRUCTIONS
============================
NOTE: Do NOT delete this comment block. It provides guidance for execution.

- Sections 1-9 are PRE-APPROVED content - do NOT modify during execution
- Only THIS TABLE and the comment sections below should be edited during execution phase
-->

| EI | Task Description | VR | Execution Summary | Task Outcome | Performed By - Date |
|----|------------------|----|-------------------|--------------|---------------------|
| EI-1 | Pre-execution baseline: commit and push project repository per SOP-004 Section 5 | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-2 | Push test-env qms-cli main to origin (fast-forward) | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-3 | Update production qms-cli submodule (fetch and fast-forward to c83dda0) | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-4 | Update pipe-dream submodule pointer and commit | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-5 | Verify integration: qms interact --help, commit reachability | Yes | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-6 | Post-execution commit per SOP-004 Section 5 | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |

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
- **SOP-005:** Code Governance (Section 7.1.3 — Merge Gate)
- **SOP-006:** SDLC Governance (Section 7.2 — Single Commit Requirement)
- **INV-012:** CR-091 Governance Failure Investigation (parent, CAPA-1)
- **CR-091:** Interaction System Engine (CLOSED — source of the code being propagated)

---

**END OF DOCUMENT**

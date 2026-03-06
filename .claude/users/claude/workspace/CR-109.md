---
title: Add qms-workflow-engine submodule under formal change control
revision_summary: Initial draft
---

# CR-109: Add qms-workflow-engine submodule under formal change control

## 1. Purpose

Establish the `qms-workflow-engine` repository as a controlled submodule within pipe-dream, bringing it under formal QMS change control from its inception. This enables full traceability for the workflow engine's development from commit zero, while ensuring it operates as a strictly parallel, independent tool that cannot interfere with the existing QMS.

---

## 2. Scope

### 2.1 Context

Independent improvement. The workflow engine has been designed across Sessions 2026-03-03 through 2026-03-05 (CR-108 EI-3 prototyping, bedrock primitives design, agent interface research). The design is now sufficiently mature to warrant a dedicated repository under formal change control.

- **Parent Document:** None

### 2.2 Changes Summary

Create a new GitHub repository (`qms-workflow-engine`) with minimal initial contents (README.md and .gitignore) and add it to pipe-dream as a git submodule.

### 2.3 Files Affected

- `.gitmodules` - Add qms-workflow-engine submodule entry
- `qms-workflow-engine/` - New submodule directory (README.md, .gitignore)

---

## 3. Current State

The pipe-dream repository contains two submodules: `flow-state` (application code) and `qms-cli` (QMS infrastructure). Workflow engine design work exists only as session artifacts (prototypes, research documents, forward plan) within `.claude/sessions/`. There is no dedicated repository for the workflow engine.

---

## 4. Proposed State

A third submodule, `qms-workflow-engine`, exists in the pipe-dream repository. It contains only a README.md and .gitignore. It is under formal QMS change control: any future modifications to the engine require a CR with appropriate review and approval. No SDLC documents (RS/RTM) exist yet — they will be created when the engine has code to qualify.

---

## 5. Change Description

### 5.1 Repository Creation

Create a new GitHub repository at `github.com/whharris917/qms-workflow-engine` with:

- **README.md** — Project description, purpose statement, and relationship to pipe-dream/QMS
- **.gitignore** — Python-appropriate gitignore (standard Python template)

No application code, no tests, no CI configuration. This is an intentionally minimal initial commit.

### 5.2 Submodule Integration

Add the repository as a git submodule of pipe-dream:

```bash
git submodule add https://github.com/whharris917/qms-workflow-engine.git qms-workflow-engine
```

This updates `.gitmodules` to include the new submodule entry alongside `flow-state` and `qms-cli`.

### 5.3 Independence Guarantee

The workflow engine is a parallel, independent tool. It:

- Has no runtime dependencies on the existing QMS CLI or document control system
- Cannot modify QMS-controlled documents or metadata
- Shares no code with `qms-cli` or `flow-state`
- Any future integration with the QMS would require its own CR with full impact assessment

---

## 6. Justification

- **Provenance from day one:** Every design decision, structural change, and prototype iteration will be tracked under formal change control from the very first commit. This is especially valuable for a system that may eventually enhance or replace current QMS governance tooling.
- **Recursive governance:** The QMS governs the development of the tool that will extend it — the recursive governance loop operating as designed.
- **Zero risk:** The engine is independent and parallel. It cannot interfere with the existing QMS because any interaction would require its own CR with impact assessment. The cost of formal control on an almost-empty repo is near zero.
- **Prevents technical debt:** Avoids the "we'll formalize later" trap where prototype code accumulates without traceability and requires retroactive justification.

---

## 7. Impact Assessment

### 7.1 Files Affected

| File | Change Type | Description |
|------|-------------|-------------|
| `.gitmodules` | Modify | Add qms-workflow-engine submodule entry |
| `qms-workflow-engine/README.md` | Create | Project description (via submodule) |
| `qms-workflow-engine/.gitignore` | Create | Python gitignore (via submodule) |

### 7.2 Documents Affected

| Document | Change Type | Description |
|----------|-------------|-------------|
| CLAUDE.md | Modify | Add qms-workflow-engine to project structure section |

### 7.3 Other Impacts

None. The new submodule is independent of all existing systems. No existing build processes, CI pipelines, or QMS operations are affected.

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

This is an infrastructure CR with no application code. Verification is procedural:

- Confirm the GitHub repository exists and is accessible
- Confirm `git submodule update --init` successfully clones the new submodule
- Confirm the submodule contains only README.md and .gitignore
- Confirm existing submodules (`flow-state`, `qms-cli`) are unaffected

---

## 9. Implementation Plan

1. Commit and push the pre-execution baseline (per SOP-004 Section 5)
2. Create the `qms-workflow-engine` GitHub repository with README.md and .gitignore
3. Add the repository as a submodule to pipe-dream
4. Update CLAUDE.md project structure to include the new submodule
5. Verify submodule integration (clone test)
6. Commit and push the post-execution state (per SOP-004 Section 5)

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
| EI-2 | Create qms-workflow-engine GitHub repository with README.md and .gitignore | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-3 | Add qms-workflow-engine as submodule to pipe-dream | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-4 | Update CLAUDE.md project structure section | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-5 | Verify submodule integration | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-6 | Commit and push post-execution state | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |

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
- **SOP-005:** Code Governance (Section 5 — repository structure; submodule pattern)
- **CR-030:** Established the submodule pattern for pipe-dream
- **CR-108:** Workflow engine design work (EI-3 prototyping, in progress)

---

**END OF DOCUMENT**

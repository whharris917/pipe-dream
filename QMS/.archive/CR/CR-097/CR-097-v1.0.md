---
title: VR Compilation Rendering Fixes
revision_summary: Initial draft
---

# CR-097: VR Compilation Rendering Fixes

## 1. Purpose

Fix three rendering defects in the VR compilation pipeline that reduce readability and consistency of compiled verification records, and improve auto-commit message quality during VR execution.

---

## 2. Scope

### 2.1 Context

Independent improvement identified during review of CR-096-VR-001 compiled output. The Verification Objective and Prerequisites sections render correctly (blockquoted response, attribution on next line), but step subsections have formatting problems.

- **Parent Document:** None

### 2.2 Changes Summary

Three defects addressed:
1. **D1 - Missing Labels:** Step subsections render four response-attribution pairs with no indication of what each represents. Add `**Instructions:**`, `**Expected:**`, `**Actual:**`, `**Outcome:**` labels.
2. **D2 - Instructions Not Blockquoted:** Step instructions use `**bold**` while all other VR responses use `>` blockquote. Switch to blockquote for consistency.
3. **D3 - Terse Auto-Commit Messages:** Engine-managed commits produce `[QMS] {doc_id} | {context} | {prompt_id}` with redundant loop context. Improve format to `[QMS] auto-commit | {doc_id} | {prompt_id} | Evidence capture during VR execution`.

### 2.3 Files Affected

- `qms-cli/interact_compiler.py` - Fix step subsection rendering (D1, D2)
- `qms-cli/commands/interact.py` - Fix commit message format (D3)
- `qms-cli/tests/test_interact_compiler.py` - Update compiler tests
- `qms-cli/tests/test_interact_integration.py` - Update integration tests

---

## 3. Current State

The `_expand_loops()` function in `interact_compiler.py` generates four response-attribution pairs per step with no labels. Step instructions are wrapped in `**bold**` markers while all other VR responses use `>` blockquote. Engine-managed commits produce `[QMS] {doc_id} | {context} | {prompt_id}` where the loop context is redundant with the prompt ID.

---

## 4. Proposed State

Each step subsection has labeled sections (`**Instructions:**`, `**Expected:**`, `**Actual:**`, `**Outcome:**`). Step instructions use `>` blockquote consistent with all other response rendering. Engine-managed commits produce descriptive messages: `[QMS] auto-commit | {doc_id} | {prompt_id} | Evidence capture during VR execution`.

---

## 5. Change Description

### 5.1 D1/D2: Step Subsection Rendering (`interact_compiler.py`)

In `_expand_loops()` (lines 432-441), replace the four rendering branches to add labels and use blockquote for instructions:

- `step_instructions`: Change from `**{value}**` to `**Instructions:**\n\n> {value}`
- `step_expected`: Add `**Expected:**` label before existing blockquote rendering
- `step_actual`: Add `**Actual:**` label before existing code fence rendering
- `step_outcome`: Add `**Outcome:**` label before existing blockquote rendering

### 5.2 D3: Auto-Commit Messages (`commands/interact.py`)

- Remove `context` parameter from `_do_engine_commit()` signature
- Change commit message format from `[QMS] {doc_id} | {context} | {prompt_id}` to `[QMS] auto-commit | {doc_id} | {prompt_id} | Evidence capture during VR execution`
- Remove context variable construction from the caller (lines 300-313)

---

## 6. Justification

- Compiled VR output lacks visual distinction between step subsection types, making review difficult
- Bold markers for instructions are inconsistent with blockquote rendering used everywhere else in the document
- Auto-commit messages provide insufficient context for git history review and contain redundant information
- These are rendering-only changes with no impact on source data or template structure

---

## 7. Impact Assessment

### 7.1 Files Affected

| File | Change Type | Description |
|------|-------------|-------------|
| `qms-cli/interact_compiler.py` | Modify | Add labels, blockquote instructions in `_expand_loops()` |
| `qms-cli/commands/interact.py` | Modify | Remove `context` param, improve commit message format |
| `qms-cli/tests/test_interact_compiler.py` | Modify | Update assertions for new rendering |
| `qms-cli/tests/test_interact_integration.py` | Modify | Update commit message format assertions |

### 7.2 Documents Affected

| Document | Change Type | Description |
|----------|-------------|-------------|
| SDLC-QMS-RS | Modify | No new requirements; existing REQ-INT-016/024/025 coverage |
| SDLC-QMS-RTM | Modify | Update verification evidence for affected requirements |

### 7.3 Other Impacts

- Existing VRs can be recompiled for improved output; source data is preserved
- No changes to source.json format, TEMPLATE-VR, or any other templates
- No SDLC requirement additions needed (changes refine existing behavior under REQ-INT-016, REQ-INT-024, REQ-INT-025)

### 7.4 Development Controls

This CR implements changes to qms-cli, a controlled submodule. Development follows established controls:

1. **Test environment isolation:** Development in `.test-env/qms-cli/` (gitignored)
2. **Branch isolation:** All development on branch `cr-097`
3. **Write protection:** `.claude/settings.local.json` blocks direct writes to `qms-cli/`
4. **Qualification required:** All new/modified requirements must have passing tests before merge
5. **CI verification:** Tests must pass on GitHub Actions for dev branch
6. **PR gate:** Changes merge to main only via PR after RS/RTM approval
7. **Submodule update:** Parent repo updates pointer only after PR merge

### 7.5 Qualified State Continuity

| Phase | main branch | RS/RTM Status | Qualified Release |
|-------|-------------|---------------|-------------------|
| Before CR | f0cd391 | EFFECTIVE v18.0 / v22.0 | qms-cli current |
| During execution | Unchanged | DRAFT (checked out) | qms-cli current (unchanged) |
| Post-approval | Merged from cr-097 | EFFECTIVE v18.1 / v22.1 | qms-cli updated |

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

### Automated Verification

- Update `test_loop_bold_not_broken` -> `test_loop_instructions_blockquoted`: verify instructions use blockquote, not bold
- Update `test_step_subsection_headings`: verify all four labels present
- Update `test_step_expected_blockquoted`: verify Expected label present
- Update `test_step_actual_code_fenced`: verify Actual label present
- Update `test_commit_message_format`: verify new commit message format
- Update `test_engine_commit_in_git_repo`: verify commit with new signature and message
- Run full qms-cli test suite to verify no regressions

### Integration Verification

- Compile an existing VR (e.g., CR-096-VR-001) using `qms interact --compile` and inspect step subsection rendering
- Verify labels appear, instructions are blockquoted, and formatting is consistent

---

## 9. Implementation Plan

### 9.1 Phase 1: Implementation and Testing

1. Clone/update qms-cli into `.test-env/qms-cli/` (gitignored working directory)
2. Create and checkout branch `cr-097`
3. Modify `interact_compiler.py`: update `_expand_loops()` rendering branches
4. Modify `commands/interact.py`: update `_do_engine_commit()` signature and message
5. Update test files with new assertions
6. Run test suite locally, verify all pass

### 9.2 Phase 2: Qualification

1. Push to `cr-097` branch
2. Verify GitHub Actions CI passes
3. Document qualified commit hash

### 9.3 Phase 3: Integration Verification

1. Compile an existing VR with the execution branch code
2. Inspect rendered output for correct labels, blockquote formatting
3. Document observations

### 9.4 Phase 4: RTM Update and Approval

1. Checkout SDLC-QMS-RTM
2. Update verification evidence for REQ-INT-016, REQ-INT-024, REQ-INT-025
3. Checkin, route for review and approval
4. Verify RTM reaches EFFECTIVE before proceeding

### 9.5 Phase 5: Merge and Submodule Update

**Prerequisite:** RTM must be EFFECTIVE before proceeding.

1. Create PR to merge `cr-097` to main
2. Merge PR using merge commit (--no-ff)
3. Verify qualified commit hash is reachable on main
4. Update submodule pointer in parent repo
5. Verify functionality in production context

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
| EI-1 | Pre-execution baseline commit | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-2 | Implement rendering fixes and test updates on branch cr-097 | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-3 | Run full test suite, push, verify CI | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-4 | Integration verification: compile VR and inspect output | Yes | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-5 | Update RTM, route for approval | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-6 | Merge PR, update submodule pointer | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-7 | Post-execution commit and push | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |

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
- **SOP-004:** Executable Document Control
- **CR-091:** Interaction System Engine (created the interact system)
- **CR-094:** Interactive Compilation Defects (previous compilation fixes)
- **CR-095:** Block rendering, auto-metadata, step subsection numbering

---

**END OF DOCUMENT**

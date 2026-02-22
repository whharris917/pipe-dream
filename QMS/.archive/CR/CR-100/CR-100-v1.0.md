---
title: 'INV-014 CAPA-003/004: Tighten SDLC Governance Controls'
revision_summary: Initial draft
---

# CR-100: INV-014 CAPA-003/004: Tighten SDLC Governance Controls

## 1. Purpose

This CR implements INV-014 CAPA-003 (preventive: tighten SOP-005 and SOP-002) and CAPA-004 (preventive: tighten TEMPLATE-CR) to close the procedural gaps that enabled CR-098's governance bypass. The changes make development location, PR merge requirement, file type scope, and seed workflow instructions explicit and unambiguous, and add PR verification to the QA post-review checklist.

---

## 2. Scope

### 2.1 Context

INV-014 investigated CR-098's direct commit to qms-cli main without using the SOP-005 Section 7.1 execution branch workflow. Root cause analysis identified vague language in SOP-005, TEMPLATE-CR, and SOP-002 that enabled the bypass. This CR addresses all procedural gaps.

- **Parent Document:** INV-014

### 2.2 Changes Summary

Tighten SOP-005, TEMPLATE-CR, and SOP-002 to eliminate vague language and add explicit mandates. Update the seed copy of TEMPLATE-CR to match, following the SOP-005 execution branch workflow for the seed change.

### 2.3 Files Affected

- `QMS/SOP/SOP-005.md` — Add development environment specification, PR mandate, file type scope, direct commit prohibition
- `QMS/TEMPLATE/TEMPLATE-CR.md` — Replace vague language with explicit locations and workflow references
- `QMS/SOP/SOP-002.md` — Add PR verification bullet to QA post-review checklist
- `qms-cli/seed/templates/TEMPLATE-CR.md` — Align seed copy with QMS changes (via execution branch workflow)

---

## 3. Current State

SOP-005 Section 7.1 says "Create execution branch from main" without specifying where development occurs, does not mandate PRs as the merge method, and scopes the "Used for" list to "code" without explicitly including templates, configuration, or documentation.

TEMPLATE-CR uses "or other gitignored location" (Section 7.4, line 205), "or other appropriate location" (Section 9.1, line 273), "commit in qms-cli submodule" (TEMPLATE CR PATTERNS, line 104), and has no enforcement language around PRs (Section 9.7, line 345).

SOP-002 Section 7.3 QA Post-Review Verification does not verify that code was integrated via PR merge.

---

## 4. Proposed State

SOP-005 specifies `.test-env/{system}/` (local) and `/projects/{system}/` (container) as the only permitted development locations, mandates GitHub PR as the exclusive merge method, prohibits direct commits to main, and explicitly covers all file types within governed systems.

TEMPLATE-CR specifies `.test-env/` and `/projects/` as the only permitted locations (no "or other" language), references SOP-005 Section 7.1 for seed workflow, and includes enforcement language requiring CI-passing PRs.

SOP-002 QA Post-Review Verification includes a bullet verifying code was integrated via GitHub PR merge.

---

## 5. Change Description

### 5.1 SOP-005 Changes (CAPA-003)

**Change A — New "Development Environment" paragraph before the Section 7.1.1 workflow box (after line 128):**

Add a subsection specifying that all development occurs in `.test-env/{system}/` (local) or `/projects/{system}/` (container). State that production submodule copies must never be edited directly. State that `.claude/settings.local.json` write protection and PreToolUse hooks enforce this constraint. State that this workflow applies to all modifications regardless of file type.

**Change B — Section 7.1.1 "Used for" list (line 165), add bullet:**

```
- Any modification to files within the governed codebase, including templates, configuration, and documentation
```

**Change C — Section 7.1.3 Merge Gate, new paragraph after line 184:**

Add "Merge method" paragraph mandating that code shall be merged to main exclusively via GitHub Pull Request. Prohibit direct commits to main, force-push, and local merge followed by push.

**Change D — Section 7.1.3 submodule paragraph (line 186), append:**

State that the submodule pointer update in the parent repository must occur only after the PR is merged and the merge commit is verified on main.

### 5.2 TEMPLATE-CR Changes (CAPA-004)

**Change A — Section 7.4, line 205:**

From: `Development in a non-QMS-controlled directory (e.g., .test-env/, /projects/ for containerized agents, or other gitignored location)`
To: `Development in .test-env/ (local) or /projects/ (containerized agents). No other locations are permitted.`

**Change B — Section 9.1, line 273:**

From: `Verify/create a non-QMS-controlled working directory (e.g., .test-env/, /projects/, or other appropriate location)`
To: `Verify/create the required development directory: .test-env/ (local) or /projects/ (containerized agents)`

**Change C — TEMPLATE CR PATTERNS, line 104:**

From: `Seed copy: commit in qms-cli submodule, update submodule pointer`
To: `Seed copy: follow the SOP-005 Section 7.1 execution branch workflow — develop in .test-env/, create execution branch, run CI, merge via PR, then update submodule pointer in parent repo`

**Change D — Section 9.7 Phase 7, step 3 (line 345):**

From: `Create PR to merge dev branch to main`
To: `Create PR to merge dev branch to main. The PR must pass all CI checks before merge. Direct commits to main are prohibited.`

### 5.3 SOP-002 Change (CAPA-003 extension)

**Change — Section 7.3 QA Post-Review Verification, add new bullet after line 228:**

```
- For code CRs: verify that code was integrated to the governed system's main branch via GitHub Pull Request merge — not via direct commit, local merge, or force-push
```

### 5.4 Seed TEMPLATE-CR (CAPA-004)

Apply identical Changes A-D as the QMS TEMPLATE-CR. This change follows the SOP-005 Section 7.1 execution branch workflow: develop in `.test-env/qms-cli/`, create branch, run CI, merge via PR, update submodule pointer. This validates the very controls being established.

---

## 6. Justification

- INV-014 identified these gaps as root causes of CR-098's governance bypass
- This is the second investigation into SDLC governance bypass for qms-cli (INV-012 was the first)
- Prior CAPAs were insufficient because they addressed specific failure modes rather than the systemic vagueness in the governing procedures
- Without these changes, the same class of deviation will recur

---

## 7. Impact Assessment

### 7.1 Files Affected

| File | Change Type | Description |
|------|-------------|-------------|
| `QMS/SOP/SOP-005.md` | Modify | Add dev environment, PR mandate, file scope, direct commit prohibition |
| `QMS/TEMPLATE/TEMPLATE-CR.md` | Modify | Replace vague language, add SOP-005 workflow reference for seed |
| `QMS/SOP/SOP-002.md` | Modify | Add PR verification to QA post-review checklist |
| `qms-cli/seed/templates/TEMPLATE-CR.md` | Modify | Align seed copy with QMS TEMPLATE-CR changes |

### 7.2 Documents Affected

| Document | Change Type | Description |
|----------|-------------|-------------|
| SOP-005 | Modify | v6.0 → v7.0 |
| TEMPLATE-CR | Modify | v9.0 → v10.0 |
| SOP-002 | Modify | v15.0 → v16.0 |

### 7.3 Other Impacts

None. These are procedural/template changes with no code behavior impact.

### 7.4 Development Controls

This CR implements changes to qms-cli, a controlled submodule. Development follows established controls:

1. **Test environment isolation:** Development in `.test-env/qms-cli/` (the only permitted local development location per SOP-005 Section 7.1)
2. **Branch isolation:** All development on branch `cr-100`
3. **Write protection:** PreToolUse hook blocks direct writes to `qms-cli/`
4. **Qualification required:** All existing tests must continue to pass
5. **CI verification:** Tests must pass on GitHub Actions for dev branch
6. **PR gate:** Changes merge to main only via PR
7. **Submodule update:** Parent repo updates pointer only after PR merge

### 7.5 Qualified State Continuity

| Phase | main branch | RS/RTM Status | Qualified Release |
|-------|-------------|---------------|-------------------|
| Before CR | Commit 5124b4a | EFFECTIVE (RS v18.0, RTM v23.0) | CLI-14.0 |
| During execution | Unchanged | Unchanged (no RS/RTM update needed) | CLI-14.0 (unchanged) |
| Post-approval | Merged from cr-100 | Unchanged | CLI-14.0 (unchanged) |

Note: No RS/RTM update is needed. Seed templates are content, not functional code with REQ-* requirements. Tests confirm no regressions but no new requirements are added.

---

## 8. Testing Summary

### Automated Verification

- Run full qms-cli test suite (673 tests) on execution branch to confirm no regressions from seed template changes
- CI must pass on GitHub Actions

### Integration Verification

- Verify seed TEMPLATE-CR matches QMS TEMPLATE-CR (diff shows only revision_summary difference)
- Verify SOP-005, TEMPLATE-CR, and SOP-002 are EFFECTIVE at correct versions
- Attempt Edit on `qms-cli/` file — should be blocked by PreToolUse hook

---

## 9. Implementation Plan

This is a hybrid CR. QMS documents are modified via checkout/checkin. The seed template change follows the SOP-005 execution branch workflow.

**Critical ordering:** SOP-005 must reach EFFECTIVE before seed work begins (EI-3 before EI-8), because the seed changes must follow the very rules being established.

### 9.1 Phase 1: QMS Document Changes

1. Checkout SOP-005, apply changes per Section 5.1, checkin
2. Route SOP-005 for review/approval → EFFECTIVE
3. Checkout TEMPLATE-CR, apply changes per Section 5.2, checkin
4. Route TEMPLATE-CR for review/approval → EFFECTIVE
5. Checkout SOP-002, apply change per Section 5.3, checkin
6. Route SOP-002 for review/approval → EFFECTIVE

### 9.2 Phase 2: Seed Template Change (Execution Branch Workflow)

1. Set up `.test-env/qms-cli/` — pull latest, create branch `cr-100`
2. Apply seed TEMPLATE-CR changes per Section 5.4 in `.test-env/qms-cli/`
3. Run test suite — all must pass
4. Push branch, verify CI passes
5. Create PR to merge `cr-100` to main
6. Merge PR (--no-ff)
7. Verify seed/QMS alignment via diff
8. Update submodule pointer in parent repo

### 9.3 Phase 3: Post-Execution Baseline

1. Commit and push parent repo to capture post-execution state

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
-->

| EI | Task Description | VR | Execution Summary | Task Outcome | Performed By - Date |
|----|------------------|----|-------------------|--------------|---------------------|
| EI-1 | Pre-execution baseline: commit and push | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-2 | Checkout SOP-005, apply changes (dev environment, PR mandate, file scope, direct commit prohibition), checkin | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-3 | Route SOP-005 for review/approval → EFFECTIVE | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-4 | Checkout TEMPLATE-CR, apply changes (4 locations: Sections 7.4, 9.1, 9.7, TEMPLATE CR PATTERNS), checkin | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-5 | Route TEMPLATE-CR for review/approval → EFFECTIVE | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-6 | Checkout SOP-002, add PR verification bullet to Section 7.3, checkin | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-7 | Route SOP-002 for review/approval → EFFECTIVE | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-8 | Set up .test-env/qms-cli/, pull latest, create branch cr-100 | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-9 | Apply seed TEMPLATE-CR changes in .test-env/qms-cli/ | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-10 | Run test suite, push branch, verify CI passes | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-11 | Create PR, merge (--no-ff) | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-12 | Verify seed/QMS TEMPLATE-CR alignment via diff | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-13 | Update submodule pointer in parent repo | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-14 | Post-execution baseline: commit and push | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |

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
- **SOP-002:** Change Control (Section 7.3 — target for CAPA-003)
- **SOP-005:** Code Governance (Section 7.1 — target for CAPA-003)
- **TEMPLATE-CR:** Change Record Template (Sections 7.4, 9.1, 9.7, TEMPLATE CR PATTERNS — target for CAPA-004)
- **INV-014:** CR-098 Direct Submodule Edit: SDLC Governance Bypass (parent investigation)

---

**END OF DOCUMENT**

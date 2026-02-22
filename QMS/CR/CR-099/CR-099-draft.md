---
title: 'CAPA-002/003: Dual-Template Architecture Procedural Controls'
revision_summary: Initial draft
---

# CR-099: CAPA-002/003: Dual-Template Architecture Procedural Controls

## 1. Purpose

This CR implements preventive actions INV-013-CAPA-002 and INV-013-CAPA-003 to establish procedural controls for the dual-template architecture. It adds awareness of the dual-template relationship to the TEMPLATE-CR usage guide and adds template alignment verification to the QA post-review checklist in SOP-002.

---

## 2. Scope

### 2.1 Context

Preventive actions from INV-013, which investigated systematic template drift between QMS-controlled templates and seed templates. CAPA-002 and CAPA-003 are bundled into this single CR because both address related procedural gaps in the same workflow.

- **Parent Document:** INV-013 (CAPA-002, CAPA-003)

### 2.2 Changes Summary

Two controlled document updates:
1. Add a "TEMPLATE CR PATTERNS" section to the TEMPLATE-CR usage guide warning about dual-template architecture
2. Add template alignment verification to SOP-002 Section 7.3 QA post-review checklist

### 2.3 Files Affected

- `QMS/TEMPLATE/TEMPLATE-CR.md` — Add TEMPLATE CR PATTERNS section to usage guide
- `QMS/SOP/SOP-002.md` — Add template alignment verification to Section 7.3

---

## 3. Current State

- TEMPLATE-CR's usage guide has a "CODE CR PATTERNS" section but no guidance for template-modifying CRs. Authors are unaware that template changes must be propagated to both QMS and seed locations.
- SOP-002 Section 7.3 QA post-review checklist verifies document status, VARs, VRs, code prerequisites, and submodule state — but does not verify template alignment when a CR modifies templates.

---

## 4. Proposed State

- TEMPLATE-CR's usage guide includes a "TEMPLATE CR PATTERNS" section that documents the dual-template architecture and requires an alignment verification EI for any CR that modifies templates.
- SOP-002 Section 7.3 QA post-review verification includes a bullet requiring template alignment verification for CRs that modify templates.

---

## 5. Change Description

### 5.1 TEMPLATE-CR Usage Guide Update (CAPA-002)

Add a new "TEMPLATE CR PATTERNS" section to the usage guide comment block, positioned after the existing "CODE CR PATTERNS" section. Content:

- Explain that templates exist in two locations: `QMS/TEMPLATE/` (active QMS instance) and `qms-cli/seed/templates/` (bootstrapping new instances)
- State that changes to either copy must be propagated to the other
- Require an alignment verification EI in the implementation plan for any CR that modifies templates
- Note that QMS template changes require checkout/checkin while seed template changes require qms-cli submodule commits

### 5.2 SOP-002 Section 7.3 Update (CAPA-003)

Add a new bullet to the "QA Post-Review Verification" checklist:

- For CRs that modify templates: both QMS-controlled copies (`QMS/TEMPLATE/`) and seed copies (`qms-cli/seed/templates/`) are aligned and reflect the changes authorized by the CR

---

## 6. Justification

- INV-013 root cause analysis identified absence of procedural guidance as the primary root cause of template drift
- Without these controls, future template-modifying CRs will continue to update only one copy, re-introducing the same systematic drift
- Adding both author-facing guidance (TEMPLATE-CR) and QA verification (SOP-002) creates defense in depth

---

## 7. Impact Assessment

### 7.1 Files Affected

| File | Change Type | Description |
|------|-------------|-------------|
| `QMS/TEMPLATE/TEMPLATE-CR.md` | Modify | Add TEMPLATE CR PATTERNS to usage guide |
| `QMS/SOP/SOP-002.md` | Modify | Add template alignment to Section 7.3 |

### 7.2 Documents Affected

| Document | Change Type | Description |
|----------|-------------|-------------|
| TEMPLATE-CR | Modify | Usage guide enhancement |
| SOP-002 | Modify | QA checklist enhancement |

### 7.3 Other Impacts

None. These are procedural controls that affect future CR workflows only.

---

## 8. Testing Summary

- Verify TEMPLATE-CR usage guide contains TEMPLATE CR PATTERNS section with dual-template guidance
- Verify SOP-002 Section 7.3 contains template alignment verification bullet
- Verify both documents reach EFFECTIVE status through their own review/approval workflows

---

## 9. Implementation Plan

### 9.1 Phase 1: Pre-Execution Baseline

Commit and push project repository to capture pre-execution state.

### 9.2 Phase 2: Update TEMPLATE-CR (CAPA-002)

1. Checkout TEMPLATE-CR via QMS CLI
2. Add TEMPLATE CR PATTERNS section to usage guide
3. Update revision_summary to reference CR-099
4. Checkin TEMPLATE-CR

### 9.3 Phase 3: Update SOP-002 (CAPA-003)

1. Checkout SOP-002 via QMS CLI
2. Add template alignment verification bullet to Section 7.3
3. Update revision_summary to reference CR-099
4. Checkin SOP-002

### 9.4 Phase 4: Post-Execution

Commit and push project repository to capture post-execution state.

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
| EI-1 | Pre-execution baseline: commit and push project state | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-2 | Update TEMPLATE-CR: add TEMPLATE CR PATTERNS section to usage guide | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-3 | Update SOP-002: add template alignment verification to Section 7.3 | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-4 | Post-execution: commit and push project state | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |

<!--
NOTE: Do NOT delete this comment. It provides guidance during document execution.

Add rows as needed. When adding rows, fill columns 3-5 during execution.
-->

---

### Execution Comments

| Comment | Performed By - Date |
|---------|---------------------|
| CAPA-002 and CAPA-003 bundled per INV-013 plan: both are controlled document updates addressing related procedural gaps. | claude - 2026-02-22 |

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
- **SOP-002:** Change Control (Section 7.3 — QA post-review requirements)
- **SOP-003:** Deviation Management
- **INV-013:** Seed-QMS Template Divergence (parent investigation, CAPA-002 and CAPA-003)

---

**END OF DOCUMENT**

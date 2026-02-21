---
title: 'INV-012 CAPA-2/3: SOP-005 Submodule Workflow and SOP-002 QA Checklist Update'
revision_summary: Initial draft
---

# CR-093: INV-012 CAPA-2/3: SOP-005 Submodule Workflow and SOP-002 QA Checklist Update

## 1. Purpose

Preventive actions for INV-012 CAPA-2 and CAPA-3. Update SOP-005 to include explicit submodule workflow steps in the execution branch model, and update SOP-002 to include submodule state verification in the QA post-review checklist. These changes close the procedural gaps that allowed CR-091's code to be closed without propagation to the production submodule.

---

## 2. Scope

### 2.1 Context

INV-012 identified two procedural root causes: (1) SOP-005 Section 7.1 does not address submodule pointer updates after merging code, and (2) SOP-002 Section 7.3 QA post-review checklist does not include submodule state verification. Both CAPAs are bundled into this CR because they address related gaps and affect the same workflow.

- **Parent Document:** INV-012 (CAPA-2 and CAPA-3)

### 2.2 Changes Summary

1. Add submodule workflow step to SOP-005 Section 7.1.1 (Workflow)
2. Add submodule pointer guidance to SOP-005 Section 7.1.3 (Merge Gate)
3. Add submodule state verification to SOP-002 Section 7.3 (QA Post-Review)

### 2.3 Files Affected

- `QMS/SOP/SOP-005.md` — Add submodule workflow steps
- `QMS/SOP/SOP-002.md` — Add submodule state verification to QA checklist

---

## 3. Current State

SOP-005 Section 7.1.1 workflow step 6 says "Merge to main (see 7.1.3)" without addressing submodule pointer updates. Section 7.1.3 covers merge prerequisites and merge type but not submodule propagation.

SOP-002 Section 7.3 QA Post-Review Verification checklist covers execution items, VARs, VRs, controlled documents, revision_summary, and RS/RTM status, but does not include verification that code is reachable from the production branch of submodule-based systems.

---

## 4. Proposed State

SOP-005 Section 7.1.1 includes a new step 7: "Update parent repository submodule pointer (for submodule-based systems)". Section 7.1.3 includes a new subsection addressing the submodule pointer update as part of the merge gate workflow.

SOP-002 Section 7.3 QA Post-Review Verification includes a new bullet: verification that for code CRs affecting submodule-based systems, the qualified commit is reachable from the production submodule's main branch.

---

## 5. Change Description

### 5.1 SOP-005 Changes

**Section 7.1.1 (Workflow):** Add step 7 to the numbered list and workflow diagram:

```
7. Update parent repo submodule pointer (for submodule-based systems)
```

**Section 7.1.3 (Merge Gate):** Add a paragraph after the existing fast-forward merge guidance addressing the submodule pointer update requirement for submodule-based systems.

### 5.2 SOP-002 Changes

**Section 7.3 (QA Post-Review Verification):** Add a new bullet to the verification checklist requiring verification that for code CRs affecting submodule-based systems, the qualified commit is reachable from the production submodule's main branch and the parent repository's submodule pointer has been updated.

---

## 6. Justification

- SOP-005's merge gate ends at merging to the submodule's main branch, creating a structural blind spot for the submodule pointer update
- SOP-002's QA checklist cannot catch what it doesn't cover; adding submodule verification provides a safety net
- Both gaps were identified as root causes in INV-012; these changes implement the preventive actions
- Without these changes, the same governance failure could recur on any future CR affecting submodule-based code

---

## 7. Impact Assessment

### 7.1 Files Affected

| File | Change Type | Description |
|------|-------------|-------------|
| `QMS/SOP/SOP-005.md` | Modify | Add submodule workflow step and merge gate guidance |
| `QMS/SOP/SOP-002.md` | Modify | Add submodule state verification to QA post-review checklist |

### 7.2 Documents Affected

| Document | Change Type | Description |
|----------|-------------|-------------|
| SOP-005 | Modify | Section 7.1.1 (step 7), Section 7.1.3 (submodule paragraph) |
| SOP-002 | Modify | Section 7.3 (new checklist bullet) |
| INV-012 | Reference | CAPA-2 and CAPA-3 implementation evidence |

### 7.3 Other Impacts

None. These are additive procedural changes that codify existing informal practice.

---

## 8. Testing Summary

Procedural verification. Review the updated SOP text for clarity, consistency with existing language, correct placement within document structure, and accuracy of the technical description.

---

## 9. Implementation Plan

1. Pre-execution baseline commit
2. Check out SOP-005, add submodule workflow content to Section 7.1.1 and 7.1.3
3. Check in SOP-005, route for review and approval
4. Check out SOP-002, add QA checklist bullet to Section 7.3
5. Check in SOP-002, route for review and approval
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
| EI-2 | Checkout SOP-005, add submodule workflow step to Section 7.1.1 and merge gate guidance to Section 7.1.3 | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-3 | Checkin SOP-005, route for review and approval to EFFECTIVE | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-4 | Checkout SOP-002, add submodule state verification to Section 7.3 QA post-review checklist | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-5 | Checkin SOP-002, route for review and approval to EFFECTIVE | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
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
- **SOP-002:** Change Control (Section 7.3 — target of CAPA-3 changes)
- **SOP-005:** Code Governance (Section 7.1 — target of CAPA-2 changes)
- **INV-012:** CR-091 Governance Failure Investigation (parent, CAPA-2 and CAPA-3)

---

**END OF DOCUMENT**

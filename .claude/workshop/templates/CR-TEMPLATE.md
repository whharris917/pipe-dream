---
title: 'Change Record Template'
revision_summary: 'Simplified frontmatter per SOP-001 three-tier architecture'
---

<!--
================================================================================
TEMPLATE DOCUMENT NOTICE
================================================================================
This template is a QMS-controlled document. The frontmatter contains only:
- title: Document title
- revision_summary: Description of changes in this revision

All other metadata (version, status, responsible_user, dates) is managed
automatically by the QMS CLI in sidecar files (.meta/) per SOP-001 Section 5.

When creating a CR from this template, copy from the EXAMPLE FRONTMATTER onward.
================================================================================
-->

---
title: '{{TITLE}}'
revision_summary: 'Initial draft'
---

<!--
================================================================================
TEMPLATE USAGE GUIDE
================================================================================

DOCUMENT TYPE:
CRs are EXECUTABLE documents that authorize implementation activities.

WORKFLOW:
  DRAFT → IN_PRE_REVIEW → PRE_REVIEWED → IN_PRE_APPROVAL → PRE_APPROVED
       → IN_EXECUTION → IN_POST_REVIEW → POST_REVIEWED → IN_POST_APPROVAL
       → POST_APPROVED → CLOSED

PLACEHOLDER TYPES:
1. {{DOUBLE_CURLY}} — Replace when DRAFTING (before routing for review)
2. [SQUARE_BRACKETS] — Replace during EXECUTION (after release)

After authoring:
- NO {{...}} placeholders should remain
- All [...] placeholders should remain until execution

Authors may define additional execution placeholders as needed. Use square
brackets for any field that must be filled during execution.

ID FORMAT:
  CR-NNN
  Example: CR-001, CR-015

LOCKED vs EDITABLE:
- Sections 1-5 are locked after pre-approval
- Section 6 (Execution) is editable during execution

Delete this comment block after reading.
================================================================================
-->

# CR-XXX: {{TITLE}}

## 1. Purpose

{{PURPOSE — What problem does this solve? What improvement does it introduce?}}

---

## 2. Scope

### 2.1 Context

{{CONTEXT — Reference parent investigation, CAPA, or driving document. If none, state the origin of this change (e.g., "Independent improvement identified during development" or "User-requested enhancement").}}

- **Parent Document:** {{PARENT_DOC_ID or "None"}}

### 2.2 Changes Summary

{{CHANGES_SUMMARY — Brief description of what will change}}

### 2.3 Files Affected

{{FILES_AFFECTED — List each file and describe changes}}

- `{{path/to/file1}}` — {{description of changes}}
- `{{path/to/file2}}` — {{description of changes}}

---

## 3. Rationale

{{RATIONALE — Explain WHY this change is needed:}}
- {{Current state and its problems}}
- {{Impact of not making this change}}
- {{How this solution addresses the root cause}}

---

## 4. Implementation Plan

{{IMPLEMENTATION — Describe HOW the change will be implemented}}

### 4.1 {{Component/Area 1}}

1. {{Step one}}
2. {{Step two}}
3. {{Step three}}

### 4.2 {{Component/Area 2}}

1. {{Step one}}
2. {{Step two}}

---

## 5. Testing Summary

{{TESTING — Describe how the implementation will be verified}}

- {{Test case 1}}
- {{Test case 2}}
- {{Test case 3}}

---

## 6. Execution

<!--
EXECUTION PHASE INSTRUCTIONS
============================
NOTE: Do NOT delete this comment block. It provides guidance for execution.

- Sections 1-5 are PRE-APPROVED content — do NOT modify during execution
- Only THIS TABLE and the comment sections below should be edited during execution phase

COLUMNS:
- EI: Execution item identifier
- Task Description: What to do (static, from Implementation Plan)
- Execution Summary: Narrative of what was done, evidence, observations (editable)
- Task Outcome: Pass or Fail (editable)
- Performed By — Date: Signature (editable)

TASK OUTCOME:
- Pass: Task completed as planned
- Fail: Task could not be completed as planned — attach VAR with explanation

VAR TYPES (see VAR-TEMPLATE):
- Type 1: Use when the failed task is critical to CR objectives
- Type 2: Use when impact is contained and CR can conceptually close

EXECUTION SUMMARY EXAMPLES:
- "Implemented per plan. Commit abc123."
- "Modified src/module.py:45-67. Unit tests passing."
- "Created SOP-007 (now EFFECTIVE)."
-->

| EI | Task Description | Execution Summary | Task Outcome | Performed By — Date |
|----|------------------|-------------------|--------------|---------------------|
| EI-1 | {{DESCRIPTION}} | [SUMMARY] | [Pass/Fail] | [PERFORMER] — [DATE] |
| EI-2 | {{DESCRIPTION}} | [SUMMARY] | [Pass/Fail] | [PERFORMER] — [DATE] |
| EI-3 | {{DESCRIPTION}} | [SUMMARY] | [Pass/Fail] | [PERFORMER] — [DATE] |

<!--
Add rows as needed. Each row:
- Columns 1-2: Design-time (author fills during drafting)
- Columns 3-5: Run-time (executor fills during execution)
-->

---

### Execution Comments

| Comment | Performed By — Date |
|---------|---------------------|
| [COMMENT] | [PERFORMER] — [DATE] |

<!--
Record observations, decisions, or issues encountered during execution.
Add rows as needed.

NOTE: This section is the appropriate place to attach VARs that do not apply
to any individual execution item, but apply to the CR as a whole.
-->

---

## 7. Execution Summary

<!--
Complete this section after all EIs are executed.
Summarize the overall outcome and any deviations from the plan.
-->

[EXECUTION_SUMMARY]

---

## 8. References

{{REFERENCES — List related documents. At minimum, reference governing SOPs.}}

- **SOP-001:** Document Control
- **SOP-002:** Change Control

---

**END OF DOCUMENT**

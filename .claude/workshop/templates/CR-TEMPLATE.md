---
doc_id: CR-TEMPLATE
title: 'Change Record Template'
version: '0.1'
status: DRAFT
revision_summary: 'Initial draft of CR template with execution-phase placeholders'
---

<!--
================================================================================
TEMPLATE DOCUMENT NOTICE
================================================================================
The frontmatter above is for QMS management of THIS TEMPLATE as a controlled
document. When this template is promoted to the QMS, it will be versioned and
governed like any other document.

The frontmatter below is the EXAMPLE frontmatter for Change Records created
from this template. Authors should copy from the example frontmatter onward.
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

This template uses TWO types of placeholders:

1. TEMPLATE PLACEHOLDERS: {{DOUBLE_CURLY_BRACES}}
   - Replace these when DRAFTING the CR (before routing for review)
   - Examples: {{TITLE}}, {{PURPOSE}}, {{FILE_PATH}}
   - After drafting, NO double-curly-brace placeholders should remain

2. EXECUTION PLACEHOLDERS: [SQUARE_BRACKETS]
   - These REMAIN in the document after drafting
   - Replace these during EXECUTION PHASE (after release)
   - Examples: [PENDING], [EXECUTION]
   - Only appear in Section 6 (Execution table)

   Authors may define additional execution placeholders as needed to structure
   their executable document. Use square brackets for any field that must be
   filled during execution. Examples:
   - [TEST_RESULT]
   - [REVIEWER_NOTES]
   - [MEASURED_VALUE]

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
- Only THIS TABLE should be edited during execution phase
- For each EI row, replace execution placeholders:
  - [PENDING]   → COMPLETE, PARTIAL, SKIPPED, or BLOCKED
  - [EXECUTION] → Actual evidence or follow-up notes

STATUS VALUES:
- [PENDING]  : Not yet started (initial state — do not remove until executing)
- COMPLETE   : Successfully implemented and verified
- PARTIAL    : Partially implemented (explain in Follow-up)
- SKIPPED    : Not implemented (justify in Follow-up)
- BLOCKED    : Cannot proceed (explain blocker in Follow-up)

EVIDENCE EXAMPLES:
- "Commit abc123"
- "src/module.py:45-67"
- "Unit tests passing"
- "Manual verification: [description]"

FOLLOW-UP EXAMPLES:
- "Created INV-XXX for discovered issue"
- "Deferred to CR-YYY"
- "" (blank if nothing to note)
-->

| EI | Description | Status | Evidence | Follow-up |
|----|-------------|--------|----------|-----------|
| EI-1 | {{Description from 4.1 step 1}} | [PENDING] | [EXECUTION] | [EXECUTION] |
| EI-2 | {{Description from 4.1 step 2}} | [PENDING] | [EXECUTION] | [EXECUTION] |
| EI-3 | {{Description from 4.1 step 3}} | [PENDING] | [EXECUTION] | [EXECUTION] |

---

## 7. Execution Summary

<!--
Complete this section after all EIs are executed.
Summarize the overall outcome and any deviations from the plan.
-->

[EXECUTION_SUMMARY]

---

## 8. Comments

<!--
Record observations, decisions, or issues encountered during execution.
Add rows as needed. Replace example row with actual comments.
-->

| Date | User | Comment |
|------|------|---------|
| [DATE] | [USER] | [COMMENT] |

---

## 9. References

{{REFERENCES — List related documents. At minimum, reference governing SOPs.}}

- **SOP-001:** Document Control
- **SOP-002:** Change Control

---

**END OF DOCUMENT**

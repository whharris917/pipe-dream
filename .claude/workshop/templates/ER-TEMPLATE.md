---
title: 'Exception Report Template'
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

When creating an ER from this template, copy from the EXAMPLE FRONTMATTER onward.
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

PLACEHOLDER TYPES:
1. {{DOUBLE_CURLY}} — Replace when AUTHORING the ER (design time)
2. [SQUARE_BRACKETS] — Replace when EXECUTING the ER (run time)

ER ID FORMAT:
  {TC_ID}-ER-NNN
  Example: TP-001-TC-001-ER-001

TEMPLATE NESTING:
- Re-test section follows TC-TEMPLATE structure
- ERs can nest: if re-testing fails, create child ER (e.g., TP-001-TC-001-ER-001-ER-001)

WORKFLOW SIGNATURES:
- Pre-approval and post-approval signatures are handled by QMS CLI
- Only execution-phase signatures appear in the document body

LOCKED vs EDITABLE:
- Sections 1-5 are locked after pre-approval
- Section 6 (Re-test) and Section 7 (Closure) are editable during execution

================================================================================
-->

# {{ER_ID}}: {{TITLE}}

## 1. Exception Identification

| Parent Test Case | Failed Step |
|------------------|-------------|
| {{TC_ID}} | {{STEP_ID}} |

---

## 2. Detailed Description

{{DETAILED_DESCRIPTION — What happened? What was expected vs. actual?}}

---

## 3. Root Cause

{{ROOT_CAUSE — Why did this happen?}}

---

## 4. Exception Type

{{EXCEPTION_TYPE}}

<!--
Select one:
- Test Script Error: Test itself was written or designed incorrectly
- Test Execution Error: Tester made a mistake by not following instructions as written
- System Error: The system under test behaved unexpectedly
- Documentation Error: Error in a document other than the test script itself
- Other: See Detailed Description
-->

---

## 5. Proposed Corrective Action

{{PROPOSED_CORRECTIVE_ACTION — What will be done to address the root cause before re-testing?}}

---

## 6. Re-test

<!--
================================================================================
RE-TEST INSTRUCTIONS
================================================================================
This section contains a full re-execution of the test case (not just the
failed step). The re-test may have different, more, or fewer steps than
the original if the test script itself required correction.

If the test script is modified, the test script author and all reviewers must
verify that the revised test script meets the intent of the original test
script, as expressed in the original test script's objectives. If the TC
objectives themselves are modified, this must be justified.

Follow TC-TEMPLATE structure for the re-test.
If the re-test fails, create a nested ER.
================================================================================
-->

### Re-test: {{TC_ID}}

#### Prerequisite Section

| Test Case ID | Objectives | Prerequisites | Performed By — Date |
|--------------|------------|---------------|---------------------|
| {{TC_ID}} | {{OBJECTIVES}} | {{PREREQUISITES}} | [PERFORMER] — [DATE] |

The signature above indicates that all listed test prerequisites have been satisfied and that the test script below is ready for execution.

---

#### Test Script

**Instructions:** Test execution must be performed in accordance with SOP-004 Document Execution. The individual test steps must be executed in the order shown. If a test step fails, execution of the test script must pause. The executor of the test will explain what occurred in the Actual Result field, mark the outcome of the step as "Fail", sign the step, and create a nested ER to document and remedy the testing failure.

**Acceptance Criteria:** A test case is accepted when either: (1) all test steps pass (Actual Results match Expected Results), or (2) a step failed, subsequent steps are marked N/A with nested ER reference, and the nested ER contains a successful full re-execution and is closed.

| Step | REQ ID | Instruction | Expected Result | Actual Result | Pass/Fail | Performed By — Date |
|------|--------|-------------|-----------------|---------------|-----------|---------------------|
| {{STEP_ID}}-001 | {{REQ_ID}} | {{INSTRUCTION}} | {{EXPECTED}} | [ACTUAL] | [Pass/Fail] | [PERFORMER] — [DATE] |
| {{STEP_ID}}-002 | {{REQ_ID}} | {{INSTRUCTION}} | {{EXPECTED}} | [ACTUAL] | [Pass/Fail] | [PERFORMER] — [DATE] |
| {{STEP_ID}}-003 | {{REQ_ID}} | {{INSTRUCTION}} | {{EXPECTED}} | [ACTUAL] | [Pass/Fail] | [PERFORMER] — [DATE] |

<!--
Add rows as needed. Each row:
- Columns 1-4: Design-time (author fills during drafting)
- Columns 5-7: Run-time (executor fills during execution)
-->

---

#### Test Execution Comments

| Comment | Performed By — Date |
|---------|---------------------|
| [COMMENT] | [PERFORMER] — [DATE] |

---

## 7. ER Closure

| Details of Resolution | Outcome | Performed By — Date |
|-----------------------|---------|---------------------|
| [RESOLUTION_DETAILS] | [OUTCOME] | [PERFORMER] — [DATE] |

---

## 8. References

- **SOP-004:** Document Execution
- **TC-TEMPLATE:** Test Case structure
- **{{TC_ID}}:** Parent test case
- {{ADDITIONAL_REFERENCES}}

---

**END OF EXCEPTION REPORT**

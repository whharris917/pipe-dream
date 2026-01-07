---
doc_id: TP-TEMPLATE
title: 'Test Protocol Template'
version: '0.1'
status: DRAFT
revision_summary: 'Initial draft of Test Protocol template'
---

<!--
================================================================================
TEMPLATE DOCUMENT NOTICE
================================================================================
The frontmatter above is for QMS management of THIS TEMPLATE as a controlled
document.

The frontmatter below is the EXAMPLE frontmatter for Test Protocols created
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

PLACEHOLDER TYPES:
1. {{DOUBLE_CURLY}} — Replace when AUTHORING the protocol (design time)
2. [SQUARE_BRACKETS] — Replace when EXECUTING the protocol (run time)

After authoring:
- NO {{...}} placeholders should remain
- All [...] placeholders should remain until execution

TEMPLATE NESTING:
- Test Cases follow TC-TEMPLATE structure
- Insert TC sections using the format shown in Section 3
- Do not duplicate TC-TEMPLATE content here—reference it

WORKFLOW SIGNATURES:
- Pre-approval and post-approval signatures are handled by QMS CLI
- Only execution-phase signatures appear in the document body
  (e.g., step Performed By, Reviewer Comments)

ID HIERARCHY:
- Protocol ID: TP-NNN
- Test Case ID: TP-NNN-TC-NNN (e.g., TP-001-TC-001)
- Step ID: TP-NNN-TC-NNN-NNN (e.g., TP-001-TC-001-001)
- ER ID: TP-NNN-TC-NNN-ER-NNN (e.g., TP-001-TC-001-ER-001)
- Nested ER: TP-NNN-TC-NNN-ER-NNN-ER-NNN

================================================================================
-->

# {{TP_ID}}: {{TITLE}}

## 1. Purpose

{{PURPOSE — What does this test protocol verify? What system/feature is under test?}}

---

## 2. Scope

| System | Version | Commit |
|--------|---------|--------|
| {{SYSTEM_NAME}} | {{SYSTEM_VERSION}} | {{COMMIT_HASH}} |

---

## 3. Test Cases

<!--
================================================================================
TEST CASE INSTRUCTIONS
================================================================================
Insert Test Cases below following TC-TEMPLATE structure:

  ### TC-NNN: {{TEST_CASE_TITLE}}

  #### Prerequisite Section
  (per TC-TEMPLATE)

  #### Test Script
  (per TC-TEMPLATE)

  #### Test Execution Comments
  (per TC-TEMPLATE)

Number TCs sequentially: TC-001, TC-002, etc.
Step IDs follow format: TC-NNN-001, TC-NNN-002, etc.

See TC-TEMPLATE for full structure and boilerplate content.
================================================================================
-->

### TC-001: {{TEST_CASE_TITLE}}

<!-- Insert TC-001 content per TC-TEMPLATE -->

---

### TC-002: {{TEST_CASE_TITLE}}

<!-- Insert TC-002 content per TC-TEMPLATE -->

---

## 4. Protocol Summary

### 4.1 Overall Result

[OVERALL_RESULT — Pass / Fail / Pass with Exceptions]

### 4.2 Execution Summary

[EXECUTION_SUMMARY — Overall narrative of test execution, significant observations, deviations from plan]

---

## 5. References

- **SOP-004:** Document Execution
- **SOP-006:** SDLC Governance
- **TC-TEMPLATE:** Test Case structure
- {{ADDITIONAL_REFERENCES}}

---

**END OF TEST PROTOCOL**

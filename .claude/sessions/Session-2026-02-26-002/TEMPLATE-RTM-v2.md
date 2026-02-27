---
title: 'Requirements Traceability Matrix Template'
revision_summary: 'Initial draft'
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

When creating an RTM from this template, copy from the EXAMPLE FRONTMATTER onward.
================================================================================
-->

---
title: '{%user:system_name%} Requirements Traceability Matrix'
revision_summary: 'Initial draft'
system_name: {{Human-readable system name (e.g., "QMS CLI")}}
rs_doc_id: {{RS document identifier (e.g., "SDLC-QMS-RS")}}
rs_version: {{RS version this RTM traces against (e.g., "22.0")}}
repository: {{GitHub repository (e.g., "whharris917/qms-cli")}}
branch: {{Qualification branch name}}
qualified_commit: {{CI-verified commit hash}}
ci_run: {{CI run identifier}}
---

<!--
================================================================================
TEMPLATE USAGE GUIDE
================================================================================

DOCUMENT TYPE:
RTMs are NON-EXECUTABLE documents that trace requirements to verification evidence.

WORKFLOW:
  DRAFT -> IN_REVIEW -> REVIEWED -> IN_APPROVAL -> EFFECTIVE

PLACEHOLDER TYPES:
1. {%user:...%} - Metadata-backed variables. Set via `qms set` at any time.
   Resolved from metadata.user_properties at render time.
2. {%sys:...%}  - System-computed variables. Resolved from metadata fields
   at render time. Authors cannot set these.
3. {{DOUBLE_CURLY}} - One-time authoring placeholders. Replace with prose
   when drafting. These are NOT variables — they are structural scaffolding
   that disappears after the author fills them in.

FRONTMATTER AND METADATA:
The YAML frontmatter declares this document's user-provided metadata fields.
Replacing a {{...}} placeholder in the frontmatter with a concrete value
auto-sets the corresponding user_properties field upon checkin. This is
equivalent to running `qms set DOC PROPERTY VALUE` for each field.

Any frontmatter fields left as {{...}} placeholders at checkin — and which
have not been manually set via `qms set` — will produce a validation error.
All user-provided metadata fields must have concrete values before checkin.

USER PROPERTIES (settable via `qms set DOC PROPERTY VALUE`):
  system_name         - Human-readable system name (e.g., "QMS CLI")
  rs_doc_id           - RS document identifier (e.g., "SDLC-QMS-RS")
  rs_version          - RS version this RTM traces against (e.g., "22.0")
  repository          - GitHub repository (e.g., "whharris917/qms-cli")
  branch              - Qualification branch name
  qualified_commit    - CI-verified commit hash
  ci_run              - CI run identifier

SYSTEM PROPERTIES (auto-resolved):
  sys:doc_id          - Document identifier (e.g., "SDLC-QMS-RTM")
  sys:version         - Current document version

Delete this comment block after reading.
================================================================================
-->

# {%sys:doc_id%}: {%user:system_name%} Requirements Traceability Matrix

## 1. Purpose

This document provides traceability between the requirements specified in {%user:rs_doc_id%} v{%user:rs_version%} and the qualification tests that verify them. Each requirement is mapped to specific test protocols and functions where verification occurs.

---

## 2. Scope

This RTM covers all requirements defined in {%user:rs_doc_id%} v{%user:rs_version%} across the following domains:

{{SCOPE_DOMAINS - List each requirement domain}}

---

## 3. Verification Approach

### 3.1 Test Architecture

{{TEST_ARCHITECTURE}}

### 3.2 Test Environment

{{TEST_ENVIRONMENT}}

### 3.3 Test Organization

{{TEST_ORGANIZATION - Table of test protocols}}

### 3.4 Traceability Convention

{{TRACEABILITY_CONVENTION}}

---

## 4. Summary Matrix

| REQ ID | Requirement | Code Reference | Status |
|--------|-------------|----------------|--------|
| {{REQ_ID}} | {{REQUIREMENT}} | {{CODE_REFERENCE}} | {{STATUS}} |

---

## 5. Traceability Details

{{TRACEABILITY_DETAILS - Per-requirement detailed traceability}}

---

## 6. Test Execution Summary

### 6.1 Qualified Baseline

| Attribute | Value |
|-----------|-------|
| Requirements Spec | {%user:rs_doc_id%} v{%user:rs_version%} |
| Repository | {%user:repository%} |
| Branch | {%user:branch%} |
| Commit | {%user:qualified_commit%} |
| CI Run | {%user:ci_run%} |

### 6.2 Test Protocol Results

{{TEST_PROTOCOL_RESULTS}}

### 6.3 Test Environment

- Tests executed via GitHub Actions CI on push to main branch
- All tests run in isolated temporary environments (no production QMS impact)
- CI provides independent, timestamped, immutable record of test results

---

## 7. References

- {%user:rs_doc_id%}: {%user:system_name%} Requirements Specification
- SOP-007: Software Development Lifecycle

---

**END OF DOCUMENT**

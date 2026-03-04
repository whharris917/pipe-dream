---
title: 'Requirements Traceability Matrix Template'
revision_summary: 'v3 — Aligned with CR-107 (Jinja2 unified lifecycle) and CR-106
  (system governance). Replaced {%user:...%}/{%sys:...%} with Jinja2 syntax. Replaced
  qms set with frontmatter editing. Added CR-106 qualification fields (qualified_version,
  traces_to_rs_version). Renamed rs_version to traces_to_rs_version for qualification
  gate alignment.'
---

<!--
================================================================================
TEMPLATE DOCUMENT NOTICE
================================================================================
This template is a QMS-controlled document managed under the unified document
lifecycle (CR-107). The first frontmatter block above is the template's own
metadata (title and revision_summary of the TEMPLATE document itself).

The second frontmatter block below is the SCHEMA DECLARATION for RTM documents
created from this template. Its keys define the user_properties schema that the
CLI stamps into every RTM's metadata sidecar. At every checkout, the CLI syncs
the document's schema against this template (living schema authority).

All other metadata (version, status, responsible_user, dates) is managed
automatically by the QMS CLI in sidecar files (.meta/) per SOP-001 Section 5.
================================================================================
-->

---
title: '{{ user.system_name }} Requirements Traceability Matrix'
revision_summary: '{{Describe changes in this revision}}'
system_name: '{{Human-readable system name (e.g., "QMS CLI")}}'
rs_doc_id: '{{RS document identifier (e.g., "SDLC-QMS-RS")}}'
traces_to_rs_version: '{{RS version this RTM traces against (e.g., "22.0")}}'
qualified_version: '{{System version being qualified (e.g., "19.0")}}'
repository: '{{GitHub repository (e.g., "whharris917/qms-cli")}}'
branch: '{{Qualification branch name}}'
qualified_commit: '{{CI-verified commit hash}}'
ci_run: '{{CI run identifier}}'
---

<!--
================================================================================
TEMPLATE USAGE GUIDE
================================================================================

DOCUMENT TYPE:
RTMs are NON-EXECUTABLE documents that trace requirements to verification
evidence. Under CR-106, the RTM is the qualification authority for its
registered system — the evidence chain flows through it.

WORKFLOW:
  DRAFT -> IN_REVIEW -> REVIEWED -> IN_APPROVAL -> EFFECTIVE

UNIFIED LIFECYCLE (CR-107):
This document uses the unified document lifecycle. The source file (in
QMS/.source/) is a Jinja2 template. The draft (in QMS/{TYPE}/) is always a
derived artifact rendered from source + .meta/ context. You edit the source;
the system renders the draft.

EXPRESSION TYPES:
1. {{ user.foo }}  - Jinja2 expressions resolved from user_properties in
   .meta/. Authors set these by editing frontmatter values in the source file.
   Checkin populates user_properties from frontmatter.
2. {{ sys.bar }}   - Jinja2 expressions resolved from system metadata in
   .meta/. Authors cannot set these — they are managed by the CLI.
3. {{SCAFFOLDING}} - One-time authoring placeholders. Replace with prose when
   drafting. These are NOT Jinja2 expressions — they are structural scaffolding
   that disappears after the author fills them in.

FRONTMATTER AND SCHEMA:
The YAML frontmatter in the source file declares this document's user property
values. All frontmatter keys are user properties — there is no distinction
between "author-maintained" and "system-managed" frontmatter in the source.
System properties (version, status, dates) are injected into the rendered draft
by the CLI; they never appear in the source.

To update a value: check out the document, edit the frontmatter field in your
workspace copy, check in. The CLI validates that all declared properties have
concrete values at checkin — {{...}} placeholders and null values are rejected.

There is no `qms set` command. Frontmatter editing is the sole input channel.

TEMPLATE AS LIVING SCHEMA AUTHORITY:
The frontmatter keys declared in this template define the user_properties
schema for ALL RTM documents. At every checkout, the CLI syncs the document's
schema against the current template:
  - New template fields: appear in the document with null values (checkin
    blocked until the author provides concrete values)
  - Removed template fields: archived with provenance (value, timestamp,
    template version) — never silently discarded

USER PROPERTIES (set via source frontmatter editing):
  system_name           - Human-readable system name (e.g., "QMS CLI")
  rs_doc_id             - RS document identifier (e.g., "SDLC-QMS-RS")
  traces_to_rs_version  - RS version this RTM traces against (e.g., "22.0")
                          Used by the qualification gate (CR-106) to verify
                          the RTM traces to the current EFFECTIVE RS
  qualified_version     - System version being qualified (e.g., "19.0")
                          Used by the qualification gate (CR-106) to set
                          the system record's qualified_version at approval
  repository            - GitHub repository (e.g., "whharris917/qms-cli")
  branch                - Qualification branch name
  qualified_commit      - CI-verified commit hash; the exact commit at which
                          CI verification was performed. Used by the
                          qualification gate (CR-106) to verify CI status
                          and match the PR HEAD at system checkin
  ci_run                - CI run identifier

SYSTEM PROPERTIES (auto-resolved from .meta/):
  sys.doc_id            - Document identifier (e.g., "SDLC-QMS-RTM")
  sys.version           - Current document version

QUALIFICATION LIFECYCLE (CR-106):
When this RTM reaches EFFECTIVE, the CLI updates the registered system
record from user_properties:
  - qualified_version and qualified_commit are always propagated
  - If the system is NOT checked out (migration/baseline): current_release
    and release_commit are also set, completing qualification in one step
  - If the system IS checked out (active development): current_release
    stays at the old value until system checkin

Delete this comment block after reading.
================================================================================
-->

# {{ sys.doc_id }}: {{ user.system_name }} Requirements Traceability Matrix

## 1. Purpose

This document provides traceability between the requirements specified in {{ user.rs_doc_id }} v{{ user.traces_to_rs_version }} and the qualification tests that verify them. Each requirement is mapped to specific test protocols and functions where verification occurs.

---

## 2. Scope

This RTM covers all requirements defined in {{ user.rs_doc_id }} v{{ user.traces_to_rs_version }} across the following domains:

{{SCOPE_DOMAINS - List each requirement domain with count}}

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
| Requirements Spec | {{ user.rs_doc_id }} v{{ user.traces_to_rs_version }} |
| Qualified Version | {{ user.qualified_version }} |
| Repository | {{ user.repository }} |
| Branch | {{ user.branch }} |
| Commit | {{ user.qualified_commit }} |
| CI Run | {{ user.ci_run }} |

### 6.2 Test Protocol Results

{{TEST_PROTOCOL_RESULTS - Tables of per-protocol test counts}}

### 6.3 Test Environment

- Tests executed via GitHub Actions CI on push to execution branch
- All tests run in isolated temporary environments (no production QMS impact)
- CI provides independent, timestamped, immutable record of test results

---

## 7. References

- {{ user.rs_doc_id }}: {{ user.system_name }} Requirements Specification
- SOP-006: Software Development Lifecycle

---

**END OF DOCUMENT**

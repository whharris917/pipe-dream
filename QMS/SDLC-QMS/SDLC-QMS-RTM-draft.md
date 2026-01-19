---
title: QMS CLI Requirements Traceability Matrix
revision_summary: Updated with qualification results - commit 9fd2d72, 54/54 tests
  passing
---

# SDLC-QMS-RTM: QMS CLI Requirements Traceability Matrix

## 1. Purpose

This document provides traceability between the requirements specified in SDLC-QMS-RS and the qualification tests that verify them. Each requirement is mapped to specific test protocols, functions, and line numbers where verification occurs.

---

## 2. Scope

This RTM covers all 56 requirements defined in SDLC-QMS-RS v1.0 across the following domains:

- REQ-SEC (Security): 6 requirements
- REQ-DOC (Document Management): 12 requirements
- REQ-WF (Workflow): 13 requirements
- REQ-META (Metadata): 4 requirements
- REQ-AUDIT (Audit Trail): 4 requirements
- REQ-TASK (Task/Inbox): 4 requirements
- REQ-CFG (Configuration): 7 requirements
- REQ-QRY (Query Operations): 6 requirements

---

## 3. Verification Approach

### 3.1 Test Architecture

Verification uses behavioral tests that exercise the CLI as end users would. Tests execute actual CLI commands and verify observable outcomes (files created, status changes, command output).

### 3.2 Test Environment

All tests run in isolated temporary environments created by pytest fixtures. No test modifies the production QMS. See `qms-cli/tests/conftest.py` for fixture implementation.

### 3.3 Test Organization

Tests are organized by workflow scenario rather than individual requirement. Each test protocol verifies multiple related requirements:

| Test Protocol | File | Description |
|---------------|------|-------------|
| SOP Lifecycle | `qualification/test_sop_lifecycle.py` | Non-executable document workflow |
| CR Lifecycle | `qualification/test_cr_lifecycle.py` | Executable document workflow |
| Security | `qualification/test_security.py` | Access control and authorization |
| Document Types | `qualification/test_document_types.py` | Creation, child documents, templates |
| Queries | `qualification/test_queries.py` | Read, status, history, inbox, workspace |

### 3.4 Traceability Convention

Test code includes inline markers `[REQ-XXX]` to identify where each requirement is verified. This RTM references those markers with file and line numbers.

---

## 4. Summary Matrix

| REQ ID | Requirement | Code Reference |
|--------|-------------|----------------|
| REQ-SEC-001 | User Group Classification | test_security::test_user_group_classification::44-67 |
| REQ-SEC-002 | Group-Based Action Authorization | test_security::test_unauthorized_create::73-85<br>test_security::test_unauthorized_assign::87-105<br>test_security::test_fix_authorization::107-134 |
| REQ-SEC-003 | Owner-Only Restrictions | test_security::test_owner_only_checkin::140-161<br>test_security::test_owner_only_route::163-180 |
| REQ-SEC-004 | Assignment-Based Review Access | test_security::test_unassigned_cannot_review::186-209<br>test_security::test_unassigned_cannot_approve::211-234 |
| REQ-SEC-005 | Rejection Access | test_security::test_rejection_access::240-265 |
| REQ-SEC-006 | Unknown User Rejection | test_security::test_unknown_user_rejection::271-288 |
| REQ-DOC-001 | Supported Document Types | test_document_types::test_create_sop::44-60<br>test_document_types::test_create_cr::62-80<br>test_document_types::test_create_inv::82-100 |
| REQ-DOC-002 | Child Document Relationships | test_document_types::test_create_tp_under_cr::106-129<br>test_document_types::test_create_var_under_cr::131-155<br>test_document_types::test_create_var_under_inv::157-176 |
| REQ-DOC-003 | QMS Folder Structure | test_sop_lifecycle::test_sop_full_lifecycle::105-110,239-243 |
| REQ-DOC-004 | Sequential ID Generation | test_document_types::test_sequential_id_generation::182-209 |
| REQ-DOC-005 | Child Document ID Generation | test_document_types::test_create_var_under_cr::131-155<br>test_document_types::test_child_id_generation::215-242 |
| REQ-DOC-006 | Version Format | test_sop_lifecycle::test_sop_full_lifecycle::110-115,233-236 |
| REQ-DOC-007 | Checkout Behavior | test_sop_lifecycle::test_sop_full_lifecycle::157-167 |
| REQ-DOC-008 | Checkin Updates QMS | test_sop_lifecycle::test_sop_full_lifecycle::145-156,171-180 |
| REQ-DOC-009 | Checkin Reverts Reviewed Status | test_sop_lifecycle::test_checkin_reverts_reviewed::271-295 |
| REQ-DOC-010 | Cancel Restrictions | test_document_types::test_cancel_v0_document::248-268<br>test_document_types::test_cancel_blocked_for_v1::270-294 |
| REQ-DOC-011 | Template Name-Based ID | test_document_types::test_template_name_based_id::300-324 |
| REQ-DOC-012 | SDLC Document Types | test_document_types::test_sdlc_document_types::330-357 |
| REQ-WF-001 | Status Transition Validation | test_sop_lifecycle::test_invalid_transition::252-269 |
| REQ-WF-002 | Non-Executable Document Lifecycle | test_sop_lifecycle::test_sop_full_lifecycle::95-250 |
| REQ-WF-003 | Executable Document Lifecycle | test_cr_lifecycle::test_cr_full_lifecycle::62-190 |
| REQ-WF-004 | Review Completion Gate | test_sop_lifecycle::test_multi_reviewer_gate::295-326 |
| REQ-WF-005 | Approval Gate | test_sop_lifecycle::test_approval_gate_blocking::328-350 |
| REQ-WF-006 | Approval Version Bump | test_sop_lifecycle::test_sop_full_lifecycle::226-246 |
| REQ-WF-007 | Rejection Handling | test_sop_lifecycle::test_rejection::352-377<br>test_cr_lifecycle::test_pre_approval_rejection::406-436<br>test_cr_lifecycle::test_post_approval_rejection::438-470 |
| REQ-WF-008 | Release Transition | test_cr_lifecycle::test_cr_full_lifecycle::119-142<br>test_cr_lifecycle::test_owner_only_release::325-360 |
| REQ-WF-009 | Revert Transition | test_cr_lifecycle::test_revert::194-238 |
| REQ-WF-010 | Close Transition | test_cr_lifecycle::test_cr_full_lifecycle::172-190<br>test_cr_lifecycle::test_owner_only_close::362-404 |
| REQ-WF-011 | Terminal State Enforcement | test_cr_lifecycle::test_terminal_state::241-278 |
| REQ-WF-012 | Retirement Routing | test_sop_lifecycle::test_retirement::379-428<br>test_sop_lifecycle::test_retirement_rejected_for_v0::430-448 |
| REQ-WF-013 | Retirement Transition | test_sop_lifecycle::test_retirement::409-428 |
| REQ-META-001 | Three-Tier Separation | test_sop_lifecycle::test_sop_full_lifecycle::115-143 |
| REQ-META-002 | CLI-Exclusive Metadata Management | test_sop_lifecycle::test_sop_full_lifecycle::115-128 |
| REQ-META-003 | Required Metadata Fields | test_sop_lifecycle::test_sop_full_lifecycle::115-143<br>test_cr_lifecycle::test_cr_full_lifecycle::68-85 |
| REQ-META-004 | Execution Phase Tracking | test_cr_lifecycle::test_cr_full_lifecycle::77-85,126-129<br>test_cr_lifecycle::test_execution_phase_preserved::282-322 |
| REQ-AUDIT-001 | Append-Only Logging | test_sop_lifecycle::test_sop_full_lifecycle::167-171 |
| REQ-AUDIT-002 | Required Event Types | test_sop_lifecycle::test_sop_full_lifecycle::128-143,246-250<br>test_cr_lifecycle::test_cr_full_lifecycle::129-142,179-190<br>test_queries::test_history_shows_all_event_types::219-245 |
| REQ-AUDIT-003 | Event Attribution | test_sop_lifecycle::test_sop_full_lifecycle::128-143 |
| REQ-AUDIT-004 | Comment Preservation | test_sop_lifecycle::test_sop_full_lifecycle::197-212 |
| REQ-TASK-001 | Task Generation on Routing | test_sop_lifecycle::test_sop_full_lifecycle::187-191 |
| REQ-TASK-002 | Task Content Requirements | test_sop_lifecycle::test_sop_full_lifecycle::191-196 |
| REQ-TASK-003 | QA Auto-Assignment | test_sop_lifecycle::test_sop_full_lifecycle::187-191 |
| REQ-TASK-004 | Task Removal on Completion | test_sop_lifecycle::test_sop_full_lifecycle::216-218 |
| REQ-CFG-001 | Project Root Discovery | conftest::temp_project::15-90 |
| REQ-CFG-002 | QMS Root Path | test_sop_lifecycle::test_sop_full_lifecycle::105-110 |
| REQ-CFG-003 | Users Directory Path | test_sop_lifecycle::test_sop_full_lifecycle::157-167,187-191 |
| REQ-CFG-004 | Agents Directory Path | conftest::temp_project::75-90 |
| REQ-CFG-005 | User Registry | test_security::test_unknown_user_rejection::271-288 |
| REQ-CFG-006 | Document Type Registry | test_document_types::test_create_sop::44-60<br>test_document_types::test_create_cr::62-80<br>test_document_types::test_create_inv::82-100 |
| REQ-CFG-007 | Agent Definition Loading | conftest::temp_project::75-90 |
| REQ-QRY-001 | Document Reading | test_queries::test_read_draft::44-58<br>test_queries::test_read_effective::60-81<br>test_queries::test_read_archived_version::83-105<br>test_queries::test_read_draft_flag::107-139 |
| REQ-QRY-002 | Document Status Query | test_queries::test_status_query::142-164<br>test_queries::test_status_shows_checked_out::166-189 |
| REQ-QRY-003 | Audit History Query | test_queries::test_history_query::191-217<br>test_queries::test_history_shows_all_event_types::219-245 |
| REQ-QRY-004 | Review Comments Query | test_queries::test_comments_query::248-266<br>test_queries::test_comments_includes_rejection::268-291 |
| REQ-QRY-005 | Inbox Query | test_queries::test_inbox_query::294-312<br>test_queries::test_inbox_multiple_tasks::314-335<br>test_queries::test_inbox_empty_when_no_tasks::337-352 |
| REQ-QRY-006 | Workspace Query | test_queries::test_workspace_query::355-369<br>test_queries::test_workspace_multiple_documents::371-390<br>test_queries::test_workspace_empty_after_checkin::392-410 |

---

## 5. Traceability Details

### 5.1 Security (REQ-SEC)

#### REQ-SEC-001: User Group Classification

**Requirement:** The CLI shall classify all users into exactly one of three groups: Initiators, QA, or Reviewers.

| Test File | Test Function | Lines |
|-----------|---------------|-------|
| test_security.py | test_user_group_classification | 44-67 |

---

#### REQ-SEC-002: Group-Based Action Authorization

**Requirement:** The CLI shall authorize actions based on user group membership: create, checkout, checkin, route, release, revert, close (Initiators); assign (QA); fix (QA, lead).

| Test File | Test Function | Lines |
|-----------|---------------|-------|
| test_security.py | test_unauthorized_create | 73-85 |
| test_security.py | test_unauthorized_assign | 87-105 |
| test_security.py | test_fix_authorization | 107-134 |

---

#### REQ-SEC-003: Owner-Only Restrictions

**Requirement:** The CLI shall restrict checkin, route, release, revert, and close actions to the document's responsible_user (owner).

| Test File | Test Function | Lines |
|-----------|---------------|-------|
| test_security.py | test_owner_only_checkin | 140-161 |
| test_security.py | test_owner_only_route | 163-180 |

---

#### REQ-SEC-004: Assignment-Based Review Access

**Requirement:** The CLI shall permit review and approve actions only for users listed in the document's pending_assignees.

| Test File | Test Function | Lines |
|-----------|---------------|-------|
| test_security.py | test_unassigned_cannot_review | 186-209 |
| test_security.py | test_unassigned_cannot_approve | 211-234 |

---

#### REQ-SEC-005: Rejection Access

**Requirement:** The CLI shall permit reject actions using the same authorization rules as approve (pending_assignees).

| Test File | Test Function | Lines |
|-----------|---------------|-------|
| test_security.py | test_rejection_access | 240-265 |

---

#### REQ-SEC-006: Unknown User Rejection

**Requirement:** The CLI shall reject any command invoked with a user identifier not present in the user registry, returning an error without modifying any state.

| Test File | Test Function | Lines |
|-----------|---------------|-------|
| test_security.py | test_unknown_user_rejection | 271-288 |

### 5.2 Document Management (REQ-DOC)

#### REQ-DOC-001: Supported Document Types

**Requirement:** The CLI shall support creation and management of the following document types: SOP, CR, INV, TP, ER, VAR, RS, RTM, and TEMPLATE.

| Test File | Test Function | Lines |
|-----------|---------------|-------|
| test_document_types.py | test_create_sop | 44-60 |
| test_document_types.py | test_create_cr | 62-80 |
| test_document_types.py | test_create_inv | 82-100 |

---

#### REQ-DOC-002: Child Document Relationships

**Requirement:** The CLI shall enforce parent-child relationships: TP is a child of CR; ER is a child of TP; VAR is a child of CR or INV. Child documents shall be stored within their parent's folder.

| Test File | Test Function | Lines |
|-----------|---------------|-------|
| test_document_types.py | test_create_tp_under_cr | 106-129 |
| test_document_types.py | test_create_var_under_cr | 131-155 |
| test_document_types.py | test_create_var_under_inv | 157-176 |

---

#### REQ-DOC-003: QMS Folder Structure

**Requirement:** The CLI shall maintain the following folder structure: QMS/ for controlled documents organized by type; QMS/.meta/ for workflow state sidecar files; QMS/.audit/ for audit trail logs; QMS/.archive/ for superseded versions; and per-user workspace and inbox directories.

| Test File | Test Function | Lines |
|-----------|---------------|-------|
| test_sop_lifecycle.py | test_sop_full_lifecycle | 105-110, 239-243 |

---

#### REQ-DOC-004: Sequential ID Generation

**Requirement:** The CLI shall generate document IDs sequentially within each document type (e.g., CR-001, CR-002, SOP-001, SOP-002). The next available number shall be determined by scanning existing documents.

| Test File | Test Function | Lines |
|-----------|---------------|-------|
| test_document_types.py | test_sequential_id_generation | 182-209 |

---

#### REQ-DOC-005: Child Document ID Generation

**Requirement:** For child document types, the CLI shall generate IDs in the format `{PARENT}-{TYPE}-NNN` where NNN is sequential within that parent (e.g., CR-005-VAR-001, CR-005-VAR-002).

| Test File | Test Function | Lines |
|-----------|---------------|-------|
| test_document_types.py | test_create_var_under_cr | 131-155 |
| test_document_types.py | test_child_id_generation | 215-242 |

---

#### REQ-DOC-006: Version Format

**Requirement:** The CLI shall enforce version numbers in the format `N.X` where N = approval number (major version) and X = revision number within approval cycle (minor version). Initial documents shall start at version 0.1.

| Test File | Test Function | Lines |
|-----------|---------------|-------|
| test_sop_lifecycle.py | test_sop_full_lifecycle | 110-115, 233-236 |

---

#### REQ-DOC-007: Checkout Behavior

**Requirement:** The CLI shall permit checkout of any document not currently checked out by another user. On checkout, the CLI shall: (1) copy the document to the user's workspace, (2) set the user as responsible_user, (3) mark the document as checked_out, and (4) if the document is EFFECTIVE, create a new draft version at N.1.

| Test File | Test Function | Lines |
|-----------|---------------|-------|
| test_sop_lifecycle.py | test_sop_full_lifecycle | 157-167 |

---

#### REQ-DOC-008: Checkin Updates QMS

**Requirement:** When a user checks in a document, the CLI shall: (1) copy the document from workspace to QMS working directory, (2) archive any previous draft version, and (3) maintain the user as responsible_user.

| Test File | Test Function | Lines |
|-----------|---------------|-------|
| test_sop_lifecycle.py | test_sop_full_lifecycle | 145-156, 171-180 |

---

#### REQ-DOC-009: Checkin Reverts Reviewed Status

**Requirement:** When a document in REVIEWED, PRE_REVIEWED, or POST_REVIEWED status is checked in, the CLI shall revert the status to DRAFT (for non-executable) or the appropriate pre-review state (for executable) to require a new review cycle.

| Test File | Test Function | Lines |
|-----------|---------------|-------|
| test_sop_lifecycle.py | test_checkin_reverts_reviewed | 271-295 |

---

#### REQ-DOC-010: Cancel Restrictions

**Requirement:** The CLI shall only permit cancellation of documents with version < 1.0 (never approved). Cancellation shall permanently delete the document file, metadata, and audit trail.

| Test File | Test Function | Lines |
|-----------|---------------|-------|
| test_document_types.py | test_cancel_v0_document | 248-268 |
| test_document_types.py | test_cancel_blocked_for_v1 | 270-294 |

---

#### REQ-DOC-011: Template Name-Based ID

**Requirement:** Template documents shall use name-based identifiers in the format `TEMPLATE-{NAME}` rather than sequential numbering. The name shall be specified at creation time.

| Test File | Test Function | Lines |
|-----------|---------------|-------|
| test_document_types.py | test_template_name_based_id | 300-324 |

---

#### REQ-DOC-012: SDLC Document Types

**Requirement:** The CLI shall support RS and RTM documents for configured SDLC namespaces. Each namespace requires explicit configuration in DOCUMENT_TYPES specifying the document ID prefix (e.g., SDLC-FLOW-RS, SDLC-QMS-RTM) and storage path. Documents shall be stored in `QMS/SDLC-{NAMESPACE}/`.

| Test File | Test Function | Lines |
|-----------|---------------|-------|
| test_document_types.py | test_sdlc_document_types | 330-357 |

### 5.3 Workflow State Machine (REQ-WF)

#### REQ-WF-001: Status Transition Validation

**Requirement:** The CLI shall reject any status transition not defined in the workflow state machine. Invalid transitions shall produce an error without modifying document state.

| Test File | Test Function | Lines |
|-----------|---------------|-------|
| test_sop_lifecycle.py | test_invalid_transition | 252-269 |

---

#### REQ-WF-002: Non-Executable Document Lifecycle

**Requirement:** Non-executable documents shall follow this status progression: DRAFT → IN_REVIEW → REVIEWED → IN_APPROVAL → APPROVED → EFFECTIVE. SUPERSEDED and RETIRED are terminal states.

| Test File | Test Function | Lines |
|-----------|---------------|-------|
| test_sop_lifecycle.py | test_sop_full_lifecycle | 95-250 |

---

#### REQ-WF-003: Executable Document Lifecycle

**Requirement:** Executable documents (CR, INV, TP, ER, VAR) shall follow this status progression: DRAFT → IN_PRE_REVIEW → PRE_REVIEWED → IN_PRE_APPROVAL → PRE_APPROVED → IN_EXECUTION → IN_POST_REVIEW → POST_REVIEWED → IN_POST_APPROVAL → POST_APPROVED → CLOSED. RETIRED is a terminal state.

| Test File | Test Function | Lines |
|-----------|---------------|-------|
| test_cr_lifecycle.py | test_cr_full_lifecycle | 62-190 |

---

#### REQ-WF-004: Review Completion Gate

**Requirement:** The CLI shall automatically transition a document from IN_REVIEW to REVIEWED (or equivalent pre/post states) only when all users in pending_assignees have submitted reviews.

| Test File | Test Function | Lines |
|-----------|---------------|-------|
| test_sop_lifecycle.py | test_multi_reviewer_gate | 295-326 |

---

#### REQ-WF-005: Approval Gate

**Requirement:** The CLI shall block routing for approval if any reviewer submitted a review with `request-updates` outcome. All reviews must have `recommend` outcome before approval routing is permitted.

| Test File | Test Function | Lines |
|-----------|---------------|-------|
| test_sop_lifecycle.py | test_approval_gate_blocking | 328-350 |

---

#### REQ-WF-006: Approval Version Bump

**Requirement:** Upon successful approval (all approvers complete), the CLI shall: (1) increment the major version (N.X → N+1.0), (2) archive the previous version, (3) transition to EFFECTIVE (non-executable) or PRE_APPROVED/POST_APPROVED (executable), and (4) clear the responsible_user.

| Test File | Test Function | Lines |
|-----------|---------------|-------|
| test_sop_lifecycle.py | test_sop_full_lifecycle | 226-246 |

---

#### REQ-WF-007: Rejection Handling

**Requirement:** When any approver rejects a document, the CLI shall transition the document back to the most recent REVIEWED state (REVIEWED, PRE_REVIEWED, or POST_REVIEWED) without incrementing the version.

| Test File | Test Function | Lines |
|-----------|---------------|-------|
| test_sop_lifecycle.py | test_rejection | 352-377 |
| test_cr_lifecycle.py | test_pre_approval_rejection | 406-436 |
| test_cr_lifecycle.py | test_post_approval_rejection | 438-470 |

---

#### REQ-WF-008: Release Transition

**Requirement:** The CLI shall transition executable documents from PRE_APPROVED to IN_EXECUTION upon release command. Only the document owner may release.

| Test File | Test Function | Lines |
|-----------|---------------|-------|
| test_cr_lifecycle.py | test_cr_full_lifecycle | 119-142 |
| test_cr_lifecycle.py | test_owner_only_release | 325-360 |

---

#### REQ-WF-009: Revert Transition

**Requirement:** The CLI shall transition executable documents from POST_REVIEWED to IN_EXECUTION upon revert command, requiring a reason. Only the document owner may revert.

| Test File | Test Function | Lines |
|-----------|---------------|-------|
| test_cr_lifecycle.py | test_revert | 194-238 |

---

#### REQ-WF-010: Close Transition

**Requirement:** The CLI shall transition executable documents from POST_APPROVED to CLOSED upon close command. Only the document owner may close.

| Test File | Test Function | Lines |
|-----------|---------------|-------|
| test_cr_lifecycle.py | test_cr_full_lifecycle | 172-190 |
| test_cr_lifecycle.py | test_owner_only_close | 362-404 |

---

#### REQ-WF-011: Terminal State Enforcement

**Requirement:** The CLI shall reject all transitions from terminal states (SUPERSEDED, CLOSED, RETIRED).

| Test File | Test Function | Lines |
|-----------|---------------|-------|
| test_cr_lifecycle.py | test_terminal_state | 241-278 |

---

#### REQ-WF-012: Retirement Routing

**Requirement:** The CLI shall support routing for retirement approval, which signals that approval leads to RETIRED status rather than EFFECTIVE or PRE_APPROVED. Retirement routing shall only be permitted for documents with version >= 1.0 (once-effective).

| Test File | Test Function | Lines |
|-----------|---------------|-------|
| test_sop_lifecycle.py | test_retirement | 379-428 |
| test_sop_lifecycle.py | test_retirement_rejected_for_v0 | 430-448 |

---

#### REQ-WF-013: Retirement Transition

**Requirement:** Upon approval of a retirement-routed document, the CLI shall: (1) archive the document to `.archive/`, (2) remove the working copy from the QMS directory, (3) transition status to RETIRED, and (4) log a RETIRE event to the audit trail.

| Test File | Test Function | Lines |
|-----------|---------------|-------|
| test_sop_lifecycle.py | test_retirement | 409-428 |

### 5.4 Metadata Architecture (REQ-META)

#### REQ-META-001: Three-Tier Separation

**Requirement:** The CLI shall maintain strict separation between: Tier 1 (Frontmatter) for author-maintained fields only (title, revision_summary); Tier 2 (.meta/) for CLI-managed workflow state; and Tier 3 (.audit/) for immutable event history.

| Test File | Test Function | Lines |
|-----------|---------------|-------|
| test_sop_lifecycle.py | test_sop_full_lifecycle | 115-143 |

---

#### REQ-META-002: CLI-Exclusive Metadata Management

**Requirement:** The CLI shall be the sole mechanism for modifying .meta/ sidecar files. Workflow state (version, status, responsible_user, pending_assignees) shall never be stored in document frontmatter.

| Test File | Test Function | Lines |
|-----------|---------------|-------|
| test_sop_lifecycle.py | test_sop_full_lifecycle | 115-128 |

---

#### REQ-META-003: Required Metadata Fields

**Requirement:** Each document's .meta/ file shall contain at minimum: doc_id, doc_type, version, status, executable (boolean), responsible_user (or null), checked_out (boolean), and pending_assignees (array).

| Test File | Test Function | Lines |
|-----------|---------------|-------|
| test_sop_lifecycle.py | test_sop_full_lifecycle | 115-143 |
| test_cr_lifecycle.py | test_cr_full_lifecycle | 68-85 |

---

#### REQ-META-004: Execution Phase Tracking

**Requirement:** For executable documents, the CLI shall track the execution phase (pre_release or post_release) in metadata to correctly infer pre vs. post workflow stages.

| Test File | Test Function | Lines |
|-----------|---------------|-------|
| test_cr_lifecycle.py | test_cr_full_lifecycle | 77-85, 126-129 |
| test_cr_lifecycle.py | test_execution_phase_preserved | 282-322 |

---

### 5.5 Audit Trail (REQ-AUDIT)

#### REQ-AUDIT-001: Append-Only Logging

**Requirement:** The CLI shall never modify or delete existing audit trail entries. All audit operations shall append new entries to the .audit/ JSONL files.

| Test File | Test Function | Lines |
|-----------|---------------|-------|
| test_sop_lifecycle.py | test_sop_full_lifecycle | 167-171 |

---

#### REQ-AUDIT-002: Required Event Types

**Requirement:** The CLI shall log the following events to the audit trail: CREATE, CHECKOUT, CHECKIN, ROUTE_REVIEW, ROUTE_APPROVAL, REVIEW, APPROVE, REJECT, EFFECTIVE, RELEASE, REVERT, CLOSE, RETIRE, STATUS_CHANGE.

| Test File | Test Function | Lines |
|-----------|---------------|-------|
| test_sop_lifecycle.py | test_sop_full_lifecycle | 128-143, 246-250 |
| test_cr_lifecycle.py | test_cr_full_lifecycle | 129-142, 179-190 |
| test_queries.py | test_history_shows_all_event_types | 219-245 |

---

#### REQ-AUDIT-003: Event Attribution

**Requirement:** Each audit event shall include: timestamp (ISO 8601 format), event type, user who performed the action, and document version at time of event.

| Test File | Test Function | Lines |
|-----------|---------------|-------|
| test_sop_lifecycle.py | test_sop_full_lifecycle | 128-143 |

---

#### REQ-AUDIT-004: Comment Preservation

**Requirement:** Review comments and rejection rationale shall be stored only in the audit trail, not in document content or metadata.

| Test File | Test Function | Lines |
|-----------|---------------|-------|
| test_sop_lifecycle.py | test_sop_full_lifecycle | 197-212 |

---

### 5.6 Task & Inbox Management (REQ-TASK)

#### REQ-TASK-001: Task Generation on Routing

**Requirement:** When a document is routed for review or approval, the CLI shall create task files in each assigned user's inbox directory.

| Test File | Test Function | Lines |
|-----------|---------------|-------|
| test_sop_lifecycle.py | test_sop_full_lifecycle | 187-191 |

---

#### REQ-TASK-002: Task Content Requirements

**Requirement:** Generated task files shall include: task_id (unique identifier), task_type (REVIEW or APPROVAL), workflow_type, doc_id, version, assigned_by, and assigned_date.

| Test File | Test Function | Lines |
|-----------|---------------|-------|
| test_sop_lifecycle.py | test_sop_full_lifecycle | 191-196 |

---

#### REQ-TASK-003: QA Auto-Assignment

**Requirement:** When routing for review, the CLI shall automatically add QA to the pending_assignees list regardless of explicit assignment.

| Test File | Test Function | Lines |
|-----------|---------------|-------|
| test_sop_lifecycle.py | test_sop_full_lifecycle | 187-191 |

---

#### REQ-TASK-004: Task Removal on Completion

**Requirement:** When a user completes a review or approval action, the CLI shall remove their corresponding task file from their inbox.

| Test File | Test Function | Lines |
|-----------|---------------|-------|
| test_sop_lifecycle.py | test_sop_full_lifecycle | 216-218 |

---

### 5.7 Project Configuration (REQ-CFG)

#### REQ-CFG-001: Project Root Discovery

**Requirement:** The CLI shall discover the project root by searching for the QMS/ directory, starting from the current working directory and traversing upward.

| Test File | Test Function | Lines |
|-----------|---------------|-------|
| conftest.py | temp_project fixture | 15-90 |

---

#### REQ-CFG-002: QMS Root Path

**Requirement:** The CLI shall resolve the QMS document root as `{PROJECT_ROOT}/QMS/`. All controlled documents, metadata, and audit trails shall reside under this path.

| Test File | Test Function | Lines |
|-----------|---------------|-------|
| test_sop_lifecycle.py | test_sop_full_lifecycle | 105-110 |

---

#### REQ-CFG-003: Users Directory Path

**Requirement:** The CLI shall resolve the users directory (containing workspaces and inboxes) as `{PROJECT_ROOT}/.claude/users/`.

| Test File | Test Function | Lines |
|-----------|---------------|-------|
| test_sop_lifecycle.py | test_sop_full_lifecycle | 157-167, 187-191 |

---

#### REQ-CFG-004: Agents Directory Path

**Requirement:** The CLI shall resolve the agents directory (containing agent definition files) as `{PROJECT_ROOT}/.claude/agents/`.

| Test File | Test Function | Lines |
|-----------|---------------|-------|
| conftest.py | temp_project fixture | 75-90 |

---

#### REQ-CFG-005: User Registry

**Requirement:** The CLI shall maintain a registry of valid users, including: (1) the set of all valid user identifiers, and (2) group membership for each user (Initiators, QA, or Reviewers).

| Test File | Test Function | Lines |
|-----------|---------------|-------|
| test_security.py | test_unknown_user_rejection | 271-288 |

---

#### REQ-CFG-006: Document Type Registry

**Requirement:** The CLI shall maintain a registry of document types, including for each type: (1) storage path relative to QMS root, (2) executable flag, (3) ID prefix, (4) parent type (if child document), and (5) folder-per-document flag.

| Test File | Test Function | Lines |
|-----------|---------------|-------|
| test_document_types.py | test_create_sop | 44-60 |
| test_document_types.py | test_create_cr | 62-80 |
| test_document_types.py | test_create_inv | 82-100 |

---

#### REQ-CFG-007: Agent Definition Loading

**Requirement:** For agent users (non-human), the CLI shall support loading agent definition files from the agents directory. Agent definitions provide behavioral context for spawned subagents.

| Test File | Test Function | Lines |
|-----------|---------------|-------|
| conftest.py | temp_project fixture | 75-90 |

---

### 5.8 Query Operations (REQ-QRY)

#### REQ-QRY-001: Document Reading

**Requirement:** The CLI shall provide the ability to read any document's content. Reading shall support: (1) the current effective version, (2) the current draft version if one exists, and (3) any archived version by version number.

| Test File | Test Function | Lines |
|-----------|---------------|-------|
| test_queries.py | test_read_draft | 44-58 |
| test_queries.py | test_read_effective | 60-81 |
| test_queries.py | test_read_archived_version | 83-105 |
| test_queries.py | test_read_draft_flag | 107-139 |

---

#### REQ-QRY-002: Document Status Query

**Requirement:** The CLI shall provide the ability to query a document's current workflow state, including: doc_id, title, version, status, document type, executable flag, responsible_user, and checked_out status.

| Test File | Test Function | Lines |
|-----------|---------------|-------|
| test_queries.py | test_status_query | 142-164 |
| test_queries.py | test_status_shows_checked_out | 166-189 |

---

#### REQ-QRY-003: Audit History Query

**Requirement:** The CLI shall provide the ability to retrieve the complete audit trail for a document, displaying all recorded events in chronological order.

| Test File | Test Function | Lines |
|-----------|---------------|-------|
| test_queries.py | test_history_query | 191-217 |
| test_queries.py | test_history_shows_all_event_types | 219-245 |

---

#### REQ-QRY-004: Review Comments Query

**Requirement:** The CLI shall provide the ability to retrieve review comments for a document, filtered by version. Comments shall be extracted from REVIEW and REJECT events in the audit trail.

| Test File | Test Function | Lines |
|-----------|---------------|-------|
| test_queries.py | test_comments_query | 248-266 |
| test_queries.py | test_comments_includes_rejection | 268-291 |

---

#### REQ-QRY-005: Inbox Query

**Requirement:** The CLI shall provide the ability for a user to list all pending tasks in their inbox, showing task type, document ID, and assignment date.

| Test File | Test Function | Lines |
|-----------|---------------|-------|
| test_queries.py | test_inbox_query | 294-312 |
| test_queries.py | test_inbox_multiple_tasks | 314-335 |
| test_queries.py | test_inbox_empty_when_no_tasks | 337-352 |

---

#### REQ-QRY-006: Workspace Query

**Requirement:** The CLI shall provide the ability for a user to list all documents currently checked out to their workspace.

| Test File | Test Function | Lines |
|-----------|---------------|-------|
| test_queries.py | test_workspace_query | 355-369 |
| test_queries.py | test_workspace_multiple_documents | 371-390 |
| test_queries.py | test_workspace_empty_after_checkin | 392-410 |

---

## 6. Test Execution Summary

### 6.1 Qualified Baseline

| Attribute | Value |
|-----------|-------|
| Repository | whharris917/qms-cli |
| Commit | `9fd2d72` |
| Date | 2026-01-19 |
| CI Evidence | [GitHub Actions](https://github.com/whharris917/qms-cli/actions) |
| Total Tests | 54 |
| Passed | 54 |
| Failed | 0 |

### 6.2 Test Protocol Results

| Test Protocol | Tests | Passed | Failed | Verification |
|---------------|-------|--------|--------|--------------|
| test_sop_lifecycle.py | 8 | 8 | 0 | Non-executable workflow |
| test_cr_lifecycle.py | 8 | 8 | 0 | Executable workflow |
| test_security.py | 10 | 10 | 0 | Access control |
| test_document_types.py | 12 | 12 | 0 | Creation, child docs |
| test_queries.py | 16 | 16 | 0 | Read, status, history |
| **Total** | **54** | **54** | **0** | |

### 6.3 Execution Notes

- Tests executed via GitHub Actions CI on push to main branch
- All tests run in isolated temporary environments (no production QMS impact)
- CI provides independent, timestamped, immutable record of test results
- CR-032 closed 2026-01-19 after fixing 5 implementation gaps identified during initial qualification

---

## 7. References

- SDLC-QMS-RS: QMS CLI Requirements Specification
- SOP-007: Software Development Lifecycle

---

**END OF DOCUMENT**

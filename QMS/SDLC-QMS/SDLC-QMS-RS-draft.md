---
title: QMS CLI Requirements Specification
revision_summary: Initial draft
---

# SDLC-QMS-RS: QMS CLI Requirements Specification

## 1. Purpose

This document specifies the functional requirements for the QMS CLI (`qms-cli/`), the command-line tool that implements and enforces the Quality Management System procedures.

These requirements serve as the authoritative specification for QMS CLI behavior. All requirements are verifiable through unit tests or qualitative proofs documented in SDLC-QMS-RTM.

---

## 2. Scope

This specification covers:

- Security and access control
- Document lifecycle management (creation, checkout, checkin)
- Workflow state machine and status transitions
- Metadata architecture (three-tier separation)
- Audit trail logging
- Task and inbox management

This specification does not cover:

- User interface design or command-line argument syntax
- Internal implementation architecture
- Performance characteristics

---

## 3. Requirements

### 3.1 Security (REQ-SEC)

| REQ ID | Requirement | Verification |
|--------|-------------|--------------|
| REQ-SEC-001 | **User Group Classification.** The CLI shall classify all users into exactly one of three groups: Initiators, QA, or Reviewers. | Unit test: verify get_user_group() returns correct group for each configured user |
| REQ-SEC-002 | **Group-Based Action Authorization.** The CLI shall authorize actions based on user group membership: create, checkout, checkin, route, release, revert, close (Initiators); assign (QA); fix (QA and Initiators). | Unit test: verify check_permission() for each action/group combination |
| REQ-SEC-003 | **Owner-Only Restrictions.** The CLI shall restrict checkin, release, revert, and close actions to the document's responsible_user (owner). | Unit test: verify owner-only commands reject non-owners |
| REQ-SEC-004 | **Assignment-Based Review Access.** The CLI shall permit review and approve actions only for users listed in the document's pending_assignees. QA shall always be permitted to review and approve regardless of explicit assignment. | Unit test: verify review/approve checks pending_assignees; QA always permitted |
| REQ-SEC-005 | **Rejection Access.** The CLI shall permit reject actions using the same authorization rules as approve (pending_assignees or QA). | Unit test: verify reject uses same authorization as approve |

---

### 3.2 Document Management (REQ-DOC)

| REQ ID | Requirement | Verification |
|--------|-------------|--------------|
| REQ-DOC-001 | **Supported Document Types.** The CLI shall support creation and management of the following document types: SOP, CR, INV, TP, ER, VAR, CAPA, RS, RTM, and TEMPLATE. | Unit test: verify each doc type exists in DOCUMENT_TYPES config |
| REQ-DOC-002 | **Child Document Relationships.** The CLI shall enforce parent-child relationships: TP is a child of CR; ER is a child of TP; CAPA is a child of INV; VAR is a child of CR or INV. Child documents shall be stored within their parent's folder. | Qualitative proof: code inspection of parent-child config and path resolution in qms_config.py and qms_paths.py |
| REQ-DOC-003 | **QMS Folder Structure.** The CLI shall maintain the following folder structure: QMS/ for controlled documents organized by type; QMS/.meta/ for workflow state sidecar files; QMS/.audit/ for audit trail logs; QMS/.archive/ for superseded versions; and per-user workspace and inbox directories. | Qualitative proof: code inspection of path functions in qms_paths.py |
| REQ-DOC-004 | **Sequential ID Generation.** The CLI shall generate document IDs sequentially within each document type (e.g., CR-001, CR-002, SOP-001, SOP-002). The next available number shall be determined by scanning existing documents. | Unit test: test_qms_paths.py::test_get_next_doc_number |
| REQ-DOC-005 | **Child Document ID Generation.** For child document types, the CLI shall generate IDs in the format `{PARENT}-{TYPE}-NNN` where NNN is sequential within that parent (e.g., CR-005-VAR-001, CR-005-VAR-002). | Unit test: test_qms_paths.py::test_var_type, test_var_path |
| REQ-DOC-006 | **Version Format.** The CLI shall enforce version numbers in the format `N.X` where N = approval number (major version) and X = revision number within approval cycle (minor version). Initial documents shall start at version 0.1. | Unit test: verify version format validation in qms_schema.py |
| REQ-DOC-007 | **Checkout Creates Draft.** When a user checks out an EFFECTIVE document, the CLI shall: (1) create a new draft version at N.1, (2) copy the document to the user's workspace, (3) set the user as responsible_user, and (4) mark the document as checked_out. | Integration test: checkout effective doc, verify draft version, workspace copy, metadata updates |
| REQ-DOC-008 | **Checkin Updates QMS.** When a user checks in a document, the CLI shall: (1) copy the document from workspace to QMS working directory, (2) archive any previous draft version, and (3) maintain the user as responsible_user. | Integration test: checkin doc, verify QMS copy exists, previous archived, metadata preserved |
| REQ-DOC-009 | **Checkin Reverts Reviewed Status.** When a document in REVIEWED, PRE_REVIEWED, or POST_REVIEWED status is checked in, the CLI shall revert the status to DRAFT (for non-executable) or the appropriate pre-review state (for executable) to require a new review cycle. | Unit test: verify checkin from REVIEWED states reverts to DRAFT |
| REQ-DOC-010 | **Cancel Restrictions.** The CLI shall only permit cancellation of documents with version < 1.0 (never approved). Cancellation shall permanently delete the document file, metadata, and audit trail. | Unit test: verify cancel rejected for v>=1.0; verify files deleted for v<1.0 |

---

### 3.3 Workflow State Machine (REQ-WF)

| REQ ID | Requirement | Verification |
|--------|-------------|--------------|
| REQ-WF-001 | **Status Transition Validation.** The CLI shall reject any status transition not defined in the workflow state machine. Invalid transitions shall produce an error without modifying document state. | Unit test: test_workflow.py::TestTransitionValidation |
| REQ-WF-002 | **Non-Executable Document Lifecycle.** Non-executable documents (SOP, RS, RTM) shall follow this status progression: DRAFT → IN_REVIEW → REVIEWED → IN_APPROVAL → APPROVED → EFFECTIVE. SUPERSEDED and RETIRED are terminal states. | Unit test: test_workflow.py - verify non-exec transitions |
| REQ-WF-003 | **Executable Document Lifecycle.** Executable documents (CR, INV, TP, ER, VAR) shall follow this status progression: DRAFT → IN_PRE_REVIEW → PRE_REVIEWED → IN_PRE_APPROVAL → PRE_APPROVED → IN_EXECUTION → IN_POST_REVIEW → POST_REVIEWED → IN_POST_APPROVAL → POST_APPROVED → CLOSED. RETIRED is a terminal state. | Unit test: test_workflow.py - verify exec transitions |
| REQ-WF-004 | **Review Completion Gate.** The CLI shall automatically transition a document from IN_REVIEW to REVIEWED (or equivalent pre/post states) only when all users in pending_assignees have submitted reviews. | Unit test: test_workflow.py::TestReviewCompletion |
| REQ-WF-005 | **Approval Gate.** The CLI shall block routing for approval if any reviewer submitted a review with `request-updates` outcome. All reviews must have `recommend` outcome before approval routing is permitted. | Unit test: verify route --approval blocked when request-updates exists in audit |
| REQ-WF-006 | **Approval Version Bump.** Upon successful approval (all approvers complete), the CLI shall: (1) increment the major version (N.X → N+1.0), (2) archive the previous version, (3) transition to EFFECTIVE (non-executable) or PRE_APPROVED/POST_APPROVED (executable), and (4) clear the responsible_user. | Unit test: test_workflow.py::TestApprovalTransitions - verify version bump and state changes |
| REQ-WF-007 | **Rejection Handling.** When any approver rejects a document, the CLI shall transition the document back to the most recent REVIEWED state (REVIEWED, PRE_REVIEWED, or POST_REVIEWED) without incrementing the version. | Unit test: test_workflow.py::TestRejection |
| REQ-WF-008 | **Release Transition.** The CLI shall transition executable documents from PRE_APPROVED to IN_EXECUTION upon release command. Only the document owner may release. | Unit test: test_workflow.py::TestReleaseTransition |
| REQ-WF-009 | **Revert Transition.** The CLI shall transition executable documents from POST_REVIEWED to IN_EXECUTION upon revert command, requiring a reason. Only the document owner may revert. | Unit test: test_workflow.py::TestRevertTransition |
| REQ-WF-010 | **Close Transition.** The CLI shall transition executable documents from POST_APPROVED to CLOSED upon close command. Only the document owner may close. | Unit test: test_workflow.py::TestCloseTransition |
| REQ-WF-011 | **Terminal State Enforcement.** The CLI shall reject all transitions from terminal states (SUPERSEDED, CLOSED, RETIRED). | Unit test: test_workflow.py - verify no transitions from terminal states |

---

### 3.4 Metadata Architecture (REQ-META)

| REQ ID | Requirement | Verification |
|--------|-------------|--------------|
| REQ-META-001 | **Three-Tier Separation.** The CLI shall maintain strict separation between: Tier 1 (Frontmatter) for author-maintained fields only (title, revision_summary); Tier 2 (.meta/) for CLI-managed workflow state; and Tier 3 (.audit/) for immutable event history. | Qualitative proof: code architecture inspection showing three distinct storage mechanisms |
| REQ-META-002 | **CLI-Exclusive Metadata Management.** The CLI shall be the sole mechanism for modifying .meta/ sidecar files. Workflow state (version, status, responsible_user, pending_assignees) shall never be stored in document frontmatter. | Qualitative proof: verify .meta/ only modified via qms_meta.py functions; frontmatter filter in qms_io.py |
| REQ-META-003 | **Required Metadata Fields.** Each document's .meta/ file shall contain at minimum: doc_id, doc_type, version, status, executable (boolean), responsible_user (or null), checked_out (boolean), and pending_assignees (array). | Unit test: verify create_initial_meta() output contains all required fields |
| REQ-META-004 | **Execution Phase Tracking.** For executable documents, the CLI shall track the execution phase (pre_release or post_release) in metadata to correctly infer pre vs. post workflow stages. | Unit test: verify execution_phase field set correctly for executable docs after release |

---

### 3.5 Audit Trail (REQ-AUDIT)

| REQ ID | Requirement | Verification |
|--------|-------------|--------------|
| REQ-AUDIT-001 | **Append-Only Logging.** The CLI shall never modify or delete existing audit trail entries. All audit operations shall append new entries to the .audit/ JSONL files. | Qualitative proof: code inspection of qms_audit.py showing only file append operations |
| REQ-AUDIT-002 | **Required Event Types.** The CLI shall log the following events to the audit trail: CREATE, CHECKOUT, CHECKIN, ROUTE_REVIEW, ROUTE_APPROVAL, REVIEW, APPROVE, REJECT, EFFECTIVE, RELEASE, REVERT, CLOSE, RETIRE. | Unit test: verify each event type logged by corresponding command |
| REQ-AUDIT-003 | **Event Attribution.** Each audit event shall include: timestamp (ISO 8601 format), event type, user who performed the action, and document version at time of event. | Unit test: verify audit event structure includes ts, event, user, version fields |
| REQ-AUDIT-004 | **Comment Preservation.** Review comments and rejection rationale shall be stored only in the audit trail, not in document content or metadata. | Qualitative proof: verify comments stored in audit REVIEW/REJECT events only; not in .meta/ or frontmatter |

---

### 3.6 Task & Inbox Management (REQ-TASK)

| REQ ID | Requirement | Verification |
|--------|-------------|--------------|
| REQ-TASK-001 | **Task Generation on Routing.** When a document is routed for review or approval, the CLI shall create task files in each assigned user's inbox directory. | Integration test: route document, verify task files created in assignee inboxes |
| REQ-TASK-002 | **Task Content Requirements.** Generated task files shall include: task_id (unique identifier), task_type (REVIEW or APPROVAL), workflow_type, doc_id, version, assigned_by, and assigned_date. | Unit test: verify generated task content contains all required fields |
| REQ-TASK-003 | **QA Auto-Assignment.** When routing for review, the CLI shall automatically add QA to the pending_assignees list regardless of explicit assignment. | Unit test: verify qa always in pending_assignees after route --review |
| REQ-TASK-004 | **Task Removal on Completion.** When a user completes a review or approval action, the CLI shall remove their corresponding task file from their inbox. | Integration test: complete review, verify task file removed from inbox |

---

**END OF DOCUMENT**

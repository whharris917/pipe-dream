---
title: QMS CLI Requirements Specification
revision_summary: Convert verification methods to maximal behavioral testing
---

# SDLC-QMS-RS: QMS CLI Requirements Specification

## 1. Purpose

This document specifies the functional requirements for the QMS CLI (`qms-cli/`), the command-line tool that implements and enforces the Quality Management System procedures.

These requirements serve as the authoritative specification for QMS CLI behavior. Verification evidence demonstrating compliance with each requirement is documented in SDLC-QMS-RTM.

---

## 2. Scope

This specification covers:

- Security and access control
- Document lifecycle management (creation, checkout, checkin)
- Workflow state machine and status transitions
- Metadata architecture (three-tier separation)
- Audit trail logging
- Task and inbox management
- Project configuration (paths, registries, agent definitions)
- Query operations (reading, status, history, comments)

This specification does not cover:

- User interface design or command-line argument syntax
- Internal implementation architecture
- Performance characteristics

---

## 3. Requirements

### 3.1 Security (REQ-SEC)

| REQ ID | Requirement |
|--------|-------------|
| REQ-SEC-001 | **User Group Classification.** The CLI shall classify all users into exactly one of three groups: Initiators, QA, or Reviewers. |
| REQ-SEC-002 | **Group-Based Action Authorization.** The CLI shall authorize actions based on user group membership: create, checkout, checkin, route, release, revert, close (Initiators); assign (QA); fix (QA, lead). |
| REQ-SEC-003 | **Owner-Only Restrictions.** The CLI shall restrict checkin, route, release, revert, and close actions to the document's responsible_user (owner). |
| REQ-SEC-004 | **Assignment-Based Review Access.** The CLI shall permit review and approve actions only for users listed in the document's pending_assignees. |
| REQ-SEC-005 | **Rejection Access.** The CLI shall permit reject actions using the same authorization rules as approve (pending_assignees). |
| REQ-SEC-006 | **Unknown User Rejection.** The CLI shall reject any command invoked with a user identifier not present in the user registry, returning an error without modifying any state. |

---

### 3.2 Document Management (REQ-DOC)

| REQ ID | Requirement |
|--------|-------------|
| REQ-DOC-001 | **Supported Document Types.** The CLI shall support creation and management of the following document types: SOP, CR, INV, TP, ER, VAR, RS, RTM, and TEMPLATE. |
| REQ-DOC-002 | **Child Document Relationships.** The CLI shall enforce parent-child relationships: TP is a child of CR; ER is a child of TP; VAR is a child of CR or INV. Child documents shall be stored within their parent's folder. |
| REQ-DOC-003 | **QMS Folder Structure.** The CLI shall maintain the following folder structure: QMS/ for controlled documents organized by type; QMS/.meta/ for workflow state sidecar files; QMS/.audit/ for audit trail logs; QMS/.archive/ for superseded versions; and per-user workspace and inbox directories. |
| REQ-DOC-004 | **Sequential ID Generation.** The CLI shall generate document IDs sequentially within each document type (e.g., CR-001, CR-002, SOP-001, SOP-002). The next available number shall be determined by scanning existing documents. |
| REQ-DOC-005 | **Child Document ID Generation.** For child document types, the CLI shall generate IDs in the format `{PARENT}-{TYPE}-NNN` where NNN is sequential within that parent (e.g., CR-005-VAR-001, CR-005-VAR-002). |
| REQ-DOC-006 | **Version Format.** The CLI shall enforce version numbers in the format `N.X` where N = approval number (major version) and X = revision number within approval cycle (minor version). Initial documents shall start at version 0.1. |
| REQ-DOC-007 | **Checkout Behavior.** The CLI shall permit checkout of any document not currently checked out by another user. On checkout, the CLI shall: (1) copy the document to the user's workspace, (2) set the user as responsible_user, (3) mark the document as checked_out, and (4) if the document is EFFECTIVE, create a new draft version at N.1. |
| REQ-DOC-008 | **Checkin Updates QMS.** When a user checks in a document, the CLI shall: (1) copy the document from workspace to QMS working directory, (2) archive any previous draft version, and (3) maintain the user as responsible_user. |
| REQ-DOC-009 | **Checkin Reverts Reviewed Status.** When a document in REVIEWED, PRE_REVIEWED, or POST_REVIEWED status is checked in, the CLI shall revert the status to DRAFT (for non-executable) or the appropriate pre-review state (for executable) to require a new review cycle. |
| REQ-DOC-010 | **Cancel Restrictions.** The CLI shall only permit cancellation of documents with version < 1.0 (never approved). Cancellation shall permanently delete the document file, metadata, and audit trail. |
| REQ-DOC-011 | **Template Name-Based ID.** Template documents shall use name-based identifiers in the format `TEMPLATE-{NAME}` rather than sequential numbering. The name shall be specified at creation time. |
| REQ-DOC-012 | **SDLC Document Types.** The CLI shall support RS and RTM documents for configured SDLC namespaces. Each namespace requires explicit configuration in DOCUMENT_TYPES specifying the document ID prefix (e.g., SDLC-FLOW-RS, SDLC-QMS-RTM) and storage path. Documents shall be stored in `QMS/SDLC-{NAMESPACE}/`. |

---

### 3.3 Workflow State Machine (REQ-WF)

| REQ ID | Requirement |
|--------|-------------|
| REQ-WF-001 | **Status Transition Validation.** The CLI shall reject any status transition not defined in the workflow state machine. Invalid transitions shall produce an error without modifying document state. |
| REQ-WF-002 | **Non-Executable Document Lifecycle.** Non-executable documents shall follow this status progression: DRAFT → IN_REVIEW → REVIEWED → IN_APPROVAL → APPROVED → EFFECTIVE. SUPERSEDED and RETIRED are terminal states. |
| REQ-WF-003 | **Executable Document Lifecycle.** Executable documents (CR, INV, TP, ER, VAR) shall follow this status progression: DRAFT → IN_PRE_REVIEW → PRE_REVIEWED → IN_PRE_APPROVAL → PRE_APPROVED → IN_EXECUTION → IN_POST_REVIEW → POST_REVIEWED → IN_POST_APPROVAL → POST_APPROVED → CLOSED. RETIRED is a terminal state. |
| REQ-WF-004 | **Review Completion Gate.** The CLI shall automatically transition a document from IN_REVIEW to REVIEWED (or equivalent pre/post states) only when all users in pending_assignees have submitted reviews. |
| REQ-WF-005 | **Approval Gate.** The CLI shall block routing for approval if any reviewer submitted a review with `request-updates` outcome. All reviews must have `recommend` outcome before approval routing is permitted. |
| REQ-WF-006 | **Approval Version Bump.** Upon successful approval (all approvers complete), the CLI shall: (1) increment the major version (N.X → N+1.0), (2) archive the previous version, (3) transition to EFFECTIVE (non-executable) or PRE_APPROVED/POST_APPROVED (executable), and (4) clear the responsible_user. |
| REQ-WF-007 | **Rejection Handling.** When any approver rejects a document, the CLI shall transition the document back to the most recent REVIEWED state (REVIEWED, PRE_REVIEWED, or POST_REVIEWED) without incrementing the version. |
| REQ-WF-008 | **Release Transition.** The CLI shall transition executable documents from PRE_APPROVED to IN_EXECUTION upon release command. Only the document owner may release. |
| REQ-WF-009 | **Revert Transition.** The CLI shall transition executable documents from POST_REVIEWED to IN_EXECUTION upon revert command, requiring a reason. Only the document owner may revert. |
| REQ-WF-010 | **Close Transition.** The CLI shall transition executable documents from POST_APPROVED to CLOSED upon close command. Only the document owner may close. |
| REQ-WF-011 | **Terminal State Enforcement.** The CLI shall reject all transitions from terminal states (SUPERSEDED, CLOSED, RETIRED). |
| REQ-WF-012 | **Retirement Routing.** The CLI shall support routing for retirement approval, which signals that approval leads to RETIRED status rather than EFFECTIVE or PRE_APPROVED. Retirement routing shall only be permitted for documents with version >= 1.0 (once-effective). |
| REQ-WF-013 | **Retirement Transition.** Upon approval of a retirement-routed document, the CLI shall: (1) archive the document to `.archive/`, (2) remove the working copy from the QMS directory, (3) transition status to RETIRED, and (4) log a RETIRE event to the audit trail. |

---

### 3.4 Metadata Architecture (REQ-META)

| REQ ID | Requirement |
|--------|-------------|
| REQ-META-001 | **Three-Tier Separation.** The CLI shall maintain strict separation between: Tier 1 (Frontmatter) for author-maintained fields only (title, revision_summary); Tier 2 (.meta/) for CLI-managed workflow state; and Tier 3 (.audit/) for immutable event history. |
| REQ-META-002 | **CLI-Exclusive Metadata Management.** The CLI shall be the sole mechanism for modifying .meta/ sidecar files. Workflow state (version, status, responsible_user, pending_assignees) shall never be stored in document frontmatter. |
| REQ-META-003 | **Required Metadata Fields.** Each document's .meta/ file shall contain at minimum: doc_id, doc_type, version, status, executable (boolean), responsible_user (or null), checked_out (boolean), and pending_assignees (array). |
| REQ-META-004 | **Execution Phase Tracking.** For executable documents, the CLI shall track the execution phase (pre_release or post_release) in metadata to correctly infer pre vs. post workflow stages. |

---

### 3.5 Audit Trail (REQ-AUDIT)

| REQ ID | Requirement |
|--------|-------------|
| REQ-AUDIT-001 | **Append-Only Logging.** The CLI shall never modify or delete existing audit trail entries. All audit operations shall append new entries to the .audit/ JSONL files. |
| REQ-AUDIT-002 | **Required Event Types.** The CLI shall log the following events to the audit trail: CREATE, CHECKOUT, CHECKIN, ROUTE_REVIEW, ROUTE_APPROVAL, REVIEW, APPROVE, REJECT, EFFECTIVE, RELEASE, REVERT, CLOSE, RETIRE, STATUS_CHANGE. |
| REQ-AUDIT-003 | **Event Attribution.** Each audit event shall include: timestamp (ISO 8601 format), event type, user who performed the action, and document version at time of event. |
| REQ-AUDIT-004 | **Comment Preservation.** Review comments and rejection rationale shall be stored only in the audit trail, not in document content or metadata. |

---

### 3.6 Task & Inbox Management (REQ-TASK)

| REQ ID | Requirement |
|--------|-------------|
| REQ-TASK-001 | **Task Generation on Routing.** When a document is routed for review or approval, the CLI shall create task files in each assigned user's inbox directory. |
| REQ-TASK-002 | **Task Content Requirements.** Generated task files shall include: task_id (unique identifier), task_type (REVIEW or APPROVAL), workflow_type, doc_id, version, assigned_by, and assigned_date. |
| REQ-TASK-003 | **QA Auto-Assignment.** When routing for review, the CLI shall automatically add QA to the pending_assignees list regardless of explicit assignment. |
| REQ-TASK-004 | **Task Removal on Completion.** When a user completes a review or approval action, the CLI shall remove their corresponding task file from their inbox. |

---

### 3.7 Project Configuration (REQ-CFG)

| REQ ID | Requirement |
|--------|-------------|
| REQ-CFG-001 | **Project Root Discovery.** The CLI shall discover the project root by searching for the QMS/ directory, starting from the current working directory and traversing upward. |
| REQ-CFG-002 | **QMS Root Path.** The CLI shall resolve the QMS document root as `{PROJECT_ROOT}/QMS/`. All controlled documents, metadata, and audit trails shall reside under this path. |
| REQ-CFG-003 | **Users Directory Path.** The CLI shall resolve the users directory (containing workspaces and inboxes) as `{PROJECT_ROOT}/.claude/users/`. |
| REQ-CFG-004 | **Agents Directory Path.** The CLI shall resolve the agents directory (containing agent definition files) as `{PROJECT_ROOT}/.claude/agents/`. |
| REQ-CFG-005 | **User Registry.** The CLI shall maintain a registry of valid users, including: (1) the set of all valid user identifiers, and (2) group membership for each user (Initiators, QA, or Reviewers). |
| REQ-CFG-006 | **Document Type Registry.** The CLI shall maintain a registry of document types, including for each type: (1) storage path relative to QMS root, (2) executable flag, (3) ID prefix, (4) parent type (if child document), and (5) folder-per-document flag. |
| REQ-CFG-007 | **Agent Definition Loading.** For agent users (non-human), the CLI shall support loading agent definition files from the agents directory. Agent definitions provide behavioral context for spawned subagents. |

---

### 3.8 Query Operations (REQ-QRY)

| REQ ID | Requirement |
|--------|-------------|
| REQ-QRY-001 | **Document Reading.** The CLI shall provide the ability to read any document's content. Reading shall support: (1) the current effective version, (2) the current draft version if one exists, and (3) any archived version by version number. |
| REQ-QRY-002 | **Document Status Query.** The CLI shall provide the ability to query a document's current workflow state, including: doc_id, title, version, status, document type, executable flag, responsible_user, and checked_out status. |
| REQ-QRY-003 | **Audit History Query.** The CLI shall provide the ability to retrieve the complete audit trail for a document, displaying all recorded events in chronological order. |
| REQ-QRY-004 | **Review Comments Query.** The CLI shall provide the ability to retrieve review comments for a document, filtered by version. Comments shall be extracted from REVIEW and REJECT events in the audit trail. |
| REQ-QRY-005 | **Inbox Query.** The CLI shall provide the ability for a user to list all pending tasks in their inbox, showing task type, document ID, and assignment date. |
| REQ-QRY-006 | **Workspace Query.** The CLI shall provide the ability for a user to list all documents currently checked out to their workspace. |

---

**END OF DOCUMENT**

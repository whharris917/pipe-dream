---
title: QMS CLI Requirements Specification
revision_summary: 'CR-091: Interaction system engine — add REQ-INT section (22 requirements
  for template-driven interactive authoring of VR documents)'
---

# SDLC-QMS-RS: QMS CLI Requirements Specification

## 1. Purpose

This document specifies the functional requirements for the QMS CLI (`qms-cli/`), the command-line tool that implements and enforces the Quality Management System procedures.

These requirements serve as the authoritative specification for QMS CLI behavior. Verification evidence demonstrating compliance with each requirement is documented in SDLC-QMS-RTM.

---

## 2. Scope

This specification covers:

- Project initialization and bootstrapping
- User identity and group management
- Security and access control
- Document lifecycle management (creation, checkout, checkin)
- Workflow state machine and status transitions
- Metadata architecture (three-tier separation)
- Audit trail logging
- Task and inbox management
- Project configuration (paths, registries)
- Query operations (reading, status, history, comments)
- Prompt generation for review and approval tasks
- Document template scaffolding
- MCP server for programmatic tool access
- Interactive document authoring (template-driven prompting for VR documents)

This specification does not cover:

- User interface design or command-line argument syntax
- Internal implementation architecture
- Performance characteristics

See Section 5 for environmental assumptions and exclusions.

---

## 3. System Overview

*This section provides context for understanding the requirements. It is informative, not normative—the requirements in Section 4 are the authoritative specification.*

### 3.1 What the QMS CLI Does

The QMS CLI is a command-line tool that enforces document control procedures. It manages the lifecycle of controlled documents—from creation through review, approval, and eventual retirement. The CLI ensures that:

- Only authorized users can perform specific actions
- Documents follow defined workflow progressions
- All changes are logged to an immutable audit trail
- Review and approval gates are enforced before documents become effective

### 3.2 Key Concepts

**Documents** are markdown files stored in the `QMS/` directory. Each document has:
- A unique identifier (e.g., `SOP-001`, `CR-028`)
- A type that determines its workflow (executable vs. non-executable)
- A version number (`N.X` format)
- A status indicating its position in the workflow

**Users** are classified into four groups with hierarchical permissions:
- **Administrator** (lead, claude): All initiator permissions plus administrative commands (fix)
- **Initiator** (empty, reserved for future non-admin initiators): Create documents, initiate workflows
- **Quality** (qa): Assign reviewers, review, approve
- **Reviewer** (tu_ui, tu_scene, etc.): Review and approve when assigned

User identity is determined by: (1) hardcoded administrators (`lead` and `claude`), or (2) agent definition files in `.claude/agents/{user}.md` with `group:` frontmatter specifying group membership.

**Workflows** are state machines that documents traverse:
- **Non-executable** (SOP, RS, RTM): DRAFT → review → approval → EFFECTIVE
- **Executable** (CR, INV, VAR, ADD, VR): DRAFT → pre-review → pre-approval → EXECUTION → post-review → post-approval → CLOSED
- **VR exception**: VR documents are born IN_EXECUTION at v1.0 (template serves as pre-approval authority), then follow the standard post-execution workflow

### 3.3 The Command Model

Every CLI command follows the same pattern:

```
authorize(user, action, document)
  → validate_precondition(status, action)
  → transform_state(action, parameters)
  → append_audit_log(event)
```

Authorization checks three conditions:
1. **Group membership**: Is the user's group permitted for this action?
2. **Ownership**: If action requires ownership, is user the responsible_user?
3. **Assignment**: If action requires assignment, is user in pending_assignees?

### 3.4 State Separation

The CLI maintains strict separation between three tiers of data:

| Tier | Location | Purpose | Mutability |
|------|----------|---------|------------|
| 1 | Document frontmatter | Author-maintained fields (title, revision_summary) | User-editable |
| 2 | `.meta/` sidecar files | Workflow state (version, status, assignees) | CLI-only |
| 3 | `.audit/` log files | Event history | Append-only |

This separation ensures that workflow state cannot be tampered with by editing document content.

### 3.5 The Review/Approval Cycle

Documents progress through review and approval in a consistent pattern:

1. **Route for review**: Owner submits document; QA is auto-assigned
2. **Assign reviewers**: QA optionally adds domain experts (TU agents)
3. **Submit reviews**: Each assignee reviews and recommends (or requests updates)
4. **Route for approval**: Once all reviewers recommend, owner routes for approval
5. **Approve**: Approvers approve (bumps version) or reject (returns to reviewed state)

For executable documents, this cycle happens twice: once before execution (pre-review/pre-approval) and once after (post-review/post-approval).

### 3.6 Document Lifecycle Diagrams

**Non-Executable (SOP, RS, RTM):**
```
DRAFT ──route──▶ IN_REVIEW ──all reviewed──▶ REVIEWED ──route──▶ IN_APPROVAL ──approve──▶ EFFECTIVE
                     ▲                            │                    │
                     └────────────────────────────┴───────reject───────┘
```

**Executable (CR, INV, TP, ER, VAR, ADD, VR):**
```
DRAFT ──▶ IN_PRE_REVIEW ──▶ PRE_REVIEWED ──▶ IN_PRE_APPROVAL ──▶ PRE_APPROVED
                                                                      │
                                                                   release
                                                                      ▼
CLOSED ◀── POST_APPROVED ◀── IN_POST_APPROVAL ◀── POST_REVIEWED ◀── IN_EXECUTION
                                    │                   │  ▲            ▲
                                    └──────reject───────┘  └───revert───┘
```

### 3.7 Workspaces and Checkout/Checkin

Users do not edit documents directly in the `QMS/` directory. Instead, the CLI enforces a **checkout/checkin** model:

1. **Checkout**: The user requests a document for editing. The CLI:
   - Copies the document to the user's **workspace** (`.claude/users/{user}/workspace/`)
   - Marks the document as checked out (preventing others from editing)
   - Sets the user as the document's `responsible_user` (owner)

2. **Edit**: The user modifies the document in their workspace using any text editor.

3. **Checkin**: The user submits their changes. The CLI:
   - Copies the edited document back to `QMS/`
   - Archives the previous version if needed
   - Logs the checkin to the audit trail

This model ensures that only one user edits a document at a time, and all changes flow through the CLI for proper logging and state management.

### 3.8 Inboxes and Task Routing

When a document is routed for review or approval, the CLI creates **task files** in each assigned user's **inbox** (`.claude/users/{user}/inbox/`). Each task file contains:

- The document ID and version to review
- The type of action required (REVIEW or APPROVAL)
- The workflow phase (e.g., PRE_REVIEW, POST_APPROVAL)
- Structured prompt content to guide the reviewer

Users check their inbox to see pending assignments. When they complete a review or approval action, the CLI removes the task from their inbox.

```
.claude/users/
├── claude/
│   ├── workspace/          # Documents checked out by claude
│   └── inbox/              # Review/approval tasks assigned to claude
├── qa/
│   ├── workspace/
│   └── inbox/
└── tu_ui/
    ├── workspace/
    └── inbox/
```

### 3.9 Document Templates

When creating a new document, the CLI populates it with initial content from a **template**. Templates are themselves controlled documents stored in `QMS/TEMPLATE/` with names like `TEMPLATE-CR.md` or `TEMPLATE-SOP.md`.

Templates support **variable substitution**:
- `{DOC_ID}` → The generated document ID (e.g., `CR-029`)
- `{TITLE}` → The user-provided title

This ensures new documents start with a consistent structure appropriate to their type, including required sections, placeholders, and formatting conventions.

### 3.10 The Prompt System

Review and approval tasks include **structured prompts** that guide reviewers through a verification checklist. The prompt system:

- **Loads configuration from YAML files** in `qms-cli/prompts/`
- **Uses hierarchical lookup**: document-type-specific prompts override phase-specific defaults, which override global defaults
- **Generates checklists** with verification items organized by category
- **Includes critical reminders** and response format guidance

For example, a CR post-review task might include prompts specific to verifying execution results, while an SOP review focuses on procedural clarity. This allows the QMS to tailor reviewer guidance without code changes.

### 3.11 Use Cases

#### Purpose and Flexibility

The QMS CLI can be used to implement a **GMP-inspired framework** for document management and change control. It enforces the procedural rigor found in regulated industries—review gates, approval workflows, audit trails, and version control—while remaining adaptable to different organizational needs.

This implementation of the QMS CLI has been **tailored to a specific set of SOPs** that are managed external to the code. The SOPs define the procedures (who does what, when, and why); the CLI enforces them. The code has been written in a modular way so that users could clone and modify the system relatively easily—customizing document types, templates, and workflows to implement their own specific GMP needs.

The CLI ships with **standard document types** based on existing quality management frameworks:

| Type | Purpose | Origin |
|------|---------|--------|
| **SOP** | Standard Operating Procedure | GMP, ISO 9001 |
| **CR** | Change Record | Change control systems |
| **INV** | Investigation | Deviation/CAPA management |
| **TP** | Test Protocol | Qualification/validation |
| **ER** | Exception Report | Variance for TPs; enables re-execution with modified test design |
| **VAR** | Variance | Non-conformance documentation |
| **ADD** | Addendum Report | Post-closure corrections to executable documents |
| **VR** | Verification Record | Structured behavioral verification evidence |

These document types are defined in the `DOCUMENT_TYPES` registry in the source code. Adding new types or modifying existing ones requires changes to the codebase, not runtime configuration.

#### Example: A Change Record in Practice

Consider a development team using the QMS to manage a software change. Here is how a Change Record (CR) would flow through the system:

**1. Initiation**

A developer (initiator) identifies a need to modify the codebase. They create a CR:

```
qms --user claude create CR --title "Add user authentication module"
```

The CLI generates `CR-029`, creates the document from the CR template, and places a working copy in the developer's workspace. The CR starts at version 0.1 in DRAFT status.

**2. Pre-Review**

The developer drafts the CR, describing the proposed change, its rationale, and the implementation plan. When ready, they route it for pre-review:

```
qms --user claude route CR-029 --review
```

QA is automatically assigned. QA may add domain experts (e.g., `tu_ui` for UI changes). Each reviewer receives a task in their inbox with a structured prompt guiding them through the review checklist.

**3. Pre-Approval**

Once all reviewers recommend the change, the developer routes for pre-approval:

```
qms --user claude route CR-029 --approval
```

QA reviews the accumulated feedback and approves the CR. The version bumps to 1.0 and status becomes PRE_APPROVED.

**4. Release and Execution**

The developer releases the CR for execution:

```
qms --user claude release CR-029
```

Status changes to IN_EXECUTION. The developer now implements the change—writing code, running tests, updating documentation. They may check out and check in the CR multiple times to update the execution notes.

**5. Handling a Non-Conformance (VAR)**

During execution, the developer discovers that one test case cannot be run as originally planned due to an environment limitation. This is a **variance**—a deviation from the approved plan that requires documentation and approval.

The developer creates a VAR under the CR:

```
qms --user claude create VAR --parent CR-029 --title "Skip integration test due to sandbox limitation"
```

The CLI generates `CR-029-VAR-001` and stores it within the CR's folder. The VAR goes through its own review/approval cycle:

- Developer documents the deviation and justification
- Routes for review → QA and relevant reviewers assess impact
- Routes for approval → If acceptable, VAR is approved
- VAR is released and closed

The VAR's audit trail is linked to the parent CR, providing traceability for why execution deviated from the plan.

**6. Post-Review and Closure**

With execution complete (including the documented variance), the developer routes the CR for post-review:

```
qms --user claude route CR-029 --review
```

Reviewers verify that:
- The implementation matches the approved plan (accounting for the VAR)
- Test results are documented
- All execution items are addressed

After post-review, the developer routes for post-approval. QA approves, and the developer closes the CR:

```
qms --user claude close CR-029
```

The CR reaches CLOSED status—a terminal state. The complete history—every checkout, checkin, review, approval, and the linked VAR—is preserved in the audit trail.

**7. The Audit Trail**

At any point, stakeholders can query the CR's history:

```
qms --user qa history CR-029
```

This returns a chronological record of every action taken on the document, by whom, and when. The audit trail provides the evidence needed for compliance reviews, retrospectives, or investigations.

---

## 4. Requirements

### 4.1 Security (REQ-SEC)

| REQ ID | Requirement |
|--------|-------------|
| REQ-SEC-001 | **User Group Classification.** The CLI shall classify all users into exactly one of four groups: administrator, initiator, quality, or reviewer. The administrator group inherits all initiator permissions. |
| REQ-SEC-002 | **Group-Based Action Authorization.** The CLI shall only permit actions when the user's group is authorized per the PERMISSIONS registry: initiator (and administrator): create, checkout, checkin, route, release, revert, close; quality: assign; administrator: fix. The CLI shall reject any action for which the user's group is not explicitly permitted. |
| REQ-SEC-003 | **Owner-Only Restrictions.** The CLI shall reject checkin, route, release, revert, and close commands when the user is not the document's responsible_user. |
| REQ-SEC-004 | **Assignment-Based Review Access.** The CLI shall reject review and approve actions unless the user is: (1) listed in the document's pending_assignees, AND (2) a member of an authorized group for that action. Authorized groups: review (administrator, initiator, quality, reviewer); approve (quality, reviewer). |
| REQ-SEC-005 | **Rejection Access.** The CLI shall permit reject actions using the same authorization rules as approve (pending_assignees membership plus quality or reviewer group). |
| REQ-SEC-006 | **Unknown User Rejection.** The CLI shall reject any command invoked with a user identifier not present in the user registry, returning an error without modifying any state. |
| REQ-SEC-007 | **Assignment Validation.** The CLI shall validate workflow assignments to ensure only authorized users are assigned. Review workflows: only users in administrator, initiator, quality, or reviewer groups may be assigned. Approval workflows: only users in quality or reviewer groups may be assigned. The CLI shall reject assignment attempts for users who would not be authorized to complete the workflow action. |
| REQ-SEC-008 | **Workspace/Inbox Isolation.** The CLI shall restrict workspace and inbox operations to the requesting user's own directories. Users shall not access, view, or modify other users' workspaces or inboxes. |

---

### 4.2 Document Management (REQ-DOC)

| REQ ID | Requirement |
|--------|-------------|
| REQ-DOC-001 | **Supported Document Types.** The CLI shall only support creation and management of the following document types: Core types (SOP, CR, INV, TP, ER, VAR, ADD, VR, TEMPLATE) and SDLC types (RS, RTM, available per registered SDLC namespace). The CLI shall reject create commands for undefined document types. |
| REQ-DOC-002 | **Child Document Relationships.** The CLI shall enforce parent-child relationships: TP is a child of CR; ER is a child of TP; VAR is a child of CR or INV; ADD is a child of CR, INV, VAR, or ADD; VR is a child of CR, VAR, or ADD. Child documents shall be stored within their parent's folder. |
| REQ-DOC-003 | **QMS Folder Structure.** The CLI shall maintain the following folder structure: QMS/ for controlled documents organized by type; QMS/.meta/ for workflow state sidecar files; QMS/.audit/ for audit trail logs; QMS/.archive/ for archived versions; and per-user workspace and inbox directories. The CLI shall reject operations that would store controlled documents outside this structure. |
| REQ-DOC-004 | **Sequential ID Generation.** The CLI shall generate document IDs sequentially within each document type (e.g., CR-001, CR-002, SOP-001, SOP-002). The next available number shall be determined by scanning existing documents. |
| REQ-DOC-005 | **Child Document ID Generation.** For child document types, the CLI shall generate IDs in the format `{PARENT}-{TYPE}-NNN` where NNN is sequential within that parent (e.g., CR-005-TP-001, CR-005-VAR-001, CR-005-VAR-002, CR-005-ADD-001, CR-005-VAR-001-ADD-001, CR-005-VR-001, CR-005-VAR-001-VR-001). |
| REQ-DOC-006 | **Version Format.** The CLI shall enforce version numbers in the format `N.X` where N = approval number (major version) and X = revision number within approval cycle (minor version). Initial documents shall start at version 0.1. |
| REQ-DOC-007 | **Checkout Behavior.** The CLI shall permit checkout of any document not currently checked out by another user. On checkout, the CLI shall: (1) if the document is in an active workflow state (IN_REVIEW, IN_APPROVAL, IN_PRE_REVIEW, IN_PRE_APPROVAL, IN_POST_REVIEW, IN_POST_APPROVAL), perform auto-withdraw per REQ-WF-022 before proceeding; (2) copy the document to the user's workspace, (3) set the user as responsible_user, (4) mark the document as checked_out, and (5) if the document is EFFECTIVE, archive the current effective version and create a new draft version at N.1. |
| REQ-DOC-008 | **Checkin Updates QMS.** When a user checks in a document, the CLI shall: (1) copy the document from workspace to QMS working directory, (2) remove the workspace copy, and (3) maintain the user as responsible_user. |
| REQ-DOC-009 | **Checkin Reverts Reviewed Status.** When a document in REVIEWED, PRE_REVIEWED, or POST_REVIEWED status is checked in, the CLI shall revert the status to DRAFT and clear all review tracking fields (pending_assignees, review outcomes) to require a new review cycle. |
| REQ-DOC-010 | **Cancel Restrictions.** The CLI shall only permit cancellation of documents with version < 1.0 (never approved) that are not currently checked out. Cancellation requires the --confirm flag and shall permanently delete the document file, metadata, audit trail, any workspace copies, and any related inbox tasks. |
| REQ-DOC-011 | **Template Name-Based ID.** Template documents shall use name-based identifiers in the format `TEMPLATE-{NAME}` rather than sequential numbering. The --name argument shall be required at creation time. |
| REQ-DOC-012 | **Folder-per-Document Storage.** CR and INV documents shall be stored in dedicated subdirectories using the pattern `QMS/{TYPE}/{DOC_ID}/`. Child documents (TP, VAR, ER, ADD) shall be stored within their parent document's directory. |
| REQ-DOC-013 | **SDLC Namespace Registration.** The CLI shall support SDLC namespace registration via the `namespace add` command. Registration creates the `QMS/SDLC-{NAME}/` directory structure and enables RS and RTM document types for that namespace (e.g., SDLC-MYPROJ-RS, SDLC-MYPROJ-RTM). Registered namespaces shall be persisted in configuration. |
| REQ-DOC-014 | **SDLC Document Identification.** SDLC documents shall be identified by the pattern `SDLC-{NAMESPACE}-{TYPE}` where NAMESPACE is a registered SDLC namespace and TYPE is RS or RTM. The CLI shall resolve document type and path dynamically from the namespace registry. |
| REQ-DOC-015 | **Addendum Parent State.** ADD documents shall only be created against parents in CLOSED state. The CLI shall reject ADD creation when the parent document status is not CLOSED. |
| REQ-DOC-016 | **VR Parent State.** VR documents shall only be created against parents in IN_EXECUTION state. The CLI shall reject VR creation when the parent document status is not IN_EXECUTION. |
| REQ-DOC-017 | **VR Initial Status.** VR documents shall be created with initial status IN_EXECUTION at version 1.0 with execution_phase set to post_release. The approved VR template serves as the pre-approval authority (batch record model). VR documents are checked out at creation, ready for the performer to fill in. |

---

### 4.3 Workflow State Machine (REQ-WF)

| REQ ID | Requirement |
|--------|-------------|
| REQ-WF-001 | **Status Transition Validation.** The CLI shall reject any status transition not defined in the workflow state machine. Invalid transitions shall produce an error without modifying document state. |
| REQ-WF-002 | **Non-Executable Document Lifecycle.** Non-executable documents shall follow this status progression: DRAFT → IN_REVIEW → REVIEWED → IN_APPROVAL → APPROVED → EFFECTIVE. RETIRED is a terminal state. |
| REQ-WF-003 | **Executable Document Lifecycle.** Executable documents (CR, INV, TP, ER, VAR, ADD, VR) shall follow this status progression: DRAFT → IN_PRE_REVIEW → PRE_REVIEWED → IN_PRE_APPROVAL → PRE_APPROVED → IN_EXECUTION → IN_POST_REVIEW → POST_REVIEWED → IN_POST_APPROVAL → POST_APPROVED → CLOSED. VR documents enter this progression at IN_EXECUTION per REQ-DOC-017. RETIRED is a terminal state. |
| REQ-WF-004 | **Review Completion Gate.** The CLI shall automatically transition a document from IN_REVIEW to REVIEWED (or equivalent pre/post states) only when all users in pending_assignees have submitted reviews. |
| REQ-WF-005 | **Approval Gate.** The CLI shall block routing for approval unless: (1) all submitted reviews have `recommend` outcome (no `request-updates`), AND (2) at least one review was submitted by a quality group member. This ensures both unanimous recommendation and mandatory quality oversight before approval. |
| REQ-WF-006 | **Approval Version Bump.** Upon successful approval (all approvers complete), the CLI shall: (1) increment the major version (N.X → N+1.0), (2) archive the previous version, (3) transition to EFFECTIVE (non-executable) or PRE_APPROVED/POST_APPROVED (executable), and (4) for non-executable documents, clear the responsible_user. |
| REQ-WF-007 | **Rejection Handling.** When any approver rejects a document, the CLI shall transition the document back to the most recent REVIEWED state (REVIEWED, PRE_REVIEWED, or POST_REVIEWED) without incrementing the version. |
| REQ-WF-008 | **Release Transition.** The CLI shall transition executable documents from PRE_APPROVED to IN_EXECUTION upon release command. Only the document owner may release. |
| REQ-WF-009 | **Revert Transition.** The CLI shall transition executable documents from POST_REVIEWED to IN_EXECUTION upon revert command, requiring a reason. Only the document owner may revert. |
| REQ-WF-010 | **Close Transition.** The CLI shall transition executable documents from POST_APPROVED to CLOSED upon close command. Only the document owner may close. |
| REQ-WF-011 | **Terminal State Enforcement.** The CLI shall reject all transitions from terminal states (CLOSED, RETIRED). |
| REQ-WF-012 | **Retirement Routing.** The CLI shall support routing for retirement approval, which signals that approval leads to RETIRED status rather than EFFECTIVE or PRE_APPROVED. Retirement routing shall only be permitted for documents with version >= 1.0 (once-effective). |
| REQ-WF-013 | **Retirement Transition.** Upon approval of a retirement-routed document, the CLI shall: (1) archive the document to `.archive/`, (2) remove the working copy from the QMS directory, (3) transition status to RETIRED, and (4) log a RETIRE event to the audit trail. |
| REQ-WF-014 | **Execution Phase Tracking.** For executable document types (CR, INV), the CLI shall track execution phase in metadata: pre_release (document approved but not yet released, PRE_APPROVED state) or post_release (document released and execution complete, POST_APPROVED state). The execution phase determines the correct workflow path. |
| REQ-WF-015 | **Checked-in Requirement for Routing.** The CLI shall require documents to be checked in before routing for review or approval. If the document is checked out by the responsible user, the CLI shall auto-checkin per REQ-WF-023 before proceeding with routing. If the document is checked out by a different user, routing shall be rejected with an error. |
| REQ-WF-016 | **Pre-Release Revision.** When a document in PRE_APPROVED status is checked out, the CLI shall: (1) transition status to DRAFT, (2) clear all pre-review/pre-approval tracking fields (pending_assignees, completed_reviewers, review_outcomes), and (3) copy the document to the user workspace. This allows scope revision through re-review before execution begins. |
| REQ-WF-017 | **Post-Review Continuation.** When a document in POST_REVIEWED status is checked out, the CLI shall: (1) transition status to IN_EXECUTION, (2) clear all post-review tracking fields, and (3) copy the document to the user workspace. This allows continued execution work without an intermediate DRAFT state. |
| REQ-WF-018 | **Withdraw Command.** The CLI shall provide a `withdraw` command that allows the responsible user to abort an in-progress review or approval workflow. Withdraw shall: (1) transition from IN_REVIEW to DRAFT, IN_APPROVAL to REVIEWED, IN_PRE_REVIEW to DRAFT, IN_PRE_APPROVAL to PRE_REVIEWED, IN_POST_REVIEW to IN_EXECUTION, IN_POST_APPROVAL to POST_REVIEWED; (2) clear pending_assignees and remove related inbox tasks; and (3) log a WITHDRAW event to the audit trail. Only the responsible_user may withdraw. |
| REQ-WF-019 | **Revert Command Deprecation.** The `revert` command is deprecated. When invoked, the CLI shall print a deprecation warning recommending checkout from POST_REVIEWED as the preferred alternative. The command shall remain functional for backward compatibility. |
| REQ-WF-020 | **Effective Version Preservation.** When a non-executable document in EFFECTIVE status is checked out, the CLI shall: (1) keep the effective version (N.0) in the QMS directory (still "in force"), (2) create a new draft version (N.1) in the QMS directory, and (3) copy N.1 to user workspace. The effective version shall NOT be archived on checkout; archival occurs on approval per REQ-WF-006. |
| REQ-WF-021 | **Execution Version Tracking.** During execution of an executable document: (1) release creates version N.0 in IN_EXECUTION status; (2) first checkout creates N.1 in workspace while N.0 remains current in QMS; (3) first checkin archives N.0 and commits N.1 as current IN_EXECUTION version; (4) subsequent checkout creates N.(X+1) in workspace while N.X remains current; (5) subsequent checkin archives N.X and commits N.(X+1); (6) closure transitions to (N+1).0 POST_APPROVED then CLOSED. Archive on commit (checkin), not on checkout. |
| REQ-WF-022 | **Checkout Auto-Withdraw.** When a document in an active workflow state (IN_REVIEW, IN_APPROVAL, IN_PRE_REVIEW, IN_PRE_APPROVAL, IN_POST_REVIEW, IN_POST_APPROVAL) is checked out by the responsible user, the CLI shall first withdraw the document (per REQ-WF-018 transitions), then proceed with standard checkout behavior. The CLI shall display a message indicating the withdrawal occurred before checkout. |
| REQ-WF-023 | **Route Auto-Checkin.** When a checked-out document is routed for review or approval by the responsible user, the CLI shall first check in the document (per REQ-DOC-008), then proceed with routing. The CLI shall display a message indicating the checkin occurred before routing. If the document is checked out by a different user, routing shall be rejected. |

---

### 4.4 Metadata Architecture (REQ-META)

| REQ ID | Requirement |
|--------|-------------|
| REQ-META-001 | **Three-Tier Separation.** The CLI shall maintain strict separation between: Tier 1 (Frontmatter) for author-maintained fields only (title, revision_summary); Tier 2 (.meta/) for CLI-managed workflow state; and Tier 3 (.audit/) for immutable event history. |
| REQ-META-002 | **CLI-Exclusive Metadata Management.** The CLI shall be the sole mechanism for modifying .meta/ sidecar files. Workflow state (version, status, responsible_user, pending_assignees) shall never be stored in document frontmatter. Direct modification of .meta/ files outside the CLI constitutes a compliance violation and may result in undefined behavior. |
| REQ-META-003 | **Required Metadata Fields.** Each document's .meta/ file shall contain at minimum: doc_id, doc_type, version, status, executable (boolean), responsible_user (or null), checked_out (boolean), and pending_assignees (array). |
| REQ-META-004 | **Execution Phase Tracking.** For executable documents, the CLI shall track the execution phase (pre_release or post_release) in metadata to correctly infer pre vs. post workflow stages. |

---

### 4.5 Audit Trail (REQ-AUDIT)

| REQ ID | Requirement |
|--------|-------------|
| REQ-AUDIT-001 | **Append-Only Logging.** The CLI shall never modify or delete existing audit trail entries. All audit operations shall append new entries to the .audit/ JSONL files. |
| REQ-AUDIT-002 | **Required Event Types.** The CLI shall log the following events to the audit trail: CREATE, CHECKOUT, CHECKIN, ROUTE_REVIEW, ROUTE_APPROVAL, ASSIGN, REVIEW, APPROVE, REJECT, EFFECTIVE, RELEASE, REVERT, CLOSE, RETIRE, WITHDRAW, STATUS_CHANGE. |
| REQ-AUDIT-003 | **Event Attribution.** Each audit event shall include: timestamp (ISO 8601 format), event type, user who performed the action, and document version at time of event. |
| REQ-AUDIT-004 | **Comment Preservation.** Review comments and rejection rationale shall be stored only in the audit trail, not in document content or metadata. |

---

### 4.6 Task & Inbox Management (REQ-TASK)

| REQ ID | Requirement |
|--------|-------------|
| REQ-TASK-001 | **Task Generation on Routing.** When a document is routed for review or approval, the CLI shall create task files in each assigned user's inbox directory. |
| REQ-TASK-002 | **Task Content Requirements.** Generated task files shall include: task_id (unique identifier), task_type (REVIEW or APPROVAL), workflow_type, doc_id, version, assigned_by, and assigned_date. |
| REQ-TASK-003 | **Task Removal on Completion.** When a user completes a review or approval action, the CLI shall remove their corresponding task file from their inbox. Additionally, when a document is rejected during approval, the CLI shall remove ALL pending approval tasks for that document from ALL user inboxes. |
| REQ-TASK-004 | **Assign Command.** The CLI shall provide an `assign` command allowing quality group members to add reviewers or approvers to a document after initial routing. Assignment shall validate that assignees are authorized for the workflow type per REQ-SEC-007. |

---

### 4.7 Project Configuration (REQ-CFG)

| REQ ID | Requirement |
|--------|-------------|
| REQ-CFG-001 | **Project Root Discovery.** The CLI shall discover the project root by searching upward from the current working directory for: (1) `qms.config.json` file (preferred), or (2) `QMS/` directory (fallback for backward compatibility). The first match determines the project root. |
| REQ-CFG-002 | **QMS Root Path.** The CLI shall resolve the QMS document root as `{PROJECT_ROOT}/QMS/`. All controlled documents, metadata, and audit trails shall reside under this path. |
| REQ-CFG-003 | **Users Directory Path.** The CLI shall resolve the users directory (containing workspaces and inboxes) as `{PROJECT_ROOT}/.claude/users/`. |
| REQ-CFG-004 | **User Registry.** The CLI shall determine valid users from: (1) hardcoded administrators (`lead`, `claude`), and (2) agent definition files in `.claude/agents/`. Group membership is determined per REQ-USER-001 and REQ-USER-002. The CLI shall also maintain a permission registry mapping commands to: (1) authorized groups, (2) owner_only modifier (restricts to document owner), and (3) assigned_only modifier (restricts to assigned users). |
| REQ-CFG-005 | **Document Type Registry.** The CLI shall maintain a registry of document types, including for each type: (1) storage path relative to QMS root, (2) executable flag, (3) ID prefix, (4) parent type (if child document), and (5) folder-per-document flag. The CLI shall also maintain an SDLC namespace registry enabling dynamic RS and RTM document types per registered namespace. |

---

### 4.8 Query Operations (REQ-QRY)

| REQ ID | Requirement |
|--------|-------------|
| REQ-QRY-001 | **Document Reading.** The CLI shall provide the ability to read any document's content. Reading shall support: (1) the current effective version, (2) the current draft version if one exists, and (3) any archived version by version number. |
| REQ-QRY-002 | **Document Status Query.** The CLI shall provide the ability to query a document's current workflow state, including: doc_id, title, version, status, document type, executable flag, responsible_user, and checked_out status. |
| REQ-QRY-003 | **Audit History Query.** The CLI shall provide the ability to retrieve the complete audit trail for a document, displaying all recorded events in chronological order. |
| REQ-QRY-004 | **Review Comments Query.** The CLI shall provide the ability to retrieve review comments for a document, filtered by version. Comments shall be extracted from REVIEW and REJECT events in the audit trail. |
| REQ-QRY-005 | **Inbox Query.** The CLI shall provide the ability for a user to list all pending tasks in their inbox, showing task type, document ID, and assignment date. |
| REQ-QRY-006 | **Workspace Query.** The CLI shall provide the ability for a user to list all documents currently checked out to their workspace. |

---

### 4.9 Prompt Generation (REQ-PROMPT)

| REQ ID | Requirement |
|--------|-------------|
| REQ-PROMPT-001 | **Task Prompt Generation.** When creating task files for review or approval, the CLI shall generate structured prompt content that guides the assigned user through the task. |
| REQ-PROMPT-002 | **YAML-Based Configuration.** Prompt content shall be configurable via external YAML files stored in the `prompts/` directory. The CLI shall not require code changes to modify prompt content. |
| REQ-PROMPT-003 | **Hierarchical Prompt Lookup.** The CLI shall resolve prompt configuration using hierarchical lookup: (1) document-type and workflow-phase specific (e.g., `review/post_review/cr.yaml`), (2) workflow-phase specific (e.g., `review/post_review/default.yaml`), (3) task-type default (e.g., `review/default.yaml`). The first matching configuration shall be used. |
| REQ-PROMPT-004 | **Checklist Generation.** Review and approval prompts shall include a verification checklist. Each checklist item shall specify a category and verification item text. Items may optionally include an evidence prompt. |
| REQ-PROMPT-005 | **Prompt Content Structure.** Generated prompts shall include: (1) task header identifying the document and workflow phase, (2) verification checklist organized by category, (3) critical reminders section, and (4) response format guidance. |
| REQ-PROMPT-006 | **Custom Sections.** Prompt configurations shall support custom header text, custom footer text, additional named sections, and critical reminder lists that are included in the generated prompt. |

---

### 4.10 Document Templates (REQ-TEMPLATE)

| REQ ID | Requirement |
|--------|-------------|
| REQ-TEMPLATE-001 | **Template-Based Creation.** When creating a new document, the CLI shall populate the document with initial content from a template appropriate to the document type. |
| REQ-TEMPLATE-002 | **Template Location.** Document templates shall be stored in `QMS/TEMPLATE/` as controlled documents following the naming convention `TEMPLATE-{TYPE}.md` (e.g., `TEMPLATE-CR.md`, `TEMPLATE-SOP.md`). |
| REQ-TEMPLATE-003 | **Variable Substitution.** Templates shall support variable placeholders that the CLI substitutes at creation time. Supported patterns: `{{TITLE}}` (double braces) for user-provided title; `{TYPE}-XXX` pattern for generated document ID (e.g., `CR-XXX` becomes `CR-029`). |
| REQ-TEMPLATE-004 | **Frontmatter Initialization.** The CLI shall initialize new documents with valid YAML frontmatter containing the `title` field (from user input or default) and `revision_summary` field (set to "Initial draft"). |
| REQ-TEMPLATE-005 | **Fallback Template Generation.** When creating a document for which no template file exists, the CLI shall generate a minimal document structure containing: (1) YAML frontmatter with title and revision_summary fields, and (2) placeholder heading with document ID. |

---

### 4.11 Project Initialization (REQ-INIT)

| REQ ID | Requirement |
|--------|-------------|
| REQ-INIT-001 | **Config File Creation.** The `init` command shall create a `qms.config.json` file at the project root containing: version identifier, creation timestamp, and empty SDLC namespaces array. |
| REQ-INIT-002 | **QMS Directory Structure.** The `init` command shall create the complete QMS directory structure including: `QMS/SOP/`, `QMS/CR/`, `QMS/INV/`, `QMS/TEMPLATE/`, `QMS/.meta/`, `QMS/.audit/`, and `QMS/.archive/`. |
| REQ-INIT-003 | **User Directory Structure.** The `init` command shall create user directories for hardcoded administrators: `.claude/users/lead/workspace/`, `.claude/users/lead/inbox/`, `.claude/users/claude/workspace/`, `.claude/users/claude/inbox/`, and for the default QA user. |
| REQ-INIT-004 | **Default Agent Creation.** The `init` command shall create a default QA agent file at `.claude/agents/qa.md` with `group: quality` in frontmatter. |
| REQ-INIT-005 | **SOP Seeding.** The `init` command shall seed the `QMS/SOP/` directory with sanitized SOP documents from `qms-cli/seed/sops/`, creating corresponding `.meta/` and `.audit/` files with EFFECTIVE status at version 1.0. |
| REQ-INIT-006 | **Template Seeding.** The `init` command shall seed the `QMS/TEMPLATE/` directory with document templates from `qms-cli/seed/templates/`, creating corresponding `.meta/` and `.audit/` files with EFFECTIVE status at version 1.0. |
| REQ-INIT-007 | **Safety Checks.** The `init` command shall abort with an error if any of the following already exist at the target location: `QMS/` directory, `.claude/users/` directory, `.claude/agents/qa.md` file, or `qms.config.json` file. All checks shall be performed before any changes are made. |
| REQ-INIT-008 | **Root Flag Support.** The `init` command shall accept an optional `--root` flag to specify an alternate project root directory. If not provided, the current working directory shall be used. |

---

### 4.12 User Management (REQ-USER)

| REQ ID | Requirement |
|--------|-------------|
| REQ-USER-001 | **Hardcoded Administrators.** The users `lead` and `claude` shall be recognized as administrators without requiring agent definition files. These identities are hardcoded in the CLI. |
| REQ-USER-002 | **Agent File-Based Group Assignment.** For non-hardcoded users, the CLI shall determine group membership by reading the `group:` field from the user's agent definition file at `.claude/agents/{user}.md`. Valid group values are: administrator, initiator, quality, reviewer. |
| REQ-USER-003 | **User Add Command.** The CLI shall provide a `user --add` command that creates: (1) an agent definition file at `.claude/agents/{user}.md` with specified group, (2) workspace directory at `.claude/users/{user}/workspace/`, and (3) inbox directory at `.claude/users/{user}/inbox/`. The command shall require administrator privileges and a `--group` argument. |
| REQ-USER-004 | **Unknown User Handling.** When a command is invoked with a user identifier that is neither a hardcoded administrator nor has an agent definition file, the CLI shall reject the command with an informative error message that guides the user to create an agent file or use the `user --add` command. |
| REQ-USER-005 | **User List Command.** The CLI shall provide a `user --list` command that displays all recognized users (hardcoded administrators and users with agent definition files) along with their group assignments. |

---

### 4.13 MCP Server (REQ-MCP)

| REQ ID | Requirement |
|--------|-------------|
| REQ-MCP-001 | **MCP Protocol Implementation.** The CLI shall provide an MCP (Model Context Protocol) server that exposes QMS operations as native tools for AI agents. The server shall implement the MCP specification for tool registration and invocation. |
| REQ-MCP-002 | **User Command Tools.** The MCP server shall expose the following user query tools: `qms_inbox` (list pending tasks), `qms_workspace` (list checked-out documents), `qms_status` (get document status), `qms_read` (read document content with version/draft options), `qms_history` (view audit trail), and `qms_comments` (view review comments). |
| REQ-MCP-003 | **Document Lifecycle Tools.** The MCP server shall expose the following document lifecycle tools: `qms_create` (create new document), `qms_checkout` (check out document), `qms_checkin` (check in document with content), and `qms_cancel` (cancel never-effective document). |
| REQ-MCP-004 | **Workflow Tools.** The MCP server shall expose the following workflow tools: `qms_route` (route for review/approval with optional retire flag), `qms_assign` (add reviewers), `qms_review` (submit review with outcome and comment), `qms_approve` (approve document), `qms_reject` (reject document with comment), and `qms_withdraw` (withdraw document from review/approval workflow). |
| REQ-MCP-005 | **Execution Tools.** The MCP server shall expose the following execution tools for executable documents: `qms_release` (release for execution), `qms_revert` (revert to execution with reason), and `qms_close` (close document). |
| REQ-MCP-006 | **Administrative Tools.** The MCP server shall expose the `qms_fix` tool for administrative fixes on EFFECTIVE documents. This tool shall enforce administrator-only access. |
| REQ-MCP-007 | **Functional Equivalence.** Each MCP tool shall produce functionally equivalent results to the corresponding CLI command. The MCP interface shall delegate to the same internal functions as the CLI to ensure consistency. |
| REQ-MCP-008 | **Structured Responses.** MCP tools shall return structured responses containing: (1) success/failure status, (2) result data appropriate to the operation, and (3) error details when failures occur. Text output shall not require parsing. |
| REQ-MCP-009 | **Permission Enforcement.** MCP tools shall enforce the same permission model as the CLI (per REQ-SEC-001 through REQ-SEC-008). The resolved identity (determined per REQ-MCP-015) shall identify the calling user for authorization. |
| REQ-MCP-010 | **Setup Command Exclusion.** Administrative setup commands (`init`, `namespace`, `user`, `migrate`) shall not be exposed as MCP tools. These commands require direct CLI access. |
| REQ-MCP-011 | **Remote Transport Support.** The MCP server shall support stdio transport (available as a fallback for environments where the HTTP server is unavailable), SSE transport (deprecated, for legacy remote HTTP connections), and streamable-http transport (recommended for all connections, both local and remote). The transport mode shall be selectable at server startup. |
| REQ-MCP-012 | **Transport CLI Configuration.** The MCP server shall accept command-line arguments for transport configuration: `--transport` (stdio, sse, or streamable-http; default: stdio), `--host` (bind address, default: 127.0.0.1), and `--port` (bind port, default: 8000). Host and port arguments shall apply to remote transports (sse and streamable-http). |
| REQ-MCP-013 | **Project Root Configuration.** The MCP server shall support explicit project root configuration via: (1) `--project-root` command-line argument, or (2) `QMS_PROJECT_ROOT` environment variable. When specified, the server shall use the configured path instead of auto-discovery. The CLI argument shall take precedence over the environment variable. |
| REQ-MCP-014 | **Streamable-HTTP Transport.** When configured for streamable-http transport, the MCP server shall: (1) bind to the specified host and port, (2) expose the MCP endpoint at `/mcp`, (3) allow connections from `host.docker.internal` for Docker container access, and (4) support the standard MCP streamable-http protocol as the recommended transport for all connections. |
| REQ-MCP-015 | **Header-Based Identity Resolution.** The MCP server shall resolve caller identity based on the presence of the `X-QMS-Identity` HTTP request header. All MCP tools SHALL require a `user` parameter with no default value; calls omitting the parameter or providing an empty value SHALL be rejected with a helpful error. When the header is present (enforced mode): the `user` parameter SHALL match the header value; a mismatch SHALL return an error identifying the caller's authenticated identity and instructing them to use it, with a warning that impersonation is a QMS violation. When the header is absent (trusted mode): identity shall be read from the `user` tool parameter. The `resolve_identity` function SHALL NOT silently fall back when request context is unavailable; non-HTTP contexts (e.g., stdio) SHALL be handled as an explicit trusted-mode path. All MCP tools shall accept a `ctx: Context` parameter for request context access. |
| REQ-MCP-016 | **Identity Collision Prevention.** The MCP server shall prevent identity collisions between concurrent callers. When an identity is active in enforced mode (request with `X-QMS-Identity` header), the server shall: (1) reject trusted-mode requests (no `X-QMS-Identity` header) attempting to use the same identity with a terminal error message, (2) reject enforced-mode requests from a different container instance claiming the same identity (using `X-QMS-Instance` header for disambiguation), and (3) maintain identity locks with TTL-based expiry for crash recovery. The proxy shall inject a unique instance identifier (`X-QMS-Instance` header) per proxy lifecycle for duplicate container detection. Error messages shall be unambiguous and instruct the caller not to attempt troubleshooting. |

---

### 4.14 Interaction System (REQ-INT)

The interaction system provides template-driven interactive authoring for VR documents. Instead of freehand markdown editing, interactive templates define a state machine of prompts; the engine presents prompts in sequence, records responses with per-entry attribution, and compiles source data into markdown.

#### 4.14.1 Template Parser

| REQ ID | Requirement |
|--------|-------------|
| REQ-INT-001 | **Tag Vocabulary.** The system shall recognize `@prompt`, `@gate`, `@loop`, `@end-loop`, and `@end` tags in HTML comment syntax (`<!-- @tag -->`) within templates. |
| REQ-INT-002 | **Template Header.** The system shall parse `@template` header tags specifying template name, version, and start prompt. |
| REQ-INT-003 | **Prompt Attributes.** `@prompt` tags shall support `id`, `next`, and `commit` attributes. |
| REQ-INT-004 | **Gate Attributes.** `@gate` tags shall support `id`, `type`, `yes`, and `no` attributes; `type: yesno` gates accept yes/no decisions. |
| REQ-INT-005 | **Loop Semantics.** `@loop`/`@end-loop` pairs shall define repeating blocks with an iteration counter (`{{_n}}`); loops close via gate decision. |

#### 4.14.2 Source Data Model

| REQ ID | Requirement |
|--------|-------------|
| REQ-INT-006 | **Source File Structure.** Interactive documents shall produce `.source.json` files containing doc_id, template reference, cursor state, responses, loop state, gate decisions, and metadata. |
| REQ-INT-007 | **Session File Lifecycle.** Checkout of interactive documents shall produce `.interact` session files in the workspace; checkin moves session data to `.source.json` in `.meta/`. |
| REQ-INT-008 | **Append-Only Responses.** Each response shall be stored as a list of entries with value, author, timestamp, and optional reason and commit fields; amendments append (never replace or delete). |
| REQ-INT-009 | **Amendment Trail.** Amendments to completed prompts shall require a reason; original entries are preserved; compiled output renders superseded entries with strikethrough. |

#### 4.14.3 Interact Command

| REQ ID | Requirement |
|--------|-------------|
| REQ-INT-010 | **Interact Entry Point.** `qms interact DOC_ID` with no flags shall display document status and current prompt with guidance text. |
| REQ-INT-011 | **Response Flags.** The interact command shall support `--respond "value"` and `--respond --file path`; all prompts require an explicit response (no default values). |
| REQ-INT-012 | **Navigation Flags.** The interact command shall support `--goto prompt_id` (amend previous response), `--cancel-goto`, and `--reopen loop_name` (re-enter closed loop); `--goto` and `--reopen` require `--reason`. |
| REQ-INT-013 | **Query Flags.** The interact command shall support `--progress` (show all prompts with fill status) and `--compile` (output compiled markdown preview to stdout; does not write to workspace or QMS). |

#### 4.14.4 Engine Behavior

| REQ ID | Requirement |
|--------|-------------|
| REQ-INT-014 | **Sequential Enforcement.** The engine shall not accept responses to prompts that have not been presented; prompts must be answered in template-defined order. |
| REQ-INT-015 | **Contextual Interpolation.** Prompt guidance text may reference previous responses using `{{id}}` syntax; the engine shall substitute known values before presenting. |
| REQ-INT-016 | **Compilation.** The system shall compile source files into markdown by stripping tags and guidance, substituting placeholders with active responses, and rendering amendment trails. |

#### 4.14.5 Document Integration

| REQ ID | Requirement |
|--------|-------------|
| REQ-INT-017 | **Interactive Checkout.** Checkout of interactive documents shall initialize a `.interact` session file (not editable markdown); if a `.source.json` exists, it seeds the session. |
| REQ-INT-018 | **Interactive Checkin.** Checkin of interactive documents shall compile to markdown, store `.source.json` in `.meta/`, and remove the `.interact` session. |
| REQ-INT-019 | **Source-Aware Read.** `qms read` shall compile from `.interact` (if checked out) or `.source.json` (if checked in) when available, falling back to standard markdown for non-interactive documents. |

#### 4.14.6 Atomic Commits

| REQ ID | Requirement |
|--------|-------------|
| REQ-INT-020 | **Engine-Managed Commits.** On prompts with `commit: true`, the engine shall stage changes, commit with a system-generated message in the format `[QMS] {DOC_ID} | {context} | {prompt_id}`, and record the resulting commit hash in the response entry. |
| REQ-INT-021 | **Commit Staging Scope.** Engine-managed commits shall stage changes scoped to the project working tree. |

#### 4.14.7 MCP Parity

| REQ ID | Requirement |
|--------|-------------|
| REQ-INT-022 | **MCP Interact Tool.** The MCP server shall expose a `qms_interact` tool that is functionally equivalent to the `qms interact` CLI command, consistent with REQ-MCP-007 (functional equivalence). |

---

## 5. Environmental Assumptions, Limitations, and Exclusions

This section clarifies the boundary of the QMS CLI's responsibilities and its dependencies on external infrastructure.

### 5.1 Environmental Assumptions

The CLI assumes the following environment exists before invocation:

| Assumption | Description |
|------------|-------------|
| **Project root identifiable** | The CLI discovers the project root by searching for `qms.config.json` or `QMS/` directory. For most commands, one of these must exist. The `init` command is the exception—it creates these artifacts. |
| **Prompt YAML files exist** | The `qms-cli/prompts/` directory must contain valid YAML configuration files for prompt generation. Missing files result in fallback behavior or errors. |
| **Python environment** | Python 3.x with PyYAML installed. The CLI does not manage its own dependencies. |

### 5.2 On-Demand Directory Creation

The CLI creates the following directories automatically when first needed:

| Directory | Created When |
|-----------|--------------|
| `QMS/.meta/{TYPE}/` | First document of that type is created |
| `QMS/.audit/{TYPE}/` | First document of that type is created |
| `QMS/.archive/{TYPE}/` | First version is archived |
| `QMS/{TYPE}/` (e.g., `QMS/SOP/`) | First document of that type is created |
| `QMS/{TYPE}/{DOC_ID}/` | First folder-per-doc document (CR, INV) is created |
| `.claude/users/{user}/workspace/` | First checkout by that user |
| `.claude/users/{user}/inbox/` | First task is routed to that user |

### 5.3 Limitations

| Limitation | Description |
|------------|-------------|
| **Single-user file locking** | The CLI uses file-based checkout tracking. It does not implement OS-level file locking or support concurrent access from multiple processes. |
| **No network operations** | The CLI operates entirely on the local filesystem. It does not communicate with remote services, databases, or APIs. |
| **Hardcoded path conventions** | Directory paths (`QMS/`, `.claude/users/`) are conventions, not configurable. Projects must conform to the expected structure. |

### 5.4 Exclusions

The following are explicitly outside the CLI's scope:

| Exclusion | Rationale |
|-----------|-----------|
| **Agent behavioral directives** | While the CLI reads agent definition files for group membership (per REQ-USER-002), the behavioral directives within those files are consumed by Claude Code when spawning subagents, not by the QMS CLI. |
| **Git operations** | Version control is managed separately. The CLI does not commit, push, or interact with git repositories. |
| **User authentication (CLI)** | The CLI trusts the `--user` flag. It does not authenticate users or verify identity. The MCP server provides header-based identity resolution (per REQ-MCP-015) but does not implement cryptographic authentication. |
| **Migration tooling** | The `migrate` and `verify-migration` commands are administrative utilities for schema evolution, not core QMS functionality. They are not covered by requirements in this specification. |

---

**END OF DOCUMENT**

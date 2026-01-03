---
doc_id: SOP-001
title: Quality Management System - Document Control
version: '3.1'
status: DRAFT
document_type: SOP
executable: false
responsible_user: lead
checked_out: false
effective_version: '3.0'
supersedes: null
review_history:
- round: 1
  type: REVIEW
  date_initiated: '2026-01-02'
  assignees:
  - user: qa
    status: COMPLETE
    date: '2026-01-02'
    comments: Approved. Comprehensive coverage of QMS requirements.
  - user: lead
    status: COMPLETE
    date: '2026-01-02'
    comments: Excellent draft. Clear and comprehensive.
- round: 2
  type: REVIEW
  date_initiated: '2026-01-02'
  assignees:
  - user: qa
    status: COMPLETE
    date: '2026-01-02'
    comments: 'Review of SOP-001 v1.1 identifies the following items requiring correction
      before approval:


      1. PERMISSION INCONSISTENCY: Section 4.2 Permission Matrix shows only QA has
      ''fix'' permission, but Section 13 CLI Reference states ''QA/lead only''. These
      must align. Recommend updating Section 4.2 to show lead also has fix permission,
      or updating Section 13 to show QA only.


      2. FRONTMATTER SCHEMA MISMATCH: Section 12 schema shows ''reviewers:'' and ''approvers:''
      but actual frontmatter in this document uses ''assignees:'' for both review_history
      and approval_history. Schema must match implementation.


      3. SCHEMA MISSING TYPE FIELD: Section 12 schema shows ''type:'' only in approval_history,
      but actual implementation includes ''type: REVIEW'' in review_history entries.
      Document the type field in review_history schema.


      4. SCHEMA MISSING OUTCOME FIELD: The review workflow documents --recommend and
      --request-updates outcomes, but the frontmatter schema does not show where/how
      this outcome is recorded. Add the outcome field to the review assignee schema.


      Strengths noted: State diagrams are excellent, version numbering is clear, workflow
      documentation is thorough. After addressing these schema alignment issues, document
      will be ready for approval.'
    outcome: UPDATES_REQUIRED
- round: 3
  type: REVIEW
  date_initiated: '2026-01-02'
  assignees:
  - user: qa
    status: COMPLETE
    date: '2026-01-02'
    comments: 'All previously identified issues have been addressed:


      1. PERMISSION CONSISTENCY: Section 4.2 now shows ''lead only | Yes | -'' for
      fix command, aligning with Section 13 ''QA/lead only''. VERIFIED.


      2. FRONTMATTER SCHEMA: Section 12 now correctly uses ''assignees:'' for both
      review_history and approval_history, matching actual implementation. VERIFIED.


      3. TYPE FIELD IN REVIEW_HISTORY: Section 12 schema now includes ''type: {REVIEW|PRE_REVIEW|POST_REVIEW}''
      in review_history. VERIFIED.


      4. OUTCOME FIELD: Section 12 schema now includes ''outcome: {RECOMMEND|UPDATES_REQUIRED|null}''
      in review assignee schema. VERIFIED.


      5. DATE_INITIATED FIELD: Added to both review_history and approval_history schemas.
      VERIFIED.


      Document is comprehensive, internally consistent, and ready for approval. Recommend
      proceeding to approval stage.'
    outcome: RECOMMEND
- round: 4
  type: REVIEW
  date_initiated: '2026-01-03'
  assignees:
  - user: qa
    status: COMPLETE
    date: '2026-01-03'
    comments: 'QA Review of SOP-001 v2.1: RECOMMEND APPROVAL. All CLI examples throughout
      the document have been updated to use the required --user flag. Verified: (1)
      Section 8 Workflows - all 9 CLI examples updated; (2) Section 10 Check-Out/Check-In
      - all 4 CLI examples updated; (3) Section 13 CLI Reference - introductory sentence
      added and all 20 commands now show --user {USER} syntax; (4) Section 15 Revision
      History - v2.1 entry correctly documents the change. One observation: the assign
      command uses --user twice (once for calling user, once for target users), which
      is consistent but potentially confusing. This is a design choice and does not
      block approval. Document is internally consistent and ready for approval.'
    outcome: RECOMMEND
approval_history:
- round: 1
  type: APPROVAL
  date_initiated: '2026-01-02'
  assignees:
  - user: qa
    status: APPROVED
    date: '2026-01-02'
    comments: null
  - user: lead
    status: APPROVED
    date: '2026-01-02'
    comments: null
- round: 2
  type: APPROVAL
  date_initiated: '2026-01-02'
  assignees:
  - user: qa
    status: APPROVED
    date: '2026-01-02'
    comments: null
- round: 3
  type: APPROVAL
  date_initiated: '2026-01-03'
  assignees:
  - user: qa
    status: APPROVED
    date: '2026-01-03'
    comments: null
checked_out_date: null
---

# SOP-001: Quality Management System - Document Control

**Version:** 2.1
**Effective Date:** TBD
**Responsible User:** lead

---

## 1. Purpose

This Standard Operating Procedure (SOP) establishes the document control system for the Flow State project. It defines the structure, workflows, and requirements for creating, reviewing, approving, and maintaining controlled documents within the Quality Management System (QMS).

---

## 2. Scope

This SOP applies to all controlled documents within the Flow State QMS, including:

- Standard Operating Procedures (SOP)
- Change Records (CR)
- Investigations (INV)
- Corrective and Preventive Actions (CAPA)
- Test Protocols (TP)
- Exception Reports (ER)
- System Development Lifecycle Documents (RS, DS, CS, RTM, OQ)

This SOP applies to all authorized users of the QMS, including human users and AI agents.

---

## 3. Definitions

| Term | Definition |
|------|------------|
| **QMS** | Quality Management System - the document control infrastructure |
| **Controlled Document** | Any document managed under this SOP |
| **Responsible User** | The user who has checked out a document and owns its workflow |
| **Effective Version** | The approved version currently in force |
| **Draft** | A version under development, not yet approved |
| **Executable Document** | A document that authorizes implementation activities (CR, INV, CAPA, TP, ER) |
| **Non-Executable Document** | A document that defines requirements or specifications (RS, DS, CS, RTM, SOP, OQ) |

---

## 4. User Groups & Permissions

### 4.1 User Groups

| Group | Members | Role |
|-------|---------|------|
| **Initiators** | lead, claude | Create and manage documents through workflow |
| **QA** | qa | Mandatory reviewer/approver; assigns Technical Units |
| **Reviewers** | tu_input, tu_ui, tu_scene, tu_sketch, tu_sim, bu | Domain experts assigned by QA |

### 4.2 Permission Matrix

| Action | Initiators | QA | Reviewers |
|--------|------------|-----|-----------|
| create, checkout, checkin | Yes | - | - |
| route, release, close | Yes | - | - |
| assign | - | Yes | - |
| review | When assigned | Yes | When assigned |
| approve, reject | - | Yes | When assigned |
| fix (admin) | lead only | Yes | - |

### 4.3 Responsibilities

**Initiators** shall:
- Create and maintain documents in their workspace
- Route documents for review and approval
- Address reviewer comments before re-routing

**QA** shall:
- Be automatically assigned to all routed documents
- Assign Technical Units (TUs) based on affected domains
- Verify procedural compliance before approval

**Reviewers** shall:
- Review assigned documents for technical accuracy
- Submit review with `--recommend` or `--request-updates` outcome
- Complete reviews in a timely manner

---

## 5. QMS Structure

### 5.1 Directory Layout

```
pipe-dream/
├── .claude/users/                    # User workspaces and inboxes
│   ├── lead/
│   │   ├── workspace/
│   │   └── inbox/
│   ├── claude/
│   │   ├── workspace/
│   │   └── inbox/
│   ├── qa/
│   ├── bu/
│   ├── tu_input/
│   ├── tu_ui/
│   ├── tu_scene/
│   ├── tu_sketch/
│   └── tu_sim/
│
└── QMS/
    ├── .archive/                     # Historical versions
    │   ├── SOP/
    │   ├── CR/
    │   ├── INV/
    │   └── SDLC-FLOW/
    ├── SOP/                          # Standard Operating Procedures
    ├── CR/                           # Change Records
    ├── INV/                          # Investigations
    └── SDLC-FLOW/                    # System Lifecycle Documents
```

### 5.2 Document Naming Convention

| Document Type | Format | Example |
|---------------|--------|---------|
| Standard Operating Procedure | SOP-NNN | SOP-001 |
| Change Record | CR-NNN | CR-005 |
| Investigation | INV-NNN | INV-001 |
| CAPA (child of INV) | INV-NNN-CAPA-NNN | INV-001-CAPA-002 |
| Test Protocol (child of CR) | CR-NNN-TP | CR-005-TP |
| Exception Report (child of TP) | CR-NNN-TP-ER-NNN | CR-005-TP-ER-001 |
| Requirements Specification | SDLC-FLOW-RS | SDLC-FLOW-RS |
| Design Specification | SDLC-FLOW-DS | SDLC-FLOW-DS |
| Configuration Specification | SDLC-FLOW-CS | SDLC-FLOW-CS |
| Requirements Traceability Matrix | SDLC-FLOW-RTM | SDLC-FLOW-RTM |
| Operational Qualification | SDLC-FLOW-OQ | SDLC-FLOW-OQ |

### 5.3 File Naming

| State | Filename |
|-------|----------|
| Effective version | `{DOC_ID}.md` |
| Draft version | `{DOC_ID}-draft.md` |
| Archived version | `{DOC_ID}-v{N.X}.md` |

**Examples:**
- `SOP-001.md` — Effective version of SOP-001
- `SOP-001-draft.md` — Draft version being revised
- `.archive/SOP/SOP-001-v1.0.md` — Archived version 1.0

---

## 6. Version Control

### 6.1 Version Numbering

Versions follow the format `N.X` where:

- **N** = Approval number (major version)
- **X** = Revision number within approval cycle (minor version)

| Version | Meaning |
|---------|---------|
| v0.1 | Initial draft (never approved) |
| v0.2, v0.3... | Revisions during initial review cycle |
| v1.0 | First approval |
| v1.1, v1.2... | Revisions after re-opening v1.0 |
| v2.0 | Second approval |
| vN.0 | Nth approval |
| vN.X | Xth revision toward approval N+1 |

### 6.2 Version Transitions

| Action | Version Change |
|--------|----------------|
| Create new document | → v0.1 |
| Revise during review | v0.X → v0.(X+1) |
| First approval | v0.X → v1.0 |
| Re-open effective document | vN.0 → vN.1 |
| Subsequent approval | vN.X → v(N+1).0 |

### 6.3 Archive Management

When a document version is superseded:

1. The previous version is copied to `.archive/{TYPE}/`
2. The archive copy is renamed to include the version: `{DOC_ID}-v{N.X}.md`
3. The working directory retains only the current effective and/or draft versions

---

## 7. Document Status

### 7.1 Non-Executable Documents (SOP, RS, DS, CS, RTM, OQ)

| Status | Description |
|--------|-------------|
| DRAFT | Document is being created or revised |
| IN_REVIEW | Document is routed for review |
| REVIEWED | All assigned reviews are complete |
| IN_APPROVAL | Document is routed for approval |
| APPROVED | All assigned approvals are complete |
| EFFECTIVE | Document is approved and in force |
| SUPERSEDED | Document has been replaced by a newer version |

### 7.2 Executable Documents (CR, INV, CAPA, TP, ER)

| Status | Description |
|--------|-------------|
| DRAFT | Document is being created or revised |
| IN_PRE_REVIEW | Document is routed for pre-execution review |
| PRE_REVIEWED | All pre-reviews are complete |
| IN_PRE_APPROVAL | Document is routed for pre-execution approval |
| PRE_APPROVED | Document is approved for execution |
| IN_EXECUTION | Implementation/execution is in progress |
| IN_POST_REVIEW | Document is routed for post-execution review |
| POST_REVIEWED | All post-reviews are complete |
| IN_POST_APPROVAL | Document is routed for post-execution approval |
| POST_APPROVED | Execution verified and approved |
| CLOSED | Document is complete and closed |

---

## 8. Workflows

### 8.1 Review Workflow

Reviews must precede all approvals. Multiple review rounds are permitted.

**Initiating Review:**
```
qms --user {USER} route {DOC_ID} --review
qms --user {USER} route {DOC_ID} --pre-review     # Executable docs
qms --user {USER} route {DOC_ID} --post-review    # After execution
```

QA is automatically assigned when a document is routed. QA then assigns Technical Units as needed:
```
qms --user qa assign {DOC_ID} --assignees tu_ui tu_scene   # QA assigns additional reviewers
```

**Completing Review:**
```
qms --user {USER} review {DOC_ID} --recommend --comment "Looks good"
qms --user {USER} review {DOC_ID} --request-updates --comment "Changes needed"
```

Review outcomes:
- `--recommend`: Reviewer approves proceeding to approval stage
- `--request-updates`: Reviewer requires changes before approval

**Automatic Transition:** When all assigned reviewers complete their reviews, status transitions automatically:
- IN_REVIEW → REVIEWED
- IN_PRE_REVIEW → PRE_REVIEWED
- IN_POST_REVIEW → POST_REVIEWED

### 8.2 Approval Workflow

Approvals may only be initiated after review is complete AND all reviewers have `--recommend` outcome.

**Approval Gate:** The system blocks approval routing if any reviewer submitted `--request-updates`. The initiator must address the requested changes and route for another review round.

**Initiating Approval:**
```
qms --user {USER} route {DOC_ID} --approval
qms --user {USER} route {DOC_ID} --pre-approval    # Executable docs
qms --user {USER} route {DOC_ID} --post-approval   # After execution
```

The same Review Team (QA + assigned TUs) remains assigned for approval.

**Approving:**
```
qms --user {USER} approve {DOC_ID}
```

**Rejecting:**
```
qms --user {USER} reject {DOC_ID} --comment "Rejection rationale"
```

**Automatic Transitions:**
- All approvals complete: IN_APPROVAL → APPROVED, IN_PRE_APPROVAL → PRE_APPROVED, etc.
- Any rejection: Returns to previous REVIEWED state for revision

### 8.3 Rejection Handling

When any approver rejects a document:

| From Status | Transitions To | Required Action |
|-------------|----------------|-----------------|
| IN_APPROVAL | REVIEWED | Revise, then re-route for review |
| IN_PRE_APPROVAL | PRE_REVIEWED | Revise, then re-route for pre-review |
| IN_POST_APPROVAL | POST_REVIEWED | Revise, then re-route for post-review |

The Responsible User must:
1. Address rejection comments
2. Check in the revised document
3. Route for another review cycle before re-routing for approval

### 8.4 Release Workflow (Executable Documents Only)

After pre-approval, executable documents must be manually released:

```
qms --user {USER} release {DOC_ID}
```

This transitions the document from PRE_APPROVED to IN_EXECUTION.

### 8.5 Revert Workflow (Executable Documents Only)

If problems are discovered after post-review, the document may revert to execution:

```
qms --user {USER} revert {DOC_ID} --reason "Reason for revert"
```

This transitions from POST_REVIEWED back to IN_EXECUTION.

### 8.6 Close Workflow (Executable Documents Only)

After post-approval, executable documents must be manually closed:

```
qms --user {USER} close {DOC_ID}
```

---

## 9. State Machine Diagrams

### 9.1 Non-Executable Documents

```
DRAFT
  │
  ▼ (qms route --review)
IN_REVIEW ◄─────────────────────┐
  │                             │
  ▼ (all reviews complete)      │ (another round)
REVIEWED ───────────────────────┘
  │
  ▼ (qms route --approval)
IN_APPROVAL
  │
  ├──► (all approve) ──► APPROVED ──► EFFECTIVE
  │
  └──► (any reject) ──► REVIEWED ──► [revise, re-review]
```

### 9.2 Executable Documents

```
DRAFT
  │
  ▼ (qms route --pre-review)
IN_PRE_REVIEW ◄─────────────────┐
  │                             │
  ▼ (all reviews complete)      │ (another round)
PRE_REVIEWED ───────────────────┘
  │
  ▼ (qms route --pre-approval)
IN_PRE_APPROVAL
  │
  ├──► (all approve) ──► PRE_APPROVED
  │                           │
  │                           ▼ (qms release)
  │                      IN_EXECUTION ◄─────────────────┐
  │                           │                         │
  │                           ▼ (qms route --post-review)
  │                      IN_POST_REVIEW ◄───────────┐   │
  │                           │                     │   │
  │                           ▼ (all reviews)       │   │
  │                      POST_REVIEWED ─────────────┘   │
  │                           │        (another round)  │
  │                           │                         │
  │                           ├──► (qms revert) ────────┘
  │                           │
  │                           ▼ (qms route --post-approval)
  │                      IN_POST_APPROVAL
  │                           │
  │                           ├──► (all approve) ──► POST_APPROVED ──► CLOSED
  │                           │
  │                           └──► (any reject) ──► POST_REVIEWED
  │
  └──► (any reject) ──► PRE_REVIEWED ──► [revise, re-review]
```

---

## 10. Check-Out / Check-In

### 10.1 Check-Out

To edit a document, a user must check it out:

```
qms --user {USER} checkout {DOC_ID}
```

Effects:
1. If an effective version exists, creates a new draft at version N.1
2. Document is copied to user's workspace
3. User becomes Responsible User
4. Document is locked; other users cannot edit

### 10.2 Check-In

To save changes back to the QMS:

```
qms --user {USER} checkin {DOC_ID}
```

Effects:
1. Document is copied from workspace to QMS working directory
2. Previous draft version (if any) is archived
3. Document remains checked out to user

### 10.3 Reading Documents

Any user may read documents without checking out:

```
qms --user {USER} read {DOC_ID}                    # Latest effective version
qms --user {USER} read {DOC_ID} --draft            # Current draft
qms --user {USER} read {DOC_ID} --version N.X      # Specific archived version
```

---

## 11. User Workspaces and Inboxes

### 11.1 Workspace

Each user has a workspace at `.claude/users/{username}/workspace/`

- Contains documents checked out by that user
- Only the workspace owner may edit documents within
- Documents must be checked in to be visible to others

### 11.2 Inbox

Each user has an inbox at `.claude/users/{username}/inbox/`

- Contains task files for assigned reviews and approvals
- Tasks are automatically created when documents are routed
- Tasks are removed when the user completes the action

**Task File Format:**
```yaml
---
task_id: task_001
task_type: REVIEW  # or APPROVAL
doc_id: CR-005
assigned_by: claude
assigned_date: 2026-01-02
due_date: null
---

Please review CR-005 for technical accuracy.
```

---

## 12. Frontmatter Schema

All controlled documents must include YAML frontmatter:

```yaml
---
doc_id: {DOC_ID}
title: {Document Title}
version: {N.X}
status: {STATUS}
document_type: {SOP|CR|INV|CAPA|TP|ER|RS|DS|CS|RTM|OQ}
executable: {true|false}

responsible_user: {username}
checked_out: {true|false}
checked_out_date: {YYYY-MM-DD|null}

effective_version: {N.X|null}
supersedes: {DOC_ID vN.X|null}

review_history:
  - round: 1
    type: {REVIEW|PRE_REVIEW|POST_REVIEW}
    date_initiated: {YYYY-MM-DD}
    assignees:
      - user: {username}
        status: {PENDING|COMPLETE}
        date: {YYYY-MM-DD|null}
        comments: "{comments}"
        outcome: {RECOMMEND|UPDATES_REQUIRED|null}

approval_history:
  - round: 1
    type: {APPROVAL|PRE_APPROVAL|POST_APPROVAL}
    date_initiated: {YYYY-MM-DD}
    assignees:
      - user: {username}
        status: {PENDING|APPROVED|REJECTED}
        date: {YYYY-MM-DD|null}
        comments: "{comments}"
---
```

---

## 13. CLI Command Reference

All commands require the `--user` flag to identify the calling user.

| Command | Description |
|---------|-------------|
| `qms --user {USER} create {TYPE}` | Create a new document of specified type |
| `qms --user {USER} read {DOC_ID} [--draft] [--version N.X]` | Read a document |
| `qms --user {USER} checkout {DOC_ID}` | Check out document for editing |
| `qms --user {USER} checkin {DOC_ID}` | Check in document from workspace |
| `qms --user {USER} route {DOC_ID} --review` | Route for review (QA auto-assigned) |
| `qms --user {USER} route {DOC_ID} --pre-review` | Route for pre-review (executable docs) |
| `qms --user {USER} route {DOC_ID} --post-review` | Route for post-review (executable docs) |
| `qms --user {USER} route {DOC_ID} --approval` | Route for approval |
| `qms --user {USER} route {DOC_ID} --pre-approval` | Route for pre-approval (executable docs) |
| `qms --user {USER} route {DOC_ID} --post-approval` | Route for post-approval (executable docs) |
| `qms --user qa assign {DOC_ID} --assignees {users}` | Add reviewers to active workflow (QA only) |
| `qms --user {USER} review {DOC_ID} --recommend --comment "{text}"` | Submit review recommending approval |
| `qms --user {USER} review {DOC_ID} --request-updates --comment "{text}"` | Submit review requesting changes |
| `qms --user {USER} approve {DOC_ID}` | Approve document |
| `qms --user {USER} reject {DOC_ID} --comment "{text}"` | Reject document |
| `qms --user {USER} release {DOC_ID}` | Release for execution (executable only) |
| `qms --user {USER} revert {DOC_ID} --reason "{text}"` | Revert to execution (executable only) |
| `qms --user {USER} close {DOC_ID}` | Close document (executable only) |
| `qms --user {USER} status {DOC_ID}` | Show document status and workflow state |
| `qms --user {USER} inbox` | List tasks in current user's inbox |
| `qms --user {USER} workspace` | List documents in current user's workspace |
| `qms --user {USER} fix {DOC_ID}` | Administrative fix for EFFECTIVE docs (QA/lead only) |

---

## 14. References

- INV-2026-001: CR-2026-004 GMP Failure Investigation (historical context)

---

## 15. Revision History

| Version | Date | Author | Description |
|---------|------|--------|-------------|
| 1.0 | 2026-01-02 | claude | Initial release |
| 1.1 | 2026-01-02 | claude | Add user groups, permissions, review outcomes, qms assign/fix commands |
| 2.1 | 2026-01-03 | lead | Replace QMS_USER env var with required --user CLI flag |
| 3.1 | 2026-01-03 | lead | Rename assign --user to --assignees to avoid confusion |

---

**END OF DOCUMENT**

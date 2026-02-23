---
title: Quality Management System - Document Control
revision_summary: 'CR-089: Add VR (Verification Record) document type to Sections
  2, 3, 6.1, 8.2'
---

# SOP-001: Quality Management System - Document Control

---

## 1. Purpose

This Standard Operating Procedure (SOP) establishes the document control system for the Flow State project. It defines the structure, workflows, and requirements for creating, reviewing, approving, and maintaining controlled documents within the Quality Management System (QMS).

---

## 2. Scope

This SOP applies to all controlled documents within the Flow State QMS, including:

- Standard Operating Procedures (SOP)
- Change Records (CR)
- Investigations (INV)
- Test Protocols (TP)
- Exception Reports (ER)
- Variance Reports (VAR)
- Addendum Reports (ADD)
- Verification Records (VR)
- System Development Lifecycle Documents (RS, RTM)

This SOP applies to all authorized users of the QMS, including human users and AI agents.

---

## 3. Definitions

See [QMS-Glossary](QMS-Glossary.md) for all terms and abbreviations used in this document.

---

## 4. User Groups & Permissions

### 4.1 User Groups

| Group | Role |
|-------|------|
| **Administrator** | All Initiator permissions plus administrative commands (fix). |
| **Initiator** | Create and manage documents through workflow. |
| **Quality** | Assign reviewers; review and approve documents. |
| **Reviewer** | Review and approve assigned documents. |

### 4.2 Permission Matrix

| Action | Administrator | Initiator | Quality | Reviewer |
|--------|---------------|-----------|---------|----------|
| create, checkout, checkin | Yes | Yes | - | - |
| route, release, revert, close | Yes | Yes | - | - |
| assign | - | - | Yes | - |
| review | When assigned | When assigned | When assigned | When assigned |
| approve, reject | - | - | When assigned | When assigned |
| fix | Yes | - | - | - |

### 4.3 Responsibilities

**Administrator** shall:
- Perform all Initiator responsibilities
- Execute administrative commands (fix) when required

**Initiator** shall:
- Create and maintain documents in their workspace
- Route documents for review and approval
- Address reviewer comments before re-routing

**Quality** shall:
- Be automatically assigned to all routed documents
- Assign Reviewers based on affected domains
- Verify procedural compliance before approval

**Reviewer** shall:
- Review assigned documents for technical accuracy
- Submit review with recommend or request-updates outcome
- Complete reviews in a timely manner

---

## 5. Metadata Architecture

The QMS uses a three-tier architecture to separate concerns:

| Tier | Location | Managed By | Purpose |
|------|----------|------------|---------|
| 1 | Document frontmatter | Author | Title, revision summary |
| 2 | `.meta/` sidecar files | CLI | Version, status, responsible user, workflow state |
| 3 | `.audit/` JSONL files | CLI | Append-only event history |

### 5.1 Document Frontmatter (Author-Maintained)

Documents contain minimal YAML frontmatter with only author-maintained fields:

```yaml
---
title: Document Title
revision_summary: "CR-XXX: Brief description of what changed in this revision"
---
```

- **title**: Set at document creation, rarely changes
- **revision_summary**: Updated each revision cycle to describe changes. Should reference the authorizing CR ID when the revision is driven by a CR (e.g., `CR-004: Add traceability requirement`). Exceptions where CR ID is not required:
  - Initial document creation (v0.1)
  - Executable documents (CRs, INVs, etc.) which are self-authorizing
  - Revisions not driven by a specific CR

### 5.2 Document Content Standards

Documents shall contain content only. The following metadata elements shall NOT be manually inserted into document bodies:

- Version numbers
- Effective dates
- Responsible user identifiers
- Revision history tables

All such metadata is managed by the QMS CLI and available through status and history commands.

**Rationale:** Manually-maintained metadata creates opportunities for inconsistency between document content and authoritative sidecar files. The three-tier architecture ensures a single source of truth for all workflow metadata.

---

## 6. Document Naming

| Document Type | Format | Example |
|---------------|--------|---------|
| Standard Operating Procedure | SOP-NNN | SOP-001 |
| Change Record | CR-NNN | CR-005 |
| Investigation | INV-NNN | INV-001 |
| Test Protocol (child of CR) | CR-NNN-TP | CR-005-TP |
| Exception Report (child of TP) | {PARENT}-ER-NNN | CR-005-TP-ER-001 |
| Variance Report (child of CR/INV) | {PARENT}-VAR-NNN | CR-014-VAR-001 |
| Addendum Report (child of CR/INV/VAR/ADD) | {PARENT}-ADD-NNN | CR-014-ADD-001 |
| Verification Record (child of CR/VAR/ADD) | {PARENT}-VR-NNN | CR-089-VR-001 |
| Template | TEMPLATE-{NAME} | TEMPLATE-CR |
| Requirements Specification | SDLC-{NS}-RS | SDLC-QMS-RS |
| Requirements Traceability Matrix | SDLC-{NS}-RTM | SDLC-QMS-RTM |

Draft, effective, and archived versions are distinguished by filename suffix (e.g., `-draft.md`, `-v{N.X}.md`).

---

## 7. Version Control

Versions follow the format `N.X` where:

- **N** = Approval number (major version)
- **X** = Revision number within approval cycle (minor version)

| Version | Meaning |
|---------|---------|
| v0.1 | Initial draft (never approved) |
| v1.0 | First approval |
| vN.0 | Nth approval (effective version) |
| vN.X | Xth revision toward approval N+1 |

---

## 8. Document Status

### 8.1 Non-Executable Documents (SOP, RS, RTM)

| Status | Description |
|--------|-------------|
| DRAFT | Document is being created or revised |
| IN_REVIEW | Document is routed for review |
| REVIEWED | All assigned reviews are complete |
| IN_APPROVAL | Document is routed for approval |
| APPROVED | All assigned approvals are complete |
| EFFECTIVE | Document is approved and in force |
| RETIRED | Document has been permanently retired |

### 8.2 Executable Documents (CR, INV, TP, ER, VAR, ADD, VR)

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
| RETIRED | Document has been permanently retired |

### 8.3 Terminal States

| Status | Applies To | Description |
|--------|------------|-------------|
| CLOSED | Executable | Execution complete, no further action |
| RETIRED | All | Permanently archived, no longer in use |

---

## 9. Workflow Policy

### 9.1 Review

- Reviews must precede all approvals.
- QA is automatically assigned to all routed documents.
- QA assigns additional Technical Unit reviewers based on affected domains.
- Review outcomes are **recommend** (proceed to approval) or **request-updates** (changes required).
- When all assigned reviewers complete, the document transitions automatically to a reviewed state.

### 9.2 Approval

- Approval may only be initiated after all reviewers have recommended.
- At least one quality-group reviewer must have participated (approval gate).
- If any approver rejects, the document returns to its previous reviewed state. The responsible user must address rejection comments and route for another review cycle before re-attempting approval.

### 9.3 Release, Revert, and Close (Executable Documents)

- **Release:** After pre-approval, executable documents must be explicitly released to begin execution.
- **Revert:** If problems are discovered after post-review, the document may be reverted to execution with a stated reason.
- **Close:** After post-approval, executable documents must be explicitly closed. Closure is a terminal state.

### 9.4 Cancel and Retire

- **Cancel:** Documents that have never been approved (version < 1.0) may be permanently deleted. The document must not be checked out.
- **Retire:** Documents that have been effective (version >= 1.0) cannot be deleted. They must go through a formal retirement approval process, which archives the document and transitions it to the RETIRED terminal state.

---

## 10. State Machine Diagrams

### 10.1 Non-Executable Documents

```
DRAFT (v < 1.0)
  │
  ├──► (cancel) ──► [DELETED]
  │
  ▼ (route for review)
IN_REVIEW ◄─────────────────────┐
  │                             │
  ▼ (all reviews complete)      │ (another round)
REVIEWED ───────────────────────┘
  │
  ▼ (route for approval)
IN_APPROVAL
  │
  ├──► (all approve) ──► APPROVED ──► EFFECTIVE ──► (retire) ──► RETIRED
  │
  └──► (any reject) ──► REVIEWED ──► [revise, re-review]
```

### 10.2 Executable Documents

```
DRAFT (v < 1.0)
  │
  ├──► (cancel) ──► [DELETED]
  │
  ▼ (route for review)
IN_PRE_REVIEW ◄─────────────────┐
  │                             │
  ▼ (all reviews complete)      │ (another round)
PRE_REVIEWED ───────────────────┘
  │
  ▼ (route for approval)
IN_PRE_APPROVAL
  │
  ├──► (all approve) ──► PRE_APPROVED
  │                           │
  │                           ▼ (release)
  │                      IN_EXECUTION ◄─────────────────┐
  │                           │                         │
  │                           ▼ (route for review)      │
  │                      IN_POST_REVIEW ◄───────────┐   │
  │                           │                     │   │
  │                           ▼ (all reviews)       │   │
  │                      POST_REVIEWED ─────────────┘   │
  │                           │        (another round)  │
  │                           │                         │
  │                           ├──► (revert) ────────────┘
  │                           │
  │                           ▼ (route for approval)
  │                      IN_POST_APPROVAL
  │                           │
  │                           ├──► (all approve) ──► POST_APPROVED ──► CLOSED
  │                           │                                          │
  │                           │                          (retire) ──────┴──► RETIRED
  │                           │
  │                           └──► (any reject) ──► POST_REVIEWED
  │
  └──► (any reject) ──► PRE_REVIEWED ──► [revise, re-review]
```

---

## 11. References

- INV-2026-001: CR-2026-004 GMP Failure Investigation (historical context)

---

**END OF DOCUMENT**

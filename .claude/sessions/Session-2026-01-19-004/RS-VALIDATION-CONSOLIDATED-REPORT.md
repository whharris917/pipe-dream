# SDLC-QMS-RS Validation Report

**Date:** 2026-01-19
**Validation Method:** Multi-agent parallel review (6 domain agents + auditor)
**Document Under Review:** SDLC-QMS-RS (QMS CLI Requirements Specification)
**Total Requirements:** 64

---

## 1. Executive Summary

A comprehensive validation of the SDLC-QMS-RS was performed using 6 specialized domain review agents examining code-to-requirement alignment across Security, Document Management, Workflow, Metadata/Audit, Task/Config, and Query/Prompt/Template domains.

### Overall Scores

| Metric | Count | Percentage |
|--------|-------|------------|
| Accurate | 42 | 65.6% |
| Accurate with Issues | 15 | 23.4% |
| Inaccurate | 7 | 10.9% |
| Complete | 43 | 67.2% |
| Sufficient for Rebuild | 46 | 71.9% |

### Key Findings

1. **7 requirements** contain inaccurate statements that do not match implementation
2. **2 requirements** describe behavior that is NOT implemented in code (implementation gaps)
3. **8 critical features** in code have no corresponding requirements
4. **15 requirements** need revision for completeness or edge case coverage
5. **Best domain:** Metadata/Audit (100% accurate)
6. **Worst domain:** Document Management (25% fully accurate)

---

## 2. Validation Methodology

### 2.1 Agent Assignments

| Agent | Domain | REQs Reviewed | Code Files Examined |
|-------|--------|---------------|---------------------|
| A1-SEC | Security | 6 | qms_auth.py, qms_config.py |
| A2-DOC | Document Management | 12 | create.py, checkout.py, checkin.py, cancel.py, qms_paths.py, qms_config.py |
| A3-WF | Workflow State Machine | 13 | workflow.py, qms_config.py, route.py, approve.py, reject.py, release.py, revert.py, close.py |
| A4-META | Metadata & Audit Trail | 8 | qms_meta.py, qms_audit.py |
| A5-TASK | Task & Configuration | 9 | inbox.py, workspace.py, qms_paths.py, qms_config.py |
| A6-QUERY | Query, Prompt, Template | 16 | prompts.py, prompts/*.yaml, qms_templates.py, read.py, status.py, history.py, comments.py |

### 2.2 Evaluation Criteria

Each requirement was assessed on three dimensions:
- **Accuracy**: Does the requirement match actual code behavior?
- **Completeness**: Does the requirement capture all relevant behavior?
- **Rebuildability**: Could a developer rebuild from the requirement alone?

---

## 3. Inaccurate Requirements (Must Fix)

These 7 requirements contain statements that contradict the actual implementation.

### 3.1 REQ-SEC-002: Group-Based Action Authorization

**Current Text:**
> The CLI shall authorize actions based on user group membership: create, checkout, checkin, route, release, revert, close (Initiators); assign (QA); fix (QA, lead).

**Issues:**
1. `route` is permitted for both Initiators AND QA (per CR-032 implementation)
2. `fix` command uses hardcoded user-level checking (`qa` and `lead` users), not group-based authorization

**Evidence:** qms_auth.py:52-65, qms_config.py PERMISSIONS dict

**Recommended Fix:**
> The CLI shall authorize actions based on user group membership: create, checkout, checkin, release, revert, close (Initiators); route (Initiators, QA); assign (QA); fix (qa user, lead user).

---

### 3.2 REQ-DOC-001: Supported Document Types

**Current Text:**
> The CLI shall support creation and management of the following document types: SOP, CR, INV, TP, ER, VAR, RS, RTM, and TEMPLATE.

**Issue:** Lists 9 types but code supports 16 types. Missing: CAPA, DS, CS, OQ, QMS-RS, QMS-RTM, plus configured SDLC namespace variants.

**Evidence:** qms_config.py DOCUMENT_TYPES dict (lines 75-95)

**Recommended Fix:**
> The CLI shall support creation and management of the following document types:
> - **Core types:** SOP, CR, INV, TP, ER, VAR, CAPA, TEMPLATE
> - **SDLC types:** RS, RTM (with namespace prefixes, e.g., SDLC-FLOW-RS, SDLC-QMS-RTM)
> - **SDLC singleton types:** DS, CS, OQ (for configured namespaces)

---

### 3.3 REQ-DOC-008: Checkin Updates QMS

**Current Text:**
> When a user checks in a document, the CLI shall: (1) copy the document from workspace to QMS working directory, (2) archive any previous draft version, and (3) maintain the user as responsible_user.

**Issue:** Statement (2) is incorrect. Drafts are NOT archived on checkin. Archiving only occurs:
- On checkout of an EFFECTIVE document (before creating new draft)
- On approval (before version bump)
- On retirement

**Evidence:** checkin.py (no archive call), checkout.py:87-90 (archive on effective checkout)

**Recommended Fix:**
> When a user checks in a document, the CLI shall: (1) copy the document from workspace to QMS working directory, (2) remove the workspace copy, and (3) maintain the user as responsible_user.

---

### 3.4 REQ-DOC-012: SDLC Document Types

**Current Text:**
> The CLI shall support RS and RTM documents for configured SDLC namespaces...

**Issue:** Incomplete. Code also supports DS, CS, and OQ as SDLC singleton document types.

**Evidence:** qms_config.py:87-93

**Recommended Fix:**
> The CLI shall support the following SDLC document types for configured namespaces:
> - **RS** (Requirements Specification): Sequential ID within namespace
> - **RTM** (Requirements Traceability Matrix): Sequential ID within namespace
> - **DS** (Design Specification): Singleton per namespace
> - **CS** (Configuration Specification): Singleton per namespace
> - **OQ** (Operational Qualification): Singleton per namespace
>
> Each namespace requires explicit configuration in DOCUMENT_TYPES specifying the document ID prefix and storage path. Documents shall be stored in `QMS/SDLC-{NAMESPACE}/`.

---

### 3.5 REQ-WF-005: Approval Gate (IMPLEMENTATION GAP)

**Current Text:**
> The CLI shall block routing for approval if any reviewer submitted a review with `request-updates` outcome. All reviews must have `recommend` outcome before approval routing is permitted.

**Issue:** This check is NOT implemented in the code. Review outcomes are logged to the audit trail but not checked before allowing approval routing.

**Evidence:** route.py (no review outcome check), qms_audit.py (outcomes logged only)

**Recommended Fix (Option A - Mark as not implemented):**
> The CLI shall block routing for approval if any reviewer submitted a review with `request-updates` outcome. All reviews must have `recommend` outcome before approval routing is permitted.
>
> *Note: This requirement is not currently enforced by the implementation. See [future CR] for implementation.*

**Recommended Fix (Option B - Remove requirement):**
Delete this requirement and add a note that approval gate checking is not enforced.

---

### 3.6 REQ-WF-012: Retirement Routing (IMPLEMENTATION GAP)

**Current Text:**
> ...Retirement routing shall only be permitted for documents with version >= 1.0 (once-effective).

**Issue:** The version >= 1.0 check is NOT implemented. Currently, a never-effective document (version 0.X) can be routed for retirement.

**Evidence:** route.py (no version check for retirement routing)

**Recommended Fix (Option A - Mark as not implemented):**
> ...Retirement routing shall only be permitted for documents with version >= 1.0 (once-effective).
>
> *Note: The version check is not currently enforced by the implementation. See [future CR] for implementation.*

---

### 3.7 REQ-TASK-003: QA Auto-Assignment

**Current Text:**
> When routing for review, the CLI shall automatically add QA to the pending_assignees list regardless of explicit assignment.

**Issue:** QA is the DEFAULT assignee only when NO explicit `--assign` argument is provided. This is fallback behavior, not additive behavior.

**Evidence:** route.py:132 (`assignees = args.assign if args.assign else ['qa']`)

**Recommended Fix:**
> When routing for review, if no explicit assignees are specified via the --assign argument, the CLI shall default to assigning QA. When explicit assignees are provided, only those assignees shall be added to pending_assignees.

---

## 4. Requirements Needing Revision (Should Fix)

These requirements are accurate but incomplete or need clarification.

### 4.1 Security Domain

| REQ | Issue | Recommended Change |
|-----|-------|-------------------|
| REQ-SEC-003 | Missing initiator cross-action exception | Add: "Exception: Any Initiator may perform owner-only actions on documents owned by another Initiator." |
| REQ-SEC-004 | Dual-gate nuance not captured | Clarify: "Both group membership AND assignment are required. Note: Initiators may review but cannot approve." |

### 4.2 Document Management Domain

| REQ | Issue | Recommended Change |
|-----|-------|-------------------|
| REQ-DOC-002 | Missing CAPA as child of INV | Add CAPA to child relationships |
| REQ-DOC-005 | TP uses singular ID format | Clarify: "TP uses singular format (CR-001-TP), VAR and ER use sequential (CR-001-VAR-001)" |
| REQ-DOC-007 | Missing archive-on-effective behavior | Add: "If the document is EFFECTIVE, archive the current version before creating the draft" |
| REQ-DOC-009 | Missing review field clearing | Add: "The CLI shall also clear pending_assignees and review tracking fields" |
| REQ-DOC-010 | Missing --confirm and checkout check | Add: "--confirm flag required; checked-out documents cannot be cancelled" |
| REQ-DOC-011 | Missing --name optional behavior | Clarify: "--name is optional; if omitted, sequential fallback (TEMPLATE-001) is used" |

### 4.3 Workflow Domain

| REQ | Issue | Recommended Change |
|-----|-------|-------------------|
| REQ-WF-003 | Missing CAPA | Add CAPA to list of executable document types |
| REQ-WF-006 | responsible_user clearing nuance | Clarify: "Clear responsible_user only for non-executable documents transitioning to EFFECTIVE" |

### 4.4 Task & Config Domain

| REQ | Issue | Recommended Change |
|-----|-------|-------------------|
| REQ-TASK-004 | Missing bulk removal on rejection | Add: "Rejection removes ALL pending approval tasks across ALL user inboxes" |
| REQ-CFG-004 | Missing permission modifiers | Add: "Including command-level permissions with owner_only and assigned_only modifiers" |
| REQ-CFG-005 | Missing singleton flag | Add: "singleton flag for name-based (not sequential) document identification" |

### 4.5 Query/Template Domain

| REQ | Issue | Recommended Change |
|-----|-------|-------------------|
| REQ-PROMPT-006 | custom_header/footer not rendered | Clarify: "These fields are loaded but not currently rendered in prompt output" |
| REQ-TEMPLATE-003 | Wrong placeholder syntax | Update: "{{TITLE}} (double braces) and {TYPE}-XXX pattern (e.g., CR-XXX becomes CR-029)" |

---

## 5. Missing Requirements (New REQs Needed)

### 5.1 Critical (P1) - Must Add

| Proposed ID | Feature | Justification |
|-------------|---------|---------------|
| REQ-SEC-007 | **Workspace/Inbox Isolation** | Security boundary: users cannot access other users' workspace or inbox directories. Implemented in qms_auth.py:121-135 |
| REQ-DOC-013 | **Folder-per-Document Storage** | CR and INV documents are stored in dedicated subdirectories (QMS/CR/CR-001/). Affects path resolution. |
| REQ-WF-014 | **Execution Phase Tracking** | Metadata tracks pre_release vs post_release phase to determine correct workflow path for executable documents. |

### 5.2 Moderate (P2) - Should Add

| Proposed ID | Feature | Justification |
|-------------|---------|---------------|
| REQ-WF-015 | **Checked-in Requirement for Routing** | Documents must be checked in before routing for review or approval. |
| REQ-DOC-014 | **Archive Lifecycle** | Consolidated documentation of when archives are created (checkout effective, approval, retirement). |
| REQ-QRY-007 | **Comments Visibility Restriction** | Comments not visible during active IN_REVIEW or IN_APPROVAL states. |
| REQ-TASK-005 | **Assign Command** | QA can add reviewers/approvers after initial routing. |

### 5.3 Minor (P3) - Nice to Have

| Proposed ID | Feature | Justification |
|-------------|---------|---------------|
| REQ-TEMPLATE-005 | **Fallback Template Generation** | When no template file exists, CLI generates minimal structure automatically. |

---

## 6. Cross-Domain Issues

### 6.1 Document Type List Inconsistency

**Affected:** REQ-DOC-001, REQ-WF-003, REQ-SEC-002

The document type list appears in multiple requirements with different subsets. Recommend:
- Define authoritative list in REQ-DOC-001
- Other requirements should reference REQ-DOC-001 rather than re-listing

### 6.2 Review Outcome Storage Gap

**Affected:** REQ-WF-005, REQ-META-003, REQ-AUDIT-003

REQ-WF-005 expects review outcomes to be queryable for approval gating, but:
- Outcomes are logged to audit trail (append-only, not designed for queries)
- Outcomes are NOT stored in .meta/ where they would be accessible

This is an architectural gap. Resolution options:
1. Add review_outcomes to REQ-META-003 required fields and implement
2. Remove REQ-WF-005 approval gate requirement

### 6.3 Archive Behavior Documentation

**Affected:** REQ-DOC-007, REQ-DOC-008, REQ-WF-006, REQ-WF-013

Archive triggers are scattered across multiple requirements. Consider consolidating into a single REQ-DOC-014 for clarity.

---

## 7. Implementation Gaps Summary

Two requirements describe functionality that does not exist in the codebase:

| REQ | Described Behavior | Actual Implementation |
|-----|-------------------|----------------------|
| REQ-WF-005 | Block approval routing if any review has request-updates | No check exists; approval routing always permitted |
| REQ-WF-012 | Block retirement routing if version < 1.0 | No check exists; any document can be retired |

**Decision Required:** Should these be:
- (A) Marked as "not implemented" in the RS for now, with future CR to implement
- (B) Implemented in code as part of this CR
- (C) Removed from the RS as unnecessary constraints

---

## 8. Domain Scorecard

| Domain | Total | Accurate | Issues | Inaccurate | Notes |
|--------|-------|----------|--------|------------|-------|
| SEC | 6 | 3 | 2 | 1 | Permission model needs consolidation |
| DOC | 12 | 3 | 6 | 3 | Most revision needed |
| WF | 13 | 9 | 2 | 2 | 2 implementation gaps |
| META | 8 | 8 | 0 | 0 | Excellent - no changes needed |
| TASK/CFG | 9 | 6 | 2 | 1 | Config model incomplete |
| QUERY | 16 | 14 | 2 | 0 | Minor syntax fixes |
| **TOTAL** | **64** | **43** | **14** | **7** | |

---

## 9. Recommended CR Scope

### Phase 1: Critical Fixes (Blocking)

1. Fix 7 inaccurate requirements (Section 3)
2. Add REQ-SEC-007 (workspace isolation)
3. Decide on REQ-WF-005 and REQ-WF-012 implementation gaps

### Phase 2: Completeness Improvements

1. Revise 14 incomplete requirements (Section 4)
2. Add 3 critical missing requirements (Section 5.1)

### Phase 3: Documentation Enhancements

1. Add moderate/minor new requirements (Section 5.2, 5.3)
2. Consolidate cross-domain overlaps (Section 6)

---

## 10. Appendices

### A. Agent Reports Location

All detailed domain reports are preserved at:
- `.claude/sessions/Session-2026-01-19-004/A1-SEC-report.md`
- `.claude/sessions/Session-2026-01-19-004/A2-DOC-report.md`
- `.claude/sessions/Session-2026-01-19-004/A3-WF-report.md`
- `.claude/sessions/Session-2026-01-19-004/A4-META-report.md`
- `.claude/sessions/Session-2026-01-19-004/A5-TASK-report.md`
- `.claude/sessions/Session-2026-01-19-004/A6-QUERY-report.md`
- `.claude/sessions/Session-2026-01-19-004/AUDITOR-gap-report.md`

### B. Files Reviewed

```
qms-cli/
├── qms_auth.py
├── qms_audit.py
├── qms_config.py
├── qms_meta.py
├── qms_paths.py
├── qms_templates.py
├── prompts.py
├── workflow.py
├── prompts/
│   └── *.yaml
└── commands/
    ├── approve.py
    ├── cancel.py
    ├── checkin.py
    ├── checkout.py
    ├── close.py
    ├── comments.py
    ├── create.py
    ├── history.py
    ├── inbox.py
    ├── read.py
    ├── reject.py
    ├── release.py
    ├── revert.py
    ├── route.py
    ├── status.py
    └── workspace.py
```

---

**END OF REPORT**

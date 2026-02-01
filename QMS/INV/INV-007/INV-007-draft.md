---
title: PRE_APPROVED Documents Cannot Revert to DRAFT for Re-Review
revision_summary: Initial draft
---

# INV-007: PRE_APPROVED Documents Cannot Revert to DRAFT for Re-Review

## 1. Purpose

Investigate a gap in the QMS workflow state machine where PRE_APPROVED executable documents cannot be reverted to DRAFT status for re-review when scope changes are needed before execution begins.

---

## 2. Scope

### 2.1 Context

During preparation for CR-043 execution, scope changes were identified (authentication credentials mount, Python venv support). Attempting to check out and revise the PRE_APPROVED document revealed that the workflow does not support reverting to DRAFT for re-review.

- **Triggering Event:** CR-043 scope change attempt after pre-approval
- **Related Document:** CR-043

### 2.2 Deviation Type

- **Type:** Procedural

### 2.3 Systems/Documents Affected

- `SDLC-QMS-RS` - Requirements Specification (REQ-DOC-009, REQ-WF)
- `qms-cli` - CLI implementation of workflow state machine

---

## 3. Background

### 3.1 Expected Behavior

When a PRE_APPROVED document (not yet released for execution) requires scope changes, the workflow should allow:
1. Checkout of the document
2. Modification of content
3. Checkin reverts status to DRAFT
4. Re-routing through review and approval

This mirrors the behavior defined in REQ-DOC-009 for REVIEWED states.

### 3.2 Actual Behavior

REQ-DOC-009 states: "When a document in REVIEWED, PRE_REVIEWED, or POST_REVIEWED status is checked in, the CLI shall revert the status to DRAFT..."

PRE_APPROVED is explicitly NOT included in this list. Checking in a PRE_APPROVED document:
- Does NOT revert to DRAFT
- Maintains PRE_APPROVED status
- Prevents re-routing for review (no valid transition from PRE_APPROVED to IN_PRE_REVIEW)

### 3.3 Discovery

Discovered on 2026-02-01 during CR-043 execution preparation when attempting to add authentication and Python venv requirements to the already-approved scope.

### 3.4 Timeline

| Date | Event |
|------|-------|
| 2026-02-01 | CR-043 pre-approved (v1.0) |
| 2026-02-01 | Scope gaps identified (credentials, venv) |
| 2026-02-01 | Attempted checkout/modify/checkin to trigger re-review |
| 2026-02-01 | Discovered PRE_APPROVED does not revert on checkin |
| 2026-02-01 | Confirmed behavior matches RS (not a bug, a gap) |

---

## 4. Description of Deviation(s)

### 4.1 Facts and Observations

1. **REQ-DOC-009** explicitly lists only three states for checkin reversion: REVIEWED, PRE_REVIEWED, POST_REVIEWED
2. **PRE_APPROVED** is an approved state, not a reviewed state
3. The workflow state machine defines no backward transition from PRE_APPROVED
4. The only forward path from PRE_APPROVED is: release → IN_EXECUTION
5. Workarounds exist but are suboptimal:
   - Cancel and recreate (loses document history)
   - Proceed without re-review (scope changes not formally reviewed)
   - Use Type 1 VAR during execution (adds overhead, delays)

### 4.2 Evidence

- SDLC-QMS-RS v5.0, REQ-DOC-009: Lists REVIEWED, PRE_REVIEWED, POST_REVIEWED only
- SDLC-QMS-RS v5.0, Section 4.2: Executable workflow diagram shows no backward arrow from PRE_APPROVED
- CR-043 status after checkin: Remained PRE_APPROVED
- CLI error on route attempt: "No transition defined for route_review from PRE_APPROVED"

---

## 5. Impact Assessment

### 5.1 Systems Affected

| System | Impact | Description |
|--------|--------|-------------|
| QMS Workflow | Medium | No clean path to revise approved-but-unreleased documents |

### 5.2 Documents Affected

| Document | Impact | Description |
|----------|--------|-------------|
| Any PRE_APPROVED CR/INV | Medium | Cannot be revised through normal review cycle before release |

### 5.3 Other Impacts

- **Process efficiency:** Scope changes identified late require workarounds (VAR, cancel/recreate)
- **Audit trail clarity:** Using VARs for pre-release scope changes adds overhead and complexity
- **User experience:** Unintuitive that approved documents cannot be revised before execution

---

## 6. Root Cause Analysis

### 6.1 Contributing Factors

- REQ-DOC-009 was designed with the assumption that approved documents should remain stable
- The distinction between "approved but not yet executed" and "approved and executing" was not explicitly considered
- Executable document workflow complexity (dual review/approval cycles) increased the state space

### 6.2 Root Cause(s)

**Root Cause:** The requirements specification does not account for the use case where scope changes are needed after approval but before execution begins. The PRE_APPROVED state was treated as equivalent to EFFECTIVE (stable, final) rather than as a "ready to execute" staging state.

---

## 7. Remediation Plan (CAPAs)

| CAPA | Type | Description | Implementation | Outcome | Verified By - Date |
|------|------|-------------|----------------|---------|---------------------|
| INV-007-CAPA-001 | Preventive | Add REQ-WF-016 to allow PRE_APPROVED reversion to DRAFT via checkin | [IMPLEMENTATION] | [Pass/Fail] | [VERIFIER] - [DATE] |
| INV-007-CAPA-002 | Corrective | Implement REQ-WF-016 in qms-cli | [IMPLEMENTATION] | [Pass/Fail] | [VERIFIER] - [DATE] |

**Proposed REQ-WF-016:**

> **REQ-WF-016: Pre-Release Revision.** When a document in PRE_APPROVED status is checked in, the CLI shall revert the status to DRAFT and clear all review tracking fields, provided the document has not been released (status has never been IN_EXECUTION). This allows scope revision before execution begins.

---

## 8. Execution Comments

| Comment | Performed By - Date |
|---------|---------------------|
| [COMMENT] | [PERFORMER] - [DATE] |

---

## 9. Execution Summary

[EXECUTION_SUMMARY]

---

## 10. References

- **SOP-001:** Document Control
- **SOP-003:** Deviation Management
- **SDLC-QMS-RS:** QMS CLI Requirements Specification (REQ-DOC-009, REQ-WF-003)
- **CR-043:** Implement Containerized Claude Agent Infrastructure (triggering document)

---

**END OF DOCUMENT**

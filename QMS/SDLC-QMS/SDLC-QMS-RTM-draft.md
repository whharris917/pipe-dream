---
title: QMS CLI Requirements Traceability Matrix
revision_summary: Initial draft
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

## 4. Traceability Matrix

### 4.1 Security (REQ-SEC)

| REQ ID | Requirement | Test File | Test Function | Lines | Verification |
|--------|-------------|-----------|---------------|-------|--------------|
| REQ-SEC-001 | User Group Classification | test_security.py | test_group_permissions | TBD | Execute group-specific commands as each user |
| REQ-SEC-002 | Group-Based Action Authorization | test_security.py | test_unauthorized_actions | TBD | Attempt actions as unauthorized users |
| REQ-SEC-003 | Owner-Only Restrictions | test_security.py | test_owner_only_commands | TBD | Non-owner attempts checkin/release/revert/close |
| REQ-SEC-004 | Assignment-Based Review Access | test_security.py | test_review_assignment | TBD | Unassigned user attempts review |
| REQ-SEC-005 | Rejection Access | test_security.py | test_reject_assignment | TBD | Unassigned user attempts reject |
| REQ-SEC-006 | Unknown User Rejection | test_security.py | test_unknown_user | TBD | Command as nonexistent user |

### 4.2 Document Management (REQ-DOC)

| REQ ID | Requirement | Test File | Test Function | Lines | Verification |
|--------|-------------|-----------|---------------|-------|--------------|
| REQ-DOC-001 | Supported Document Types | test_document_types.py | test_create_all_types | TBD | Create one of each document type |
| REQ-DOC-002 | Child Document Relationships | test_document_types.py | test_child_documents | TBD | Create CR→TP→ER→VAR hierarchy |
| REQ-DOC-003 | QMS Folder Structure | test_sop_lifecycle.py | test_sop_full_lifecycle | TBD | Verify files in correct directories |
| REQ-DOC-004 | Sequential ID Generation | test_document_types.py | test_sequential_ids | TBD | Create two SOPs, verify sequence |
| REQ-DOC-005 | Child Document ID Generation | test_document_types.py | test_child_documents | TBD | Verify CR-XXX-VAR-001 format |
| REQ-DOC-006 | Version Format | test_sop_lifecycle.py | test_sop_full_lifecycle | TBD | Verify 0.1 → 1.0 → 1.1 progression |
| REQ-DOC-007 | Checkout Behavior | test_sop_lifecycle.py | test_sop_full_lifecycle | TBD | Verify workspace copy, metadata |
| REQ-DOC-008 | Checkin Updates QMS | test_sop_lifecycle.py | test_sop_full_lifecycle | TBD | Verify QMS draft updated |
| REQ-DOC-009 | Checkin Reverts Reviewed Status | test_sop_lifecycle.py | test_checkin_reverts_reviewed | TBD | Checkin from REVIEWED returns to DRAFT |
| REQ-DOC-010 | Cancel Restrictions | test_document_types.py | test_cancel_restrictions | TBD | Cancel v0.1 succeeds; v1.0 fails |
| REQ-DOC-011 | Template Name-Based ID | test_document_types.py | test_template_creation | TBD | Verify TEMPLATE-{NAME} format |
| REQ-DOC-012 | SDLC Document Types | test_document_types.py | test_sdlc_documents | TBD | Create QMS-RS, verify path |

### 4.3 Workflow State Machine (REQ-WF)

| REQ ID | Requirement | Test File | Test Function | Lines | Verification |
|--------|-------------|-----------|---------------|-------|--------------|
| REQ-WF-001 | Status Transition Validation | test_sop_lifecycle.py | test_invalid_transition | TBD | DRAFT → APPROVAL rejected |
| REQ-WF-002 | Non-Executable Document Lifecycle | test_sop_lifecycle.py | test_sop_full_lifecycle | TBD | Full SOP workflow to EFFECTIVE |
| REQ-WF-003 | Executable Document Lifecycle | test_cr_lifecycle.py | test_cr_full_lifecycle | TBD | Full CR workflow to CLOSED |
| REQ-WF-004 | Review Completion Gate | test_sop_lifecycle.py | test_multi_reviewer | TBD | Two reviewers, gate after both complete |
| REQ-WF-005 | Approval Gate | test_sop_lifecycle.py | test_approval_gate_blocking | TBD | request-updates blocks approval |
| REQ-WF-006 | Approval Version Bump | test_sop_lifecycle.py | test_sop_full_lifecycle | TBD | Verify 0.1 → 1.0, archive, EFFECTIVE |
| REQ-WF-007 | Rejection Handling | test_sop_lifecycle.py | test_rejection | TBD | Reject returns to REVIEWED |
| REQ-WF-008 | Release Transition | test_cr_lifecycle.py | test_cr_full_lifecycle | TBD | PRE_APPROVED → IN_EXECUTION |
| REQ-WF-009 | Revert Transition | test_cr_lifecycle.py | test_revert | TBD | POST_REVIEWED → IN_EXECUTION |
| REQ-WF-010 | Close Transition | test_cr_lifecycle.py | test_cr_full_lifecycle | TBD | POST_APPROVED → CLOSED |
| REQ-WF-011 | Terminal State Enforcement | test_cr_lifecycle.py | test_terminal_state | TBD | CLOSED rejects routing |
| REQ-WF-012 | Retirement Routing | test_sop_lifecycle.py | test_retirement | TBD | v0.1 rejected; v1.0 accepted |
| REQ-WF-013 | Retirement Transition | test_sop_lifecycle.py | test_retirement | TBD | Archive, remove, RETIRED status |

### 4.4 Metadata Architecture (REQ-META)

| REQ ID | Requirement | Test File | Test Function | Lines | Verification |
|--------|-------------|-----------|---------------|-------|--------------|
| REQ-META-001 | Three-Tier Separation | test_sop_lifecycle.py | test_sop_full_lifecycle | TBD | Inspect frontmatter, .meta, .audit |
| REQ-META-002 | CLI-Exclusive Metadata Management | test_sop_lifecycle.py | test_sop_full_lifecycle | TBD | Frontmatter lacks workflow fields |
| REQ-META-003 | Required Metadata Fields | test_document_types.py | test_create_all_types | TBD | Read .meta, verify all fields |
| REQ-META-004 | Execution Phase Tracking | test_cr_lifecycle.py | test_cr_full_lifecycle | TBD | execution_phase changes on release |

### 4.5 Audit Trail (REQ-AUDIT)

| REQ ID | Requirement | Test File | Test Function | Lines | Verification |
|--------|-------------|-----------|---------------|-------|--------------|
| REQ-AUDIT-001 | Append-Only Logging | test_sop_lifecycle.py | test_sop_full_lifecycle | TBD | Line count only increases |
| REQ-AUDIT-002 | Required Event Types | test_sop_lifecycle.py, test_cr_lifecycle.py | multiple | TBD | Each event type appears |
| REQ-AUDIT-003 | Event Attribution | test_sop_lifecycle.py | test_sop_full_lifecycle | TBD | ts, event, user, version fields |
| REQ-AUDIT-004 | Comment Preservation | test_sop_lifecycle.py | test_sop_full_lifecycle | TBD | Comment in audit, not frontmatter |

### 4.6 Task & Inbox Management (REQ-TASK)

| REQ ID | Requirement | Test File | Test Function | Lines | Verification |
|--------|-------------|-----------|---------------|-------|--------------|
| REQ-TASK-001 | Task Generation on Routing | test_sop_lifecycle.py | test_sop_full_lifecycle | TBD | Task file created in inbox |
| REQ-TASK-002 | Task Content Requirements | test_sop_lifecycle.py | test_sop_full_lifecycle | TBD | Task contains required fields |
| REQ-TASK-003 | QA Auto-Assignment | test_sop_lifecycle.py | test_sop_full_lifecycle | TBD | qa in pending_assignees |
| REQ-TASK-004 | Task Removal on Completion | test_sop_lifecycle.py | test_sop_full_lifecycle | TBD | Task removed after review |

### 4.7 Project Configuration (REQ-CFG)

| REQ ID | Requirement | Test File | Test Function | Lines | Verification |
|--------|-------------|-----------|---------------|-------|--------------|
| REQ-CFG-001 | Project Root Discovery | test_queries.py | test_subdirectory_execution | TBD | CLI works from subdirectory |
| REQ-CFG-002 | QMS Root Path | test_sop_lifecycle.py | test_sop_full_lifecycle | TBD | Files under QMS/ |
| REQ-CFG-003 | Users Directory Path | test_sop_lifecycle.py | test_sop_full_lifecycle | TBD | Workspace/inbox under .claude/users/ |
| REQ-CFG-004 | Agents Directory Path | test_queries.py | test_agent_definitions | TBD | Agent files exist |
| REQ-CFG-005 | User Registry | test_security.py | test_unknown_user | TBD | Valid users succeed; invalid fail |
| REQ-CFG-006 | Document Type Registry | test_document_types.py | test_create_all_types | TBD | Each type stored correctly |
| REQ-CFG-007 | Agent Definition Loading | test_queries.py | test_agent_definitions | TBD | Agent file readable |

### 4.8 Query Operations (REQ-QRY)

| REQ ID | Requirement | Test File | Test Function | Lines | Verification |
|--------|-------------|-----------|---------------|-------|--------------|
| REQ-QRY-001 | Document Reading | test_queries.py | test_read_versions | TBD | Read effective, draft, archived |
| REQ-QRY-002 | Document Status Query | test_queries.py | test_status_output | TBD | All required fields in output |
| REQ-QRY-003 | Audit History Query | test_queries.py | test_history_output | TBD | Events in chronological order |
| REQ-QRY-004 | Review Comments Query | test_queries.py | test_comments_output | TBD | Comment appears in output |
| REQ-QRY-005 | Inbox Query | test_queries.py | test_inbox_output | TBD | Task listed with correct fields |
| REQ-QRY-006 | Workspace Query | test_queries.py | test_workspace_output | TBD | Checked out docs listed |

---

## 5. Test Execution Summary

*To be completed after test execution.*

| Test Protocol | Tests | Passed | Failed | Date | Executor |
|---------------|-------|--------|--------|------|----------|
| test_sop_lifecycle.py | TBD | TBD | TBD | TBD | TBD |
| test_cr_lifecycle.py | TBD | TBD | TBD | TBD | TBD |
| test_security.py | TBD | TBD | TBD | TBD | TBD |
| test_document_types.py | TBD | TBD | TBD | TBD | TBD |
| test_queries.py | TBD | TBD | TBD | TBD | TBD |

---

## 6. References

- SDLC-QMS-RS: QMS CLI Requirements Specification
- SOP-007: Software Development Lifecycle

---

**END OF DOCUMENT**

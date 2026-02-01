---
title: QMS CLI Requirements Traceability Matrix
revision_summary: 'CR-041: Add traceability for REQ-MCP (10 requirements) for MCP
  server tools'
---

# SDLC-QMS-RTM: QMS CLI Requirements Traceability Matrix

## 1. Purpose

This document provides traceability between the requirements specified in SDLC-QMS-RS v3.0 and the qualification tests that verify them. Each requirement is mapped to specific test protocols and functions where verification occurs.

---

## 2. Scope

This RTM covers all 94 requirements defined in SDLC-QMS-RS across the following domains:

- REQ-SEC (Security): 8 requirements
- REQ-DOC (Document Management): 14 requirements
- REQ-WF (Workflow): 15 requirements
- REQ-META (Metadata): 4 requirements
- REQ-AUDIT (Audit Trail): 4 requirements
- REQ-TASK (Task/Inbox): 4 requirements
- REQ-CFG (Configuration): 5 requirements
- REQ-QRY (Query Operations): 6 requirements
- REQ-PROMPT (Prompt Generation): 6 requirements
- REQ-TEMPLATE (Document Templates): 5 requirements
- REQ-INIT (Project Initialization): 8 requirements
- REQ-USER (User Management): 5 requirements
- REQ-MCP (MCP Server): 10 requirements

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
| Document Types | `qualification/test_document_types.py` | Creation, child documents, SDLC namespaces |
| Queries | `qualification/test_queries.py` | Read, status, history, inbox, workspace |
| Prompts | `qualification/test_prompts.py` | Prompt generation and configuration |
| Templates | `qualification/test_templates.py` | Template-based document creation |
| Init | `qualification/test_init.py` | Project initialization and user management |
| MCP | `qualification/test_mcp.py` | MCP server tools and functional equivalence |

### 3.4 Traceability Convention

Test code includes inline markers `[REQ-XXX]` to identify where each requirement is verified. This RTM references those markers with file and line numbers.

---

## 4. Summary Matrix

| REQ ID | Requirement | Code Reference | Status |
|--------|-------------|----------------|--------|
| REQ-SEC-001 | User Group Classification | test_security::test_user_group_classification | PASS |
| REQ-SEC-002 | Group-Based Action Authorization | test_security::test_unauthorized_create, test_unauthorized_assign, test_fix_authorization, test_unauthorized_route, test_unauthorized_release, test_unauthorized_revert, test_unauthorized_close | PASS |
| REQ-SEC-003 | Owner-Only Restrictions | test_security::test_owner_only_checkin, test_owner_only_route, test_owner_only_revert | PASS |
| REQ-SEC-004 | Assignment-Based Review Access | test_security::test_unassigned_cannot_review, test_unassigned_cannot_approve | PASS |
| REQ-SEC-005 | Rejection Access | test_security::test_rejection_access | PASS |
| REQ-SEC-006 | Unknown User Rejection | test_security::test_unknown_user_rejection | PASS |
| REQ-SEC-007 | Assignment Validation | test_security::test_assignment_validation_review, test_assignment_validation_approval | PASS |
| REQ-SEC-008 | Workspace/Inbox Isolation | test_security::test_workspace_isolation, test_inbox_isolation | PASS |
| REQ-DOC-001 | Supported Document Types | test_document_types::test_create_sop, test_create_cr, test_create_inv, test_create_er_under_tp | PASS |
| REQ-DOC-002 | Child Document Relationships | test_document_types::test_create_tp_under_cr, test_create_var_under_cr, test_create_var_under_inv | PASS |
| REQ-DOC-003 | QMS Folder Structure | test_sop_lifecycle::test_sop_full_lifecycle | PASS |
| REQ-DOC-004 | Sequential ID Generation | test_document_types::test_sequential_id_generation | PASS |
| REQ-DOC-005 | Child Document ID Generation | test_document_types::test_create_var_under_cr, test_child_id_generation | PASS |
| REQ-DOC-006 | Version Format | test_sop_lifecycle::test_sop_full_lifecycle | PASS |
| REQ-DOC-007 | Checkout Behavior | test_sop_lifecycle::test_sop_full_lifecycle, test_document_types::test_checkout_effective_creates_archive | PASS |
| REQ-DOC-008 | Checkin Updates QMS | test_sop_lifecycle::test_sop_full_lifecycle | PASS |
| REQ-DOC-009 | Checkin Reverts Reviewed Status | test_sop_lifecycle::test_checkin_reverts_reviewed, test_cr_lifecycle::test_checkin_reverts_pre_reviewed, test_cr_lifecycle::test_checkin_reverts_post_reviewed | PASS |
| REQ-DOC-010 | Cancel Restrictions | test_document_types::test_cancel_v0_document, test_cancel_blocked_for_v1, test_cancel_blocked_while_checked_out, test_cancel_cleans_workspace_and_inbox | PASS |
| REQ-DOC-011 | Template Name-Based ID | test_document_types::test_template_name_based_id | PASS |
| REQ-DOC-012 | Folder-per-Document Storage | test_document_types::test_folder_per_document_cr, test_folder_per_document_inv, test_child_documents_in_parent_folder | PASS |
| REQ-DOC-013 | SDLC Namespace Registration | test_document_types::test_sdlc_namespace_registration, test_sdlc_namespace_list | PASS |
| REQ-DOC-014 | SDLC Document Identification | test_document_types::test_sdlc_document_identification | PASS |
| REQ-WF-001 | Status Transition Validation | test_sop_lifecycle::test_invalid_transition, test_invalid_transitions_comprehensive | PASS |
| REQ-WF-002 | Non-Executable Document Lifecycle | test_sop_lifecycle::test_sop_full_lifecycle | PASS |
| REQ-WF-003 | Executable Document Lifecycle | test_cr_lifecycle::test_cr_full_lifecycle | PASS |
| REQ-WF-004 | Review Completion Gate | test_sop_lifecycle::test_multi_reviewer_gate | PASS |
| REQ-WF-005 | Approval Gate | test_sop_lifecycle::test_approval_gate_blocking, test_approval_gate_requires_quality_review | PASS |
| REQ-WF-006 | Approval Version Bump | test_sop_lifecycle::test_sop_full_lifecycle | PASS |
| REQ-WF-007 | Rejection Handling | test_sop_lifecycle::test_rejection, test_cr_lifecycle::test_pre_approval_rejection, test_post_approval_rejection | PASS |
| REQ-WF-008 | Release Transition | test_cr_lifecycle::test_cr_full_lifecycle, test_owner_only_release | PASS |
| REQ-WF-009 | Revert Transition | test_cr_lifecycle::test_revert | PASS |
| REQ-WF-010 | Close Transition | test_cr_lifecycle::test_cr_full_lifecycle, test_owner_only_close | PASS |
| REQ-WF-011 | Terminal State Enforcement | test_cr_lifecycle::test_terminal_state, test_terminal_state_retired | PASS |
| REQ-WF-012 | Retirement Routing | test_sop_lifecycle::test_retirement, test_retirement_rejected_for_v0 | PASS |
| REQ-WF-013 | Retirement Transition | test_sop_lifecycle::test_retirement | PASS |
| REQ-WF-014 | Execution Phase Tracking | test_cr_lifecycle::test_cr_full_lifecycle, test_execution_phase_preserved | PASS |
| REQ-WF-015 | Checked-in Requirement for Routing | test_sop_lifecycle::test_routing_requires_checkin | PASS |
| REQ-META-001 | Three-Tier Separation | test_sop_lifecycle::test_sop_full_lifecycle | PASS |
| REQ-META-002 | CLI-Exclusive Metadata Management | test_sop_lifecycle::test_sop_full_lifecycle | PASS |
| REQ-META-003 | Required Metadata Fields | test_sop_lifecycle::test_sop_full_lifecycle, test_cr_lifecycle::test_cr_full_lifecycle, test_metadata_required_fields | PASS |
| REQ-META-004 | Execution Phase Tracking | test_cr_lifecycle::test_cr_full_lifecycle, test_execution_phase_preserved | PASS |
| REQ-AUDIT-001 | Append-Only Logging | test_sop_lifecycle::test_sop_full_lifecycle, test_audit_immutability | PASS |
| REQ-AUDIT-002 | Required Event Types | test_sop_lifecycle::test_sop_full_lifecycle, test_cr_lifecycle::test_cr_full_lifecycle, test_queries::test_history_shows_all_event_types, test_cr_lifecycle::test_all_audit_event_types | PASS |
| REQ-AUDIT-003 | Event Attribution | test_sop_lifecycle::test_sop_full_lifecycle | PASS |
| REQ-AUDIT-004 | Comment Preservation | test_sop_lifecycle::test_sop_full_lifecycle | PASS |
| REQ-TASK-001 | Task Generation on Routing | test_sop_lifecycle::test_sop_full_lifecycle | PASS |
| REQ-TASK-002 | Task Content Requirements | test_sop_lifecycle::test_sop_full_lifecycle, test_sop_lifecycle::test_task_content_all_fields | PASS |
| REQ-TASK-003 | Task Removal on Completion | test_sop_lifecycle::test_sop_full_lifecycle, test_rejection_clears_approval_tasks | PASS |
| REQ-TASK-004 | Assign Command | test_sop_lifecycle::test_assign_command | PASS |
| REQ-CFG-001 | Project Root Discovery | conftest::temp_project fixture, test_init::test_init_creates_complete_structure, test_init::test_project_root_discovery_via_config, test_init::test_project_root_discovery_via_qms_fallback | PASS |
| REQ-CFG-002 | QMS Root Path | test_sop_lifecycle::test_sop_full_lifecycle | PASS |
| REQ-CFG-003 | Users Directory Path | test_sop_lifecycle::test_sop_full_lifecycle | PASS |
| REQ-CFG-004 | User Registry | test_security::test_unknown_user_rejection, test_user_group_classification | PASS |
| REQ-CFG-005 | Document Type Registry | test_document_types::test_create_sop, test_create_cr, test_create_inv, test_document_type_registry | PASS |
| REQ-QRY-001 | Document Reading | test_queries::test_read_draft, test_read_effective, test_read_archived_version, test_read_draft_flag | PASS |
| REQ-QRY-002 | Document Status Query | test_queries::test_status_query, test_status_shows_checked_out, test_status_shows_executable_field | PASS |
| REQ-QRY-003 | Audit History Query | test_queries::test_history_query, test_history_shows_all_event_types | PASS |
| REQ-QRY-004 | Review Comments Query | test_queries::test_comments_query, test_comments_includes_rejection | PASS |
| REQ-QRY-005 | Inbox Query | test_queries::test_inbox_query, test_inbox_multiple_tasks, test_inbox_empty_when_no_tasks | PASS |
| REQ-QRY-006 | Workspace Query | test_queries::test_workspace_query, test_workspace_multiple_documents, test_workspace_empty_after_checkin | PASS |
| REQ-PROMPT-001 | Task Prompt Generation | test_prompts::test_review_task_prompt_generated | PASS |
| REQ-PROMPT-002 | YAML-Based Configuration | test_prompts::test_prompts_directory_exists | PASS |
| REQ-PROMPT-003 | Hierarchical Prompt Lookup | test_prompts::test_prompts_have_workflow_phase_context | PASS |
| REQ-PROMPT-004 | Checklist Generation | test_prompts::test_review_prompt_has_checklist | PASS |
| REQ-PROMPT-005 | Prompt Content Structure | test_prompts::test_prompt_has_required_sections | PASS |
| REQ-PROMPT-006 | Custom Sections | test_prompts::test_prompt_supports_custom_content | PASS |
| REQ-TEMPLATE-001 | Template-Based Creation | test_templates::test_new_document_uses_template, test_cr_uses_cr_template | PASS |
| REQ-TEMPLATE-002 | Template Location | test_templates::test_templates_in_qms_template_directory | PASS |
| REQ-TEMPLATE-003 | Variable Substitution | test_templates::test_title_substitution, test_doc_id_substitution | PASS |
| REQ-TEMPLATE-004 | Frontmatter Initialization | test_templates::test_frontmatter_title_initialized, test_frontmatter_revision_summary_initialized | PASS |
| REQ-TEMPLATE-005 | Fallback Template Generation | test_templates::test_document_created_without_template_file, test_fallback_includes_document_heading | PASS |
| REQ-INIT-001 | Config File Creation | test_init::test_init_creates_complete_structure | PASS |
| REQ-INIT-002 | QMS Directory Structure | test_init::test_init_creates_complete_structure | PASS |
| REQ-INIT-003 | User Directory Structure | test_init::test_init_creates_complete_structure | PASS |
| REQ-INIT-004 | Default Agent Creation | test_init::test_init_seeds_qa_agent | PASS |
| REQ-INIT-005 | SOP Seeding | test_init::test_init_seeds_sops | PASS |
| REQ-INIT-006 | Template Seeding | test_init::test_init_seeds_templates | PASS |
| REQ-INIT-007 | Safety Checks | test_init::test_init_blocked_by_existing_qms, test_init_blocked_by_existing_users, test_init_blocked_by_existing_qa_agent, test_init_blocked_by_existing_config | PASS |
| REQ-INIT-008 | Root Flag Support | test_init::test_init_with_root_flag | PASS |
| REQ-USER-001 | Hardcoded Administrators | test_init::test_hardcoded_admins_work | PASS |
| REQ-USER-002 | Agent File-Based Group Assignment | test_init::test_agent_group_assignment | PASS |
| REQ-USER-003 | User Add Command | test_init::test_user_add_creates_structure, test_user_add_requires_admin | PASS |
| REQ-USER-004 | Unknown User Handling | test_init::test_unknown_user_error | PASS |
| REQ-USER-005 | User List Command | test_init::test_user_add_creates_structure, test_user_list_command, test_user_list_shows_groups | PASS |
| REQ-MCP-001 | MCP Protocol Implementation | test_mcp::test_mcp_server_imports, test_register_tools_creates_all_tools | PASS |
| REQ-MCP-002 | User Command Tools | test_mcp::test_register_tools_creates_all_tools, test_qms_inbox_equivalence, test_qms_workspace_equivalence, test_qms_status_equivalence, test_qms_read_equivalence, test_qms_history_equivalence, test_qms_comments_equivalence, test_full_sop_lifecycle_via_cli | PASS |
| REQ-MCP-003 | Document Lifecycle Tools | test_mcp::test_register_tools_creates_all_tools, test_qms_create_equivalence, test_qms_checkout_equivalence, test_qms_checkin_equivalence, test_qms_cancel_equivalence, test_full_sop_lifecycle_via_cli, test_full_cr_lifecycle_via_cli | PASS |
| REQ-MCP-004 | Workflow Tools | test_mcp::test_register_tools_creates_all_tools, test_qms_route_review_equivalence, test_qms_route_approval_equivalence, test_qms_assign_equivalence, test_qms_review_equivalence, test_qms_approve_equivalence, test_qms_reject_equivalence, test_full_sop_lifecycle_via_cli, test_full_cr_lifecycle_via_cli | PASS |
| REQ-MCP-005 | Execution Tools | test_mcp::test_register_tools_creates_all_tools, test_qms_release_equivalence, test_qms_revert_equivalence, test_qms_close_equivalence, test_full_cr_lifecycle_via_cli | PASS |
| REQ-MCP-006 | Administrative Tools | test_mcp::test_register_tools_creates_all_tools, test_qms_fix_equivalence, test_qms_fix_requires_administrator | PASS |
| REQ-MCP-007 | Functional Equivalence | test_mcp::test_qms_inbox_equivalence, test_qms_workspace_equivalence, test_qms_status_equivalence, test_qms_read_equivalence, test_qms_history_equivalence, test_qms_comments_equivalence, test_qms_create_equivalence, test_qms_checkout_equivalence, test_qms_checkin_equivalence, test_qms_cancel_equivalence, test_qms_route_review_equivalence, test_qms_route_approval_equivalence, test_qms_assign_equivalence, test_qms_review_equivalence, test_qms_approve_equivalence, test_qms_reject_equivalence, test_qms_release_equivalence, test_qms_revert_equivalence, test_qms_close_equivalence, test_qms_fix_equivalence, test_full_sop_lifecycle_via_cli, test_full_cr_lifecycle_via_cli | PASS |
| REQ-MCP-008 | Structured Responses | test_mcp::test_mcp_tool_returns_string | PASS |
| REQ-MCP-009 | Permission Enforcement | test_mcp::test_qms_fix_requires_administrator, test_mcp_permission_enforcement, test_mcp_assign_requires_quality_group | PASS |
| REQ-MCP-010 | Setup Command Exclusion | test_mcp::test_mcp_excludes_setup_commands | PASS |

---

## 5. Traceability Details

### 5.1 Security (REQ-SEC)

#### REQ-SEC-001: User Group Classification

**Requirement:** The CLI shall classify all users into exactly one of four groups: administrator, initiator, quality, or reviewer. The administrator group inherits all initiator permissions.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_security.py | test_user_group_classification | Verify users are classified into correct groups with appropriate permissions. |

---

#### REQ-SEC-002: Group-Based Action Authorization

**Requirement:** The CLI shall only permit actions when the user's group is authorized per the PERMISSIONS registry.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_security.py | test_unauthorized_create | Non-initiators cannot create documents. |
| test_security.py | test_unauthorized_assign | Non-QA users cannot assign reviewers. |
| test_security.py | test_fix_authorization | Administrators can use the fix command; non-administrators cannot. |
| test_security.py | test_unauthorized_route | Non-initiators cannot route documents. |
| test_security.py | test_unauthorized_release | Non-initiators cannot release executable documents. |
| test_security.py | test_unauthorized_revert | Non-initiators cannot revert executable documents. |
| test_security.py | test_unauthorized_close | Non-initiators cannot close executable documents. |

---

#### REQ-SEC-003: Owner-Only Restrictions

**Requirement:** The CLI shall reject checkin, route, release, revert, and close commands when the user is not the document's responsible_user.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_security.py | test_owner_only_checkin | Only the document owner can checkin. |
| test_security.py | test_owner_only_route | Only the document owner can route for review/approval. |
| test_security.py | test_owner_only_revert | Only the document owner can revert executable documents. |

---

#### REQ-SEC-004: Assignment-Based Review Access

**Requirement:** The CLI shall reject review and approve actions unless the user is listed in the document's pending_assignees and is a member of an authorized group.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_security.py | test_unassigned_cannot_review | Users not in pending_assignees cannot submit reviews. |
| test_security.py | test_unassigned_cannot_approve | Users not in pending_assignees cannot approve. |

---

#### REQ-SEC-005: Rejection Access

**Requirement:** The CLI shall permit reject actions using the same authorization rules as approve.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_security.py | test_rejection_access | Rejection follows same authorization rules as approve. |

---

#### REQ-SEC-006: Unknown User Rejection

**Requirement:** The CLI shall reject any command invoked with a user identifier not present in the user registry.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_security.py | test_unknown_user_rejection | Commands with unknown user identifiers are rejected. |

---

#### REQ-SEC-007: Assignment Validation

**Requirement:** The CLI shall validate workflow assignments to ensure only authorized users are assigned.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_security.py | test_assignment_validation_review | Assignment for review validates user authorization. |
| test_security.py | test_assignment_validation_approval | Assignment for approval validates quality/reviewer membership. |

---

#### REQ-SEC-008: Workspace/Inbox Isolation

**Requirement:** The CLI shall restrict workspace and inbox operations to the requesting user's own directories.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_security.py | test_workspace_isolation | Users cannot access other users' workspaces. |
| test_security.py | test_inbox_isolation | Users cannot access other users' inboxes. |

---

### 5.2 Document Management (REQ-DOC)

#### REQ-DOC-001: Supported Document Types

**Requirement:** The CLI shall only support creation and management of defined document types.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_document_types.py | test_create_sop | Create SOP document type. |
| test_document_types.py | test_create_cr | Create CR document type (executable, folder-per-doc). |
| test_document_types.py | test_create_inv | Create INV document type (executable, folder-per-doc). |
| test_document_types.py | test_create_er_under_tp | Create ER document type as child of TP. |

---

#### REQ-DOC-002: Child Document Relationships

**Requirement:** The CLI shall enforce parent-child relationships: TP is a child of CR; ER is a child of TP; VAR is a child of CR or INV.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_document_types.py | test_create_tp_under_cr | TP is created as a child of CR. |
| test_document_types.py | test_create_var_under_cr | VAR is created as a child of CR. |
| test_document_types.py | test_create_var_under_inv | VAR can also be created as a child of INV. |

---

#### REQ-DOC-003: QMS Folder Structure

**Requirement:** The CLI shall maintain the required folder structure with QMS/, .meta/, .audit/, .archive/, and per-user directories.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_sop_lifecycle.py | test_sop_full_lifecycle | Verifies folder structure during complete lifecycle. |

---

#### REQ-DOC-004: Sequential ID Generation

**Requirement:** The CLI shall generate document IDs sequentially within each document type.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_document_types.py | test_sequential_id_generation | Document IDs are generated sequentially within each type. |

---

#### REQ-DOC-005: Child Document ID Generation

**Requirement:** For child document types, the CLI shall generate IDs in the format `{PARENT}-{TYPE}-NNN`.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_document_types.py | test_create_var_under_cr | VAR ID follows {PARENT}-VAR-NNN format. |
| test_document_types.py | test_child_id_generation | Child document IDs follow format {PARENT}-{TYPE}-NNN. |

---

#### REQ-DOC-006: Version Format

**Requirement:** The CLI shall enforce version numbers in the format `N.X`.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_sop_lifecycle.py | test_sop_full_lifecycle | Verifies version format throughout lifecycle. |

---

#### REQ-DOC-007: Checkout Behavior

**Requirement:** The CLI shall permit checkout and perform required state changes.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_sop_lifecycle.py | test_sop_full_lifecycle | Verifies checkout copies to workspace and sets metadata. |
| test_document_types.py | test_checkout_effective_creates_archive | Checkout of EFFECTIVE document creates archive and N.1 draft. |

---

#### REQ-DOC-008: Checkin Updates QMS

**Requirement:** When a user checks in a document, the CLI shall copy from workspace to QMS and update state.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_sop_lifecycle.py | test_sop_full_lifecycle | Verifies checkin updates QMS directory. |

---

#### REQ-DOC-009: Checkin Reverts Reviewed Status

**Requirement:** When a document in REVIEWED status is checked in, the CLI shall revert the status to DRAFT.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_sop_lifecycle.py | test_checkin_reverts_reviewed | Checkin from REVIEWED status reverts to DRAFT. |
| test_cr_lifecycle.py | test_checkin_reverts_pre_reviewed | Checkin from PRE_REVIEWED status reverts to DRAFT. |
| test_cr_lifecycle.py | test_checkin_reverts_post_reviewed | Checkin from POST_REVIEWED status reverts to DRAFT. |

---

#### REQ-DOC-010: Cancel Restrictions

**Requirement:** The CLI shall only permit cancellation of documents with version < 1.0.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_document_types.py | test_cancel_v0_document | Documents with version < 1.0 can be cancelled. |
| test_document_types.py | test_cancel_blocked_for_v1 | Documents with version >= 1.0 cannot be cancelled. |
| test_document_types.py | test_cancel_blocked_while_checked_out | Cancel blocked while document is checked out. |
| test_document_types.py | test_cancel_cleans_workspace_and_inbox | Cancel removes workspace and inbox entries. |

---

#### REQ-DOC-011: Template Name-Based ID

**Requirement:** Template documents shall use name-based identifiers in the format `TEMPLATE-{NAME}`.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_document_types.py | test_template_name_based_id | Template documents use name-based IDs. |

---

#### REQ-DOC-012: Folder-per-Document Storage

**Requirement:** CR and INV documents shall be stored in dedicated subdirectories.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_document_types.py | test_folder_per_document_cr | CR documents use folder-per-document pattern. |
| test_document_types.py | test_folder_per_document_inv | INV documents use folder-per-document pattern. |
| test_document_types.py | test_child_documents_in_parent_folder | Child documents stored in parent's folder. |

---

#### REQ-DOC-013: SDLC Namespace Registration

**Requirement:** The CLI shall support SDLC namespace registration via the `namespace add` command.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_document_types.py | test_sdlc_namespace_registration | SDLC namespaces can be registered. |
| test_document_types.py | test_sdlc_namespace_list | Registered namespaces can be listed. |

---

#### REQ-DOC-014: SDLC Document Identification

**Requirement:** SDLC documents shall be identified by the pattern `SDLC-{NAMESPACE}-{TYPE}`.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_document_types.py | test_sdlc_document_identification | SDLC documents use correct identification pattern. |

---

### 5.3 Workflow State Machine (REQ-WF)

#### REQ-WF-001: Status Transition Validation

**Requirement:** The CLI shall reject any status transition not defined in the workflow state machine.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_sop_lifecycle.py | test_invalid_transition | Invalid status transitions are rejected. |
| test_sop_lifecycle.py | test_invalid_transitions_comprehensive | Multiple invalid transition paths are rejected. |

---

#### REQ-WF-002: Non-Executable Document Lifecycle

**Requirement:** Non-executable documents shall follow: DRAFT → IN_REVIEW → REVIEWED → IN_APPROVAL → APPROVED → EFFECTIVE.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_sop_lifecycle.py | test_sop_full_lifecycle | Complete non-executable lifecycle verification. |

---

#### REQ-WF-003: Executable Document Lifecycle

**Requirement:** Executable documents shall follow the dual review/approval cycle with execution phase.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_cr_lifecycle.py | test_cr_full_lifecycle | Complete executable lifecycle verification. |

---

#### REQ-WF-004: Review Completion Gate

**Requirement:** The CLI shall transition from IN_REVIEW to REVIEWED only when all reviewers complete.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_sop_lifecycle.py | test_multi_reviewer_gate | Review completion gate with multiple reviewers. |

---

#### REQ-WF-005: Approval Gate

**Requirement:** The CLI shall block routing for approval unless all reviews recommend AND at least one quality group member reviewed.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_sop_lifecycle.py | test_approval_gate_blocking | Approval blocked when review has request-updates. |
| test_sop_lifecycle.py | test_approval_gate_requires_quality_review | Approval requires at least one quality group review. |

---

#### REQ-WF-006: Approval Version Bump

**Requirement:** Upon successful approval, the CLI shall increment major version and transition appropriately.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_sop_lifecycle.py | test_sop_full_lifecycle | Version bump upon approval verified. |

---

#### REQ-WF-007: Rejection Handling

**Requirement:** When any approver rejects, the CLI shall transition back to the most recent REVIEWED state.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_sop_lifecycle.py | test_rejection | Rejection returns to REVIEWED. |
| test_cr_lifecycle.py | test_pre_approval_rejection | Pre-approval rejection returns to PRE_REVIEWED. |
| test_cr_lifecycle.py | test_post_approval_rejection | Post-approval rejection returns to POST_REVIEWED. |

---

#### REQ-WF-008: Release Transition

**Requirement:** The CLI shall transition executable documents from PRE_APPROVED to IN_EXECUTION upon release.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_cr_lifecycle.py | test_cr_full_lifecycle | Release transition verified. |
| test_cr_lifecycle.py | test_owner_only_release | Only owner can release. |

---

#### REQ-WF-009: Revert Transition

**Requirement:** The CLI shall transition from POST_REVIEWED to IN_EXECUTION upon revert command.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_cr_lifecycle.py | test_revert | Revert from POST_REVIEWED to IN_EXECUTION. |

---

#### REQ-WF-010: Close Transition

**Requirement:** The CLI shall transition from POST_APPROVED to CLOSED upon close command.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_cr_lifecycle.py | test_cr_full_lifecycle | Close transition verified. |
| test_cr_lifecycle.py | test_owner_only_close | Only owner can close. |

---

#### REQ-WF-011: Terminal State Enforcement

**Requirement:** The CLI shall reject all transitions from terminal states.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_cr_lifecycle.py | test_terminal_state | CLOSED state rejects all routing. |
| test_cr_lifecycle.py | test_terminal_state_retired | RETIRED state rejects all routing. |

---

#### REQ-WF-012: Retirement Routing

**Requirement:** The CLI shall support routing for retirement approval for documents with version >= 1.0.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_sop_lifecycle.py | test_retirement | Retirement workflow for effective document. |
| test_sop_lifecycle.py | test_retirement_rejected_for_v0 | Retirement rejected for never-effective documents. |

---

#### REQ-WF-013: Retirement Transition

**Requirement:** Upon retirement approval, the CLI shall archive and remove the document.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_sop_lifecycle.py | test_retirement | Retirement transition verified. |

---

#### REQ-WF-014: Execution Phase Tracking

**Requirement:** For executable documents, the CLI shall track execution phase in metadata.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_cr_lifecycle.py | test_cr_full_lifecycle | Execution phase tracking verified. |
| test_cr_lifecycle.py | test_execution_phase_preserved | Execution phase preserved through checkout/checkin. |

---

#### REQ-WF-015: Checked-in Requirement for Routing

**Requirement:** The CLI shall require documents to be checked in before routing.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_sop_lifecycle.py | test_routing_requires_checkin | Routing rejected for checked-out documents. |

---

### 5.4 Metadata Architecture (REQ-META)

#### REQ-META-001: Three-Tier Separation

**Requirement:** The CLI shall maintain strict separation between Tier 1 (Frontmatter), Tier 2 (.meta/), and Tier 3 (.audit/).

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_sop_lifecycle.py | test_sop_full_lifecycle | Three-tier separation verified throughout lifecycle. |

---

#### REQ-META-002: CLI-Exclusive Metadata Management

**Requirement:** The CLI shall be the sole mechanism for modifying .meta/ files.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_sop_lifecycle.py | test_sop_full_lifecycle | All metadata changes flow through CLI. |

---

#### REQ-META-003: Required Metadata Fields

**Requirement:** Each document's .meta/ file shall contain all required fields.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_sop_lifecycle.py | test_sop_full_lifecycle | Required metadata fields verified. |
| test_cr_lifecycle.py | test_cr_full_lifecycle | Required metadata fields verified. |
| test_sop_lifecycle.py | test_metadata_required_fields | All 8 required metadata fields explicitly verified. |

---

#### REQ-META-004: Execution Phase Tracking

**Requirement:** For executable documents, the CLI shall track execution phase in metadata.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_cr_lifecycle.py | test_cr_full_lifecycle | Execution phase tracking verified. |
| test_cr_lifecycle.py | test_execution_phase_preserved | Phase preserved through checkout/checkin. |

---

### 5.5 Audit Trail (REQ-AUDIT)

#### REQ-AUDIT-001: Append-Only Logging

**Requirement:** The CLI shall never modify or delete existing audit trail entries.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_sop_lifecycle.py | test_sop_full_lifecycle | Audit entries are appended, not modified. |
| test_sop_lifecycle.py | test_audit_immutability | Verifies audit trail is append-only and entries cannot be modified. |

---

#### REQ-AUDIT-002: Required Event Types

**Requirement:** The CLI shall log all required event types to the audit trail.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_sop_lifecycle.py | test_sop_full_lifecycle | Event types logged during lifecycle. |
| test_cr_lifecycle.py | test_cr_full_lifecycle | Event types logged during lifecycle. |
| test_queries.py | test_history_shows_all_event_types | All event types visible in history. |
| test_cr_lifecycle.py | test_all_audit_event_types | Verifies all 14 required audit event types are logged. |

---

#### REQ-AUDIT-003: Event Attribution

**Requirement:** Each audit event shall include timestamp, event type, user, and version.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_sop_lifecycle.py | test_sop_full_lifecycle | Event attribution verified. |

---

#### REQ-AUDIT-004: Comment Preservation

**Requirement:** Review comments shall be stored only in the audit trail.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_sop_lifecycle.py | test_sop_full_lifecycle | Comments stored in audit trail. |

---

### 5.6 Task & Inbox Management (REQ-TASK)

#### REQ-TASK-001: Task Generation on Routing

**Requirement:** When a document is routed, the CLI shall create task files in each assigned user's inbox.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_sop_lifecycle.py | test_sop_full_lifecycle | Task files created on routing. |

---

#### REQ-TASK-002: Task Content Requirements

**Requirement:** Generated task files shall include all required fields.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_sop_lifecycle.py | test_sop_full_lifecycle | Task content includes required fields. |
| test_sop_lifecycle.py | test_task_content_all_fields | Verifies all 7 required task fields: task_id, task_type, workflow_type, doc_id, version, assigned_by, assigned_date. |

---

#### REQ-TASK-003: Task Removal on Completion

**Requirement:** When a user completes an action, the CLI shall remove their task. Rejection clears all pending approval tasks.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_sop_lifecycle.py | test_sop_full_lifecycle | Task removed on completion. |
| test_sop_lifecycle.py | test_rejection_clears_approval_tasks | Rejection clears all pending approval tasks. |

---

#### REQ-TASK-004: Assign Command

**Requirement:** The CLI shall provide an `assign` command for quality group members.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_sop_lifecycle.py | test_assign_command | Quality members can add reviewers/approvers. |

---

### 5.7 Project Configuration (REQ-CFG)

#### REQ-CFG-001: Project Root Discovery

**Requirement:** The CLI shall discover the project root by searching for qms.config.json (preferred) or QMS/ directory (fallback).

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| conftest.py | temp_project fixture | Project root discovery via QMS/ directory (backward compatibility). |
| test_init.py | test_init_creates_complete_structure | Project root discovery via qms.config.json after init. |
| test_init.py | test_project_root_discovery_via_config | Verifies project root found via qms.config.json from subdirectory. |
| test_init.py | test_project_root_discovery_via_qms_fallback | Verifies fallback to QMS/ directory when no config file exists. |

---

#### REQ-CFG-002: QMS Root Path

**Requirement:** The CLI shall resolve the QMS document root as `{PROJECT_ROOT}/QMS/`.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_sop_lifecycle.py | test_sop_full_lifecycle | QMS root path resolution verified. |

---

#### REQ-CFG-003: Users Directory Path

**Requirement:** The CLI shall resolve the users directory as `{PROJECT_ROOT}/.claude/users/`.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_sop_lifecycle.py | test_sop_full_lifecycle | Users directory path verified. |

---

#### REQ-CFG-004: User Registry

**Requirement:** The CLI shall maintain a registry of valid users including group membership.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_security.py | test_unknown_user_rejection | User registry enforces known users. |
| test_security.py | test_user_group_classification | User registry tracks group membership. |

---

#### REQ-CFG-005: Document Type Registry

**Requirement:** The CLI shall maintain a registry of document types.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_document_types.py | test_create_sop | Document type registry for SOP. |
| test_document_types.py | test_create_cr | Document type registry for CR. |
| test_document_types.py | test_create_inv | Document type registry for INV. |
| test_document_types.py | test_document_type_registry | Verifies document type registry includes executable flag and parent type. |

---

### 5.8 Query Operations (REQ-QRY)

#### REQ-QRY-001: Document Reading

**Requirement:** The CLI shall provide the ability to read any document's content.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_queries.py | test_read_draft | Read the current draft version. |
| test_queries.py | test_read_effective | Read the effective version. |
| test_queries.py | test_read_archived_version | Read an archived version. |
| test_queries.py | test_read_draft_flag | Read draft explicitly when both exist. |

---

#### REQ-QRY-002: Document Status Query

**Requirement:** The CLI shall provide the ability to query a document's current workflow state.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_queries.py | test_status_query | Status query shows all required fields. |
| test_queries.py | test_status_shows_checked_out | Status shows checked_out status. |
| test_queries.py | test_status_shows_executable_field | Status query includes executable flag. |

---

#### REQ-QRY-003: Audit History Query

**Requirement:** The CLI shall provide the ability to retrieve the complete audit trail.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_queries.py | test_history_query | History shows all recorded events. |
| test_queries.py | test_history_shows_all_event_types | History includes all event types. |

---

#### REQ-QRY-004: Review Comments Query

**Requirement:** The CLI shall provide the ability to retrieve review comments.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_queries.py | test_comments_query | Comments query retrieves review comments. |
| test_queries.py | test_comments_includes_rejection | Comments includes rejection rationale. |

---

#### REQ-QRY-005: Inbox Query

**Requirement:** The CLI shall provide the ability to list pending tasks in a user's inbox.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_queries.py | test_inbox_query | Inbox lists pending tasks. |
| test_queries.py | test_inbox_multiple_tasks | Inbox shows multiple pending tasks. |
| test_queries.py | test_inbox_empty_when_no_tasks | Inbox works when empty. |

---

#### REQ-QRY-006: Workspace Query

**Requirement:** The CLI shall provide the ability to list documents checked out to a user's workspace.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_queries.py | test_workspace_query | Workspace lists checked out documents. |
| test_queries.py | test_workspace_multiple_documents | Workspace shows multiple documents. |
| test_queries.py | test_workspace_empty_after_checkin | Workspace empty after checkin. |

---

### 5.9 Prompt Generation (REQ-PROMPT)

#### REQ-PROMPT-001: Task Prompt Generation

**Requirement:** When creating task files, the CLI shall generate structured prompt content.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_prompts.py | test_review_task_prompt_generated | Review tasks include prompt content. |

---

#### REQ-PROMPT-002: YAML-Based Configuration

**Requirement:** Prompt content shall be configurable via external YAML files.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_prompts.py | test_prompts_directory_exists | Prompt YAML files exist in prompts/ directory. |

---

#### REQ-PROMPT-003: Hierarchical Prompt Lookup

**Requirement:** The CLI shall resolve prompt configuration using hierarchical lookup.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_prompts.py | test_prompts_have_workflow_phase_context | Prompt lookup follows hierarchy. |

---

#### REQ-PROMPT-004: Checklist Generation

**Requirement:** Review and approval prompts shall include a verification checklist.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_prompts.py | test_review_prompt_has_checklist | Prompts include verification checklist. |

---

#### REQ-PROMPT-005: Prompt Content Structure

**Requirement:** Generated prompts shall include header, checklist, reminders, and response format.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_prompts.py | test_prompt_has_required_sections | Prompts have required structure. |

---

#### REQ-PROMPT-006: Custom Sections

**Requirement:** Prompt configurations shall support custom sections.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_prompts.py | test_prompt_supports_custom_content | Custom sections included in prompts. |

---

### 5.10 Document Templates (REQ-TEMPLATE)

#### REQ-TEMPLATE-001: Template-Based Creation

**Requirement:** When creating a new document, the CLI shall populate it from a template.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_templates.py | test_new_document_uses_template | New documents use templates. |
| test_templates.py | test_cr_uses_cr_template | CR uses CR-specific template. |

---

#### REQ-TEMPLATE-002: Template Location

**Requirement:** Document templates shall be stored in `QMS/TEMPLATE/`.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_templates.py | test_templates_in_qms_template_directory | Templates in correct location. |

---

#### REQ-TEMPLATE-003: Variable Substitution

**Requirement:** Templates shall support variable placeholders that are substituted at creation.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_templates.py | test_title_substitution | {{TITLE}} is substituted. |
| test_templates.py | test_doc_id_substitution | {TYPE}-XXX is substituted. |

---

#### REQ-TEMPLATE-004: Frontmatter Initialization

**Requirement:** The CLI shall initialize new documents with valid YAML frontmatter.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_templates.py | test_frontmatter_title_initialized | Frontmatter includes title. |
| test_templates.py | test_frontmatter_revision_summary_initialized | Frontmatter includes revision_summary. |

---

#### REQ-TEMPLATE-005: Fallback Template Generation

**Requirement:** When no template exists, the CLI shall generate a minimal document structure.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_templates.py | test_document_created_without_template_file | Documents created without template. |
| test_templates.py | test_fallback_includes_document_heading | Fallback includes heading with ID. |

---

### 5.11 Project Initialization (REQ-INIT)

#### REQ-INIT-001: Config File Creation

**Requirement:** The `init` command shall create a `qms.config.json` file at the project root.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_init.py | test_init_creates_complete_structure | Verifies qms.config.json is created with required fields. |

---

#### REQ-INIT-002: QMS Directory Structure

**Requirement:** The `init` command shall create the complete QMS directory structure.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_init.py | test_init_creates_complete_structure | Verifies QMS/, SOP/, CR/, INV/, TEMPLATE/, .meta/, .audit/, .archive/ are created. |

---

#### REQ-INIT-003: User Directory Structure

**Requirement:** The `init` command shall create user directories for hardcoded administrators and default QA user.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_init.py | test_init_creates_complete_structure | Verifies workspace and inbox directories for administrators and QA. |

---

#### REQ-INIT-004: Default Agent Creation

**Requirement:** The `init` command shall create a default QA agent file.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_init.py | test_init_seeds_qa_agent | Verifies qa.md agent file is created with quality group. |

---

#### REQ-INIT-005: SOP Seeding

**Requirement:** The `init` command shall seed the QMS/SOP/ directory with sanitized SOPs.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_init.py | test_init_seeds_sops | Verifies SOPs are seeded with EFFECTIVE status and v1.0. |

---

#### REQ-INIT-006: Template Seeding

**Requirement:** The `init` command shall seed the QMS/TEMPLATE/ directory with document templates.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_init.py | test_init_seeds_templates | Verifies templates are seeded with EFFECTIVE status and v1.0. |

---

#### REQ-INIT-007: Safety Checks

**Requirement:** The `init` command shall abort if any target infrastructure already exists.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_init.py | test_init_blocked_by_existing_qms | Init blocked if QMS/ exists. |
| test_init.py | test_init_blocked_by_existing_users | Init blocked if .claude/users/ exists. |
| test_init.py | test_init_blocked_by_existing_qa_agent | Init blocked if qa.md exists. |
| test_init.py | test_init_blocked_by_existing_config | Init blocked if qms.config.json exists. |

---

#### REQ-INIT-008: Root Flag Support

**Requirement:** The `init` command shall accept an optional `--root` flag.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_init.py | test_init_with_root_flag | Init creates structure at specified root directory. |

---

### 5.12 User Management (REQ-USER)

#### REQ-USER-001: Hardcoded Administrators

**Requirement:** The users `lead` and `claude` shall be recognized as administrators without agent files.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_init.py | test_hardcoded_admins_work | Hardcoded administrators can execute commands without agent files. |

---

#### REQ-USER-002: Agent File-Based Group Assignment

**Requirement:** For non-hardcoded users, the CLI shall determine group from agent definition files.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_init.py | test_agent_group_assignment | Users with agent files are assigned correct groups. |

---

#### REQ-USER-003: User Add Command

**Requirement:** The CLI shall provide a `user --add` command that creates agent file and directories.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_init.py | test_user_add_creates_structure | User add creates agent file, workspace, and inbox. |
| test_init.py | test_user_add_requires_admin | User add requires administrator privileges. |

---

#### REQ-USER-004: Unknown User Handling

**Requirement:** Commands with unknown users shall be rejected with informative error messages.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_init.py | test_unknown_user_error | Unknown users receive helpful error guidance. |

---

#### REQ-USER-005: User List Command

**Requirement:** The CLI shall provide a `user --list` command.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_init.py | test_user_add_creates_structure | User list shows all recognized users. |
| test_init.py | test_user_list_command | Verifies user --list command displays users. |
| test_init.py | test_user_list_shows_groups | Verifies user list includes group assignments. |

---

### 5.13 MCP Server (REQ-MCP)

#### REQ-MCP-001: MCP Protocol Implementation

**Requirement:** The CLI shall provide an MCP (Model Context Protocol) server that exposes QMS operations as native tools for AI agents.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_mcp.py | test_mcp_server_imports | Verifies MCP server module imports correctly. |
| test_mcp.py | test_register_tools_creates_all_tools | Verifies all 19 MCP tools are registered. |

---

#### REQ-MCP-002: User Command Tools

**Requirement:** The MCP server shall expose user query tools: qms_inbox, qms_workspace, qms_status, qms_read, qms_history, and qms_comments.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_mcp.py | test_register_tools_creates_all_tools | Verifies all user command tools are registered. |
| test_mcp.py | test_qms_inbox_equivalence | Verifies qms_inbox produces equivalent output to CLI. |
| test_mcp.py | test_qms_workspace_equivalence | Verifies qms_workspace produces equivalent output to CLI. |
| test_mcp.py | test_qms_status_equivalence | Verifies qms_status produces equivalent output to CLI. |
| test_mcp.py | test_qms_read_equivalence | Verifies qms_read produces equivalent output to CLI. |
| test_mcp.py | test_qms_history_equivalence | Verifies qms_history produces equivalent output to CLI. |
| test_mcp.py | test_qms_comments_equivalence | Verifies qms_comments produces equivalent output to CLI. |
| test_mcp.py | test_full_sop_lifecycle_via_cli | Integration test exercising read and history tools. |

---

#### REQ-MCP-003: Document Lifecycle Tools

**Requirement:** The MCP server shall expose document lifecycle tools: qms_create, qms_checkout, qms_checkin, and qms_cancel.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_mcp.py | test_register_tools_creates_all_tools | Verifies all lifecycle tools are registered. |
| test_mcp.py | test_qms_create_equivalence | Verifies qms_create produces equivalent results to CLI. |
| test_mcp.py | test_qms_checkout_equivalence | Verifies qms_checkout produces equivalent results to CLI. |
| test_mcp.py | test_qms_checkin_equivalence | Verifies qms_checkin produces equivalent results to CLI. |
| test_mcp.py | test_qms_cancel_equivalence | Verifies qms_cancel produces equivalent results to CLI. |
| test_mcp.py | test_full_sop_lifecycle_via_cli | Integration test exercising create and checkin. |
| test_mcp.py | test_full_cr_lifecycle_via_cli | Integration test for executable document lifecycle. |

---

#### REQ-MCP-004: Workflow Tools

**Requirement:** The MCP server shall expose workflow tools: qms_route, qms_assign, qms_review, qms_approve, and qms_reject.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_mcp.py | test_register_tools_creates_all_tools | Verifies all workflow tools are registered. |
| test_mcp.py | test_qms_route_review_equivalence | Verifies qms_route for review produces equivalent results. |
| test_mcp.py | test_qms_route_approval_equivalence | Verifies qms_route for approval produces equivalent results. |
| test_mcp.py | test_qms_assign_equivalence | Verifies qms_assign produces equivalent results to CLI. |
| test_mcp.py | test_qms_review_equivalence | Verifies qms_review produces equivalent results to CLI. |
| test_mcp.py | test_qms_approve_equivalence | Verifies qms_approve produces equivalent results to CLI. |
| test_mcp.py | test_qms_reject_equivalence | Verifies qms_reject produces equivalent results to CLI. |
| test_mcp.py | test_full_sop_lifecycle_via_cli | Integration test exercising route, review, approve. |
| test_mcp.py | test_full_cr_lifecycle_via_cli | Integration test for executable workflow. |

---

#### REQ-MCP-005: Execution Tools

**Requirement:** The MCP server shall expose execution tools for executable documents: qms_release, qms_revert, and qms_close.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_mcp.py | test_register_tools_creates_all_tools | Verifies all execution tools are registered. |
| test_mcp.py | test_qms_release_equivalence | Verifies qms_release produces equivalent results to CLI. |
| test_mcp.py | test_qms_revert_equivalence | Verifies qms_revert produces equivalent results to CLI. |
| test_mcp.py | test_qms_close_equivalence | Verifies qms_close produces equivalent results to CLI. |
| test_mcp.py | test_full_cr_lifecycle_via_cli | Integration test exercising release and close. |

---

#### REQ-MCP-006: Administrative Tools

**Requirement:** The MCP server shall expose the qms_fix tool for administrative fixes on EFFECTIVE documents, with administrator-only access.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_mcp.py | test_register_tools_creates_all_tools | Verifies qms_fix tool is registered. |
| test_mcp.py | test_qms_fix_equivalence | Verifies qms_fix produces equivalent results to CLI. |
| test_mcp.py | test_qms_fix_requires_administrator | Verifies qms_fix enforces administrator-only access. |

---

#### REQ-MCP-007: Functional Equivalence

**Requirement:** Each MCP tool shall produce functionally equivalent results to the corresponding CLI command.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_mcp.py | test_qms_inbox_equivalence | CLI/MCP equivalence for inbox. |
| test_mcp.py | test_qms_workspace_equivalence | CLI/MCP equivalence for workspace. |
| test_mcp.py | test_qms_status_equivalence | CLI/MCP equivalence for status. |
| test_mcp.py | test_qms_read_equivalence | CLI/MCP equivalence for read. |
| test_mcp.py | test_qms_history_equivalence | CLI/MCP equivalence for history. |
| test_mcp.py | test_qms_comments_equivalence | CLI/MCP equivalence for comments. |
| test_mcp.py | test_qms_create_equivalence | CLI/MCP equivalence for create. |
| test_mcp.py | test_qms_checkout_equivalence | CLI/MCP equivalence for checkout. |
| test_mcp.py | test_qms_checkin_equivalence | CLI/MCP equivalence for checkin. |
| test_mcp.py | test_qms_cancel_equivalence | CLI/MCP equivalence for cancel. |
| test_mcp.py | test_qms_route_review_equivalence | CLI/MCP equivalence for route review. |
| test_mcp.py | test_qms_route_approval_equivalence | CLI/MCP equivalence for route approval. |
| test_mcp.py | test_qms_assign_equivalence | CLI/MCP equivalence for assign. |
| test_mcp.py | test_qms_review_equivalence | CLI/MCP equivalence for review. |
| test_mcp.py | test_qms_approve_equivalence | CLI/MCP equivalence for approve. |
| test_mcp.py | test_qms_reject_equivalence | CLI/MCP equivalence for reject. |
| test_mcp.py | test_qms_release_equivalence | CLI/MCP equivalence for release. |
| test_mcp.py | test_qms_revert_equivalence | CLI/MCP equivalence for revert. |
| test_mcp.py | test_qms_close_equivalence | CLI/MCP equivalence for close. |
| test_mcp.py | test_qms_fix_equivalence | CLI/MCP equivalence for fix. |
| test_mcp.py | test_full_sop_lifecycle_via_cli | Complete SOP lifecycle integration test. |
| test_mcp.py | test_full_cr_lifecycle_via_cli | Complete CR lifecycle integration test. |

---

#### REQ-MCP-008: Structured Responses

**Requirement:** MCP tools shall return structured responses containing success/failure status and result data.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_mcp.py | test_mcp_tool_returns_string | Verifies MCP tools return string responses. |

---

#### REQ-MCP-009: Permission Enforcement

**Requirement:** MCP tools shall enforce the same permission model as the CLI.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_mcp.py | test_qms_fix_requires_administrator | Verifies fix command requires administrator. |
| test_mcp.py | test_mcp_permission_enforcement | Verifies owner-only restrictions are enforced. |
| test_mcp.py | test_mcp_assign_requires_quality_group | Verifies assign requires quality group. |

---

#### REQ-MCP-010: Setup Command Exclusion

**Requirement:** Administrative setup commands (init, namespace, user, migrate) shall not be exposed as MCP tools.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_mcp.py | test_mcp_excludes_setup_commands | Verifies init, namespace, user, migrate are not exposed. |

---

## 6. Test Execution Summary

### 6.1 Qualified Baseline

| Attribute | Value |
|-----------|-------|
| Requirements Spec | SDLC-QMS-RS v3.0 |
| Repository | whharris917/qms-cli |
| Branch | cr-041-mcp |
| Commit | 46e3c91 |
| Total Tests | 142 |
| Passed | 142 |
| Failed | 0 |

### 6.2 Test Protocol Results

| Test Protocol | Tests | Passed | Failed |
|---------------|-------|--------|--------|
| test_sop_lifecycle.py | 16 | 16 | 0 |
| test_cr_lifecycle.py | 12 | 12 | 0 |
| test_security.py | 19 | 19 | 0 |
| test_document_types.py | 22 | 22 | 0 |
| test_queries.py | 18 | 18 | 0 |
| test_prompts.py | 7 | 7 | 0 |
| test_templates.py | 9 | 9 | 0 |
| test_init.py | 10 | 10 | 0 |
| test_mcp.py | 29 | 29 | 0 |
| **Total** | **142** | **142** | **0** |

### 6.3 Test Environment

- Tests executed via GitHub Actions CI on push to main branch
- All tests run in isolated temporary environments (no production QMS impact)
- CI provides independent, timestamped, immutable record of test results

---

## 7. References

- SDLC-QMS-RS: QMS CLI Requirements Specification
- SOP-007: Software Development Lifecycle

---

**END OF DOCUMENT**

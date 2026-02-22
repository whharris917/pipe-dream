---
title: QMS CLI Requirements Traceability Matrix
revision_summary: 'CR-095: Add REQ-DOC-018/019/020 (attachment lifecycle), REQ-INT-023/024/025
  (compiler enhancements); qualified baseline 31f8306 (cr-095 branch, 673 tests)'
---

# SDLC-QMS-RTM: QMS CLI Requirements Traceability Matrix

## 1. Purpose

This document provides traceability between the requirements specified in SDLC-QMS-RS v18.0 and the qualification tests that verify them. Each requirement is mapped to specific test protocols and functions where verification occurs.

---

## 2. Scope

This RTM covers all 139 requirements defined in SDLC-QMS-RS across the following domains:

- REQ-SEC (Security): 8 requirements
- REQ-DOC (Document Management): 20 requirements
- REQ-WF (Workflow): 23 requirements
- REQ-META (Metadata): 4 requirements
- REQ-AUDIT (Audit Trail): 4 requirements
- REQ-TASK (Task/Inbox): 4 requirements
- REQ-CFG (Configuration): 5 requirements
- REQ-QRY (Query Operations): 6 requirements
- REQ-PROMPT (Prompt Generation): 6 requirements
- REQ-TEMPLATE (Document Templates): 5 requirements
- REQ-INIT (Project Initialization): 8 requirements
- REQ-USER (User Management): 5 requirements
- REQ-MCP (MCP Server): 16 requirements
- REQ-INT (Interaction System): 25 requirements

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
| CR-048 Workflow | `qualification/test_cr048_workflow.py` | Status-aware checkout, withdraw, execution versioning |
| Security | `qualification/test_security.py` | Access control and authorization |
| Document Types | `qualification/test_document_types.py` | Creation, child documents, SDLC namespaces |
| Queries | `qualification/test_queries.py` | Read, status, history, inbox, workspace |
| Prompts | `qualification/test_prompts.py` | Prompt generation and configuration |
| Templates | `qualification/test_templates.py` | Template-based document creation |
| Init | `qualification/test_init.py` | Project initialization and user management |
| CR-087 Workflow | `qualification/test_cr087_workflow.py` | Checkout auto-withdraw (REQ-WF-022), route auto-checkin (REQ-WF-023) |
| Audit Completeness | `qualification/test_audit_completeness.py` | All 16 audit event types (REQ-AUDIT-002) |
| MCP | `qualification/test_mcp.py` | MCP server tools and functional equivalence |
| Interaction Parser | `test_interact_parser.py` | Template tag parsing, header, prompts, gates, loops |
| Interaction Source | `test_interact_source.py` | Source data model, session/source files, append-only responses |
| Interaction Engine | `test_interact_engine.py` | Engine behavior, cursor, sequential enforcement, interpolation |
| Interaction Compiler | `test_interact_compiler.py` | Compilation, tag stripping, amendment rendering, block rendering, auto-metadata |
| Interaction Integration | `test_interact_integration.py` | Checkout/checkin/read integration, atomic commits, MCP parity |
| Attachment Lifecycle | `test_attachment_lifecycle.py` | Attachment classification, terminal state guard, cascade close |

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
| REQ-DOC-001 | Supported Document Types | test_document_types::test_create_sop, test_create_cr, test_create_inv, test_create_er_under_tp, test_create_add_under_cr, test_create_vr_under_cr | PASS |
| REQ-DOC-002 | Child Document Relationships | test_document_types::test_create_tp_under_cr, test_create_var_under_cr, test_create_var_under_inv, test_create_add_under_inv, test_create_add_under_var, test_create_add_requires_parent, test_create_add_rejects_invalid_parent_type, test_create_vr_under_cr, test_create_vr_under_var, test_create_vr_under_add, test_vr_requires_parent, test_vr_rejects_invalid_parent_type | PASS |
| REQ-DOC-003 | QMS Folder Structure | test_sop_lifecycle::test_sop_full_lifecycle | PASS |
| REQ-DOC-004 | Sequential ID Generation | test_document_types::test_sequential_id_generation | PASS |
| REQ-DOC-005 | Child Document ID Generation | test_document_types::test_create_var_under_cr, test_child_id_generation, test_add_sequential_id_generation, test_create_vr_under_var, test_create_vr_under_add, test_vr_sequential_id_generation | PASS |
| REQ-DOC-006 | Version Format | test_sop_lifecycle::test_sop_full_lifecycle | PASS |
| REQ-DOC-007 | Checkout Behavior | test_sop_lifecycle::test_sop_full_lifecycle, test_document_types::test_checkout_effective_creates_archive | PASS |
| REQ-DOC-008 | Checkin Updates QMS | test_sop_lifecycle::test_sop_full_lifecycle | PASS |
| REQ-DOC-009 | Checkin Reverts Reviewed Status | test_sop_lifecycle::test_checkin_reverts_reviewed, test_cr_lifecycle::test_checkin_reverts_pre_reviewed, test_cr_lifecycle::test_checkin_reverts_post_reviewed | PASS |
| REQ-DOC-010 | Cancel Restrictions | test_document_types::test_cancel_v0_document, test_cancel_blocked_for_v1, test_cancel_blocked_while_checked_out, test_cancel_cleans_workspace_and_inbox | PASS |
| REQ-DOC-011 | Template Name-Based ID | test_document_types::test_template_name_based_id | PASS |
| REQ-DOC-012 | Folder-per-Document Storage | test_document_types::test_folder_per_document_cr, test_folder_per_document_inv, test_child_documents_in_parent_folder, test_create_add_under_cr | PASS |
| REQ-DOC-013 | SDLC Namespace Registration | test_document_types::test_sdlc_namespace_registration, test_sdlc_namespace_list | PASS |
| REQ-DOC-014 | SDLC Document Identification | test_document_types::test_sdlc_document_identification | PASS |
| REQ-DOC-015 | Addendum Parent State | test_document_types::test_create_add_requires_closed_parent, test_create_add_under_cr | PASS |
| REQ-DOC-016 | VR Parent State | test_document_types::test_create_vr_under_cr, test_vr_requires_in_execution_parent | PASS |
| REQ-DOC-017 | VR Initial Status | test_document_types::test_vr_born_in_execution | PASS |
| REQ-DOC-018 | Attachment Document Classification | test_attachment_lifecycle::test_vr_is_attachment, test_cr_not_attachment, test_sop_not_attachment, test_add_not_attachment, test_attachment_types_are_executable | PASS |
| REQ-DOC-019 | Terminal State Checkout Guard | test_attachment_lifecycle::test_closed_is_terminal, test_retired_is_terminal, test_draft_is_not_terminal, test_effective_is_not_terminal | PASS |
| REQ-DOC-020 | Cascade Close of Attachments | test_attachment_lifecycle::test_attachment_types_discoverable, test_vr_id_pattern_matches_parent, test_nested_parent_pattern, test_terminal_states_rejected, test_non_terminal_states_allowed, test_compile_from_source_data, test_compile_empty_source | PASS |
| REQ-WF-001 | Status Transition Validation | test_sop_lifecycle::test_invalid_transition, test_invalid_transitions_comprehensive | PASS |
| REQ-WF-002 | Non-Executable Document Lifecycle | test_sop_lifecycle::test_sop_full_lifecycle | PASS |
| REQ-WF-003 | Executable Document Lifecycle | test_cr_lifecycle::test_cr_full_lifecycle, test_document_types::test_vr_born_in_execution | PASS |
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
| REQ-WF-015 | Route Auto-Checkin for Owner | test_sop_lifecycle::test_routing_auto_checkin, test_cr087_workflow::test_route_auto_checkin_for_review, test_route_auto_checkin_blocked_for_non_owner, test_route_auto_checkin_for_sop, test_route_auto_checkin_workspace_cleaned | PASS |
| REQ-WF-016 | Pre-Release Revision | test_cr048_workflow::test_checkout_from_pre_approved_reverts_to_draft | PASS |
| REQ-WF-017 | Post-Review Continuation | test_cr048_workflow::test_checkout_from_post_reviewed_returns_to_execution | PASS |
| REQ-WF-018 | Withdraw Command | test_cr048_workflow::test_withdraw_from_in_review_returns_to_draft, test_withdraw_from_in_pre_review_returns_to_draft, test_withdraw_from_in_post_review_returns_to_execution, test_withdraw_only_allowed_for_responsible_user, test_withdraw_clears_assignees_and_inbox | PASS |
| REQ-WF-019 | Revert Command Deprecation | test_cr048_workflow::test_revert_shows_deprecation_warning | PASS |
| REQ-WF-020 | Effective Version Preservation | test_document_types::test_checkout_effective_creates_archive | PASS |
| REQ-WF-021 | Execution Version Tracking | test_cr048_workflow::test_execution_checkout_creates_minor_version, test_execution_checkin_archives_previous, test_closure_increments_major_version | PASS |
| REQ-WF-022 | Checkout Auto-Withdraw | test_cr087_workflow::test_checkout_auto_withdraws_from_in_pre_review, test_checkout_auto_withdraws_from_in_pre_approval, test_checkout_auto_withdraws_from_in_post_review, test_checkout_auto_withdraw_clears_inbox_tasks, test_checkout_auto_withdraw_blocked_for_non_owner, test_checkout_auto_withdraws_from_non_executable_in_review | PASS |
| REQ-WF-023 | Route Auto-Checkin | test_cr087_workflow::test_route_auto_checkin_for_review, test_route_auto_checkin_blocked_for_non_owner, test_route_auto_checkin_for_sop, test_route_auto_checkin_workspace_cleaned | PASS |
| REQ-META-001 | Three-Tier Separation | test_sop_lifecycle::test_sop_full_lifecycle | PASS |
| REQ-META-002 | CLI-Exclusive Metadata Management | test_sop_lifecycle::test_sop_full_lifecycle | PASS |
| REQ-META-003 | Required Metadata Fields | test_sop_lifecycle::test_sop_full_lifecycle, test_cr_lifecycle::test_cr_full_lifecycle, test_metadata_required_fields | PASS |
| REQ-META-004 | Execution Phase Tracking | test_cr_lifecycle::test_cr_full_lifecycle, test_execution_phase_preserved | PASS |
| REQ-AUDIT-001 | Append-Only Logging | test_sop_lifecycle::test_sop_full_lifecycle, test_audit_immutability | PASS |
| REQ-AUDIT-002 | Required Event Types | test_sop_lifecycle::test_sop_full_lifecycle, test_cr_lifecycle::test_cr_full_lifecycle, test_queries::test_history_shows_all_event_types, test_audit_completeness::test_all_audit_event_types, test_audit_completeness::test_audit_event_constants_match_requirement | PASS |
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
| REQ-MCP-004 | Workflow Tools | test_mcp::test_register_tools_creates_all_tools, test_qms_route_review_equivalence, test_qms_route_approval_equivalence, test_qms_assign_equivalence, test_qms_review_equivalence, test_qms_approve_equivalence, test_qms_reject_equivalence, test_qms_withdraw_equivalence, test_qms_review_mcp_layer_recommend, test_qms_review_mcp_layer_request_updates, test_qms_route_mcp_layer, test_qms_withdraw_mcp_layer, test_full_sop_lifecycle_via_cli, test_full_cr_lifecycle_via_cli | PASS |
| REQ-MCP-005 | Execution Tools | test_mcp::test_register_tools_creates_all_tools, test_qms_release_equivalence, test_qms_revert_equivalence, test_qms_close_equivalence, test_full_cr_lifecycle_via_cli | PASS |
| REQ-MCP-006 | Administrative Tools | test_mcp::test_register_tools_creates_all_tools, test_qms_fix_equivalence, test_qms_fix_requires_administrator | PASS |
| REQ-MCP-007 | Functional Equivalence | test_mcp::test_qms_inbox_equivalence, test_qms_workspace_equivalence, test_qms_status_equivalence, test_qms_read_equivalence, test_qms_history_equivalence, test_qms_comments_equivalence, test_qms_create_equivalence, test_qms_checkout_equivalence, test_qms_checkin_equivalence, test_qms_cancel_equivalence, test_qms_route_review_equivalence, test_qms_route_approval_equivalence, test_qms_assign_equivalence, test_qms_review_equivalence, test_qms_approve_equivalence, test_qms_reject_equivalence, test_qms_withdraw_equivalence, test_qms_review_mcp_layer_recommend, test_qms_review_mcp_layer_request_updates, test_qms_route_mcp_layer, test_qms_withdraw_mcp_layer, test_qms_release_equivalence, test_qms_revert_equivalence, test_qms_close_equivalence, test_qms_fix_equivalence, test_full_sop_lifecycle_via_cli, test_full_cr_lifecycle_via_cli | PASS |
| REQ-MCP-008 | Structured Responses | test_mcp::test_mcp_tool_returns_string | PASS |
| REQ-MCP-009 | Permission Enforcement | test_mcp::test_qms_fix_requires_administrator, test_mcp_permission_enforcement, test_mcp_assign_requires_quality_group | PASS |
| REQ-MCP-010 | Setup Command Exclusion | test_mcp::test_mcp_excludes_setup_commands | PASS |
| REQ-MCP-011 | Remote Transport Support | test_mcp::test_mcp_cli_args_sse_transport, test_mcp_transport_choices, test_mcp_sse_transport_configuration, test_mcp_sse_transport_security_allows_docker, test_mcp_streamable_http_transport_configuration, test_mcp_streamable_http_transport_security_allows_docker | PASS |
| REQ-MCP-012 | Transport CLI Configuration | test_mcp::test_mcp_cli_args_default, test_mcp_cli_args_sse_transport, test_mcp_cli_args_host_port, test_mcp_transport_choices, test_mcp_sse_transport_configuration, test_mcp_streamable_http_cli_args | PASS |
| REQ-MCP-013 | Project Root Configuration | test_mcp::test_mcp_cli_args_project_root, test_mcp_project_root_env_var, test_mcp_project_root_env_var_invalid | PASS |
| REQ-MCP-014 | Streamable-HTTP Transport | test_mcp::test_mcp_streamable_http_transport_configuration, test_mcp_streamable_http_transport_security_allows_docker, test_mcp_streamable_http_cli_args, test_mcp_streamable_http_is_recommended_over_sse | PASS |
| REQ-MCP-015 | Header-Based Identity Resolution | test_mcp::test_resolve_identity_missing_user_raises_error, test_resolve_identity_empty_user_raises_error, test_resolve_identity_stdio_mode_custom_user, test_resolve_identity_http_header_enforced, test_resolve_identity_enforced_mode_mismatch_raises_error, test_resolve_identity_enforced_mode_match_succeeds, test_resolve_identity_mismatch_error_message_helpful, test_resolve_identity_http_no_header_trusted_mode, test_resolve_identity_unknown_agent_still_resolves, test_known_agents_set, test_resolve_identity_non_starlette_context_uses_trusted_mode, test_resolve_identity_tools_receive_resolved_identity | PASS |
| REQ-MCP-016 | Identity Collision Prevention | test_mcp::test_identity_collision_exception_class, test_identity_lock_ttl_constant, test_identity_collision_enforced_locks_trusted, test_identity_collision_enforced_locks_stdio_mode, test_identity_collision_error_message_terminal, test_identity_lock_ttl_expiry, test_identity_lock_heartbeat_refreshes, test_identity_collision_different_identities_ok, test_identity_collision_trusted_mode_does_not_lock, test_identity_collision_duplicate_container, test_identity_collision_same_instance_heartbeat, test_identity_collision_duplicate_after_ttl, test_identity_registry_cleanup, test_identity_lock_empty_instance_id, test_identity_collision_tool_returns_error | PASS |
| REQ-INT-001 | Tag Vocabulary | test_interact_parser::test_recognizes_prompt_tag, test_recognizes_gate_tag, test_recognizes_loop_tags, test_recognizes_end_tag, test_tags_must_be_html_comments, test_all_five_tags_in_one_template, test_end_prompt_recognized_as_tag, test_guidance_stops_at_end_prompt, test_guidance_without_end_prompt_includes_scaffold, test_end_prompt_with_gate, test_end_prompt_stripped_from_vr_template, test_all_vr_prompts_have_guidance | PASS |
| REQ-INT-002 | Template Header | test_interact_parser::test_parses_template_name, test_parses_template_version, test_parses_start_prompt, test_missing_name_raises, test_missing_start_raises, test_missing_header_raises, test_multiline_header_comment | PASS |
| REQ-INT-003 | Prompt Attributes | test_interact_parser::test_prompt_has_id, test_prompt_has_next, test_prompt_commit_defaults_false, test_prompt_commit_true, test_prompt_missing_id_raises, test_prompt_missing_next_raises, test_prompt_has_guidance | PASS |
| REQ-INT-004 | Gate Attributes | test_interact_parser::test_gate_has_id, test_gate_has_type, test_gate_has_yes_target, test_gate_has_no_target, test_gate_missing_targets_raises, test_gate_missing_id_raises | PASS |
| REQ-INT-005 | Loop Semantics | test_interact_parser::test_loop_defined_by_pair, test_loop_tracks_first_prompt, test_prompts_inside_loop_marked, test_prompts_outside_loop_not_marked, test_gate_inside_loop_marked, test_unclosed_loop_raises, test_mismatched_end_loop_raises | PASS |
| REQ-INT-006 | Source File Structure | test_interact_source::test_create_source_has_doc_id, test_create_source_has_template_reference, test_create_source_has_cursor, test_create_source_has_responses, test_create_source_has_loops, test_create_source_has_gates, test_create_source_has_metadata, test_create_source_default_metadata, test_source_serializes_to_json | PASS |
| REQ-INT-007 | Session File Lifecycle | test_interact_source::test_save_and_load_session, test_save_and_load_source, test_load_nonexistent_session_returns_none, test_load_nonexistent_source_returns_none, test_session_creates_parent_dirs, test_source_creates_parent_dirs, test_session_file_is_valid_json; test_interact_integration::test_checkout_creates_interact_session, test_checkin_stores_source_json, test_checkin_removes_interact_session | PASS |
| REQ-INT-008 | Append-Only Responses | test_interact_source::test_response_entry_has_value, test_response_entry_has_author, test_response_entry_has_timestamp, test_response_entry_optional_reason, test_response_entry_no_reason_by_default, test_response_entry_optional_commit, test_response_entry_no_commit_by_default, test_responses_stored_as_list, test_append_only_multiple_entries, test_get_active_response_returns_last | PASS |
| REQ-INT-009 | Amendment Trail | test_interact_source::test_amendment_preserves_original, test_amendment_has_reason, test_original_entry_has_no_reason, test_multiple_amendments_all_preserved; test_interact_compiler::test_amendment_shows_strikethrough_on_original, test_multiple_amendments_all_superseded_struck, test_compiled_document_shows_amendments | PASS |
| REQ-INT-010 | Interact Entry Point | test_interact_engine::test_shows_current_prompt_id, test_shows_guidance_text, test_shows_awaiting_response_status, test_shows_complete_when_done, test_shows_commit_flag, test_shows_gate_type, test_shows_loop_context | PASS |
| REQ-INT-011 | Response Flags | test_interact_engine::test_respond_records_value, test_respond_advances_cursor, test_respond_returns_next_prompt_info, test_respond_on_complete_raises; test_interact_integration::test_cli_interact_has_all_flags | PASS |
| REQ-INT-012 | Navigation Flags | test_interact_engine::test_goto_navigates_to_previous_prompt, test_goto_requires_reason, test_goto_to_unanswered_raises, test_goto_amendment_mode, test_goto_amendment_returns_to_original, test_cancel_goto, test_cancel_goto_no_active_raises, test_reopen_loop, test_reopen_requires_reason, test_reopen_nonclosed_raises | PASS |
| REQ-INT-013 | Query Flags | test_interact_engine::test_progress_shows_all_prompts, test_progress_shows_filled_status, test_progress_shows_commit_prompts, test_progress_shows_loop_iterations; test_interact_compiler::test_compile_preview_matches_compile_document | PASS |
| REQ-INT-014 | Sequential Enforcement | test_interact_engine::test_cannot_skip_prompts, test_cursor_at_correct_start, test_cursor_advances_sequentially, test_respond_on_gate_raises_if_not_gate, test_respond_on_prompt_raises_if_gate | PASS |
| REQ-INT-015 | Contextual Interpolation | test_interact_engine::test_interpolates_previous_response, test_unresolved_placeholder_left_intact, test_interpolates_metadata, test_interpolates_loop_counter | PASS |
| REQ-INT-016 | Compilation | test_interact_compiler::test_strips_template_header, test_strips_prompt_tags, test_strips_guidance_text, test_substitutes_placeholders, test_preserves_markdown_structure, test_substitutes_metadata, test_empty_responses_leave_blank, test_vr_compiles_with_filled_responses, test_vr_compiles_empty_gracefully, test_template_fm_removed, test_document_fm_kept, test_notice_stripped, test_single_fm_preserved, test_compiled_output_has_one_fm, test_real_template_preamble_stripped, test_table_rows_no_attribution, test_table_row_single_line, test_table_amendment_active_only, test_loop_bold_not_broken, test_loop_attribution_outside_code_fence, test_guidance_stripped_before_end_prompt, test_scaffold_preserved_after_end_prompt, test_end_prompt_tag_stripped_from_output, test_fallback_without_end_prompt, test_block_context_wrapped, test_block_context_attribution_in_blockquote, test_label_context_not_wrapped, test_table_context_not_wrapped, test_empty_block_not_wrapped | PASS |
| REQ-INT-017 | Interactive Checkout | test_interact_integration::test_checkout_creates_interact_session, test_checkout_seeds_from_source_json, test_checkout_creates_placeholder_md | PASS |
| REQ-INT-018 | Interactive Checkin | test_interact_integration::test_checkin_compiles_to_markdown, test_checkin_stores_source_json, test_checkin_removes_interact_session | PASS |
| REQ-INT-019 | Source-Aware Read | test_interact_integration::test_read_compiles_from_session, test_read_compiles_from_source_json, test_read_falls_back_to_standard_for_non_interactive | PASS |
| REQ-INT-020 | Engine-Managed Commits | test_interact_integration::test_commit_message_format, test_commit_hash_recorded_in_response, test_engine_commit_function_exists, test_engine_commit_returns_empty_on_no_project_root, test_engine_commit_in_git_repo | PASS |
| REQ-INT-021 | Commit Staging Scope | test_interact_integration::test_stages_all_changes, test_no_commit_when_no_changes | PASS |
| REQ-INT-022 | MCP Interact Tool | test_interact_integration::test_mcp_tools_module_has_qms_interact, test_mcp_interact_has_respond_param, test_mcp_interact_has_file_param, test_mcp_interact_has_reason_param, test_mcp_interact_has_goto_param, test_mcp_interact_has_cancel_goto_param, test_mcp_interact_has_reopen_param, test_mcp_interact_has_progress_param, test_mcp_interact_has_compile_param, test_mcp_interact_calls_interact_command, test_cli_interact_command_registered, test_cli_interact_has_all_flags, test_interact_registered_in_command_registry, test_interact_requires_doc_id, test_new_modules_import_cleanly | PASS |
| REQ-INT-023 | Auto-Generated Metadata | test_interact_compiler::test_auto_date_from_earliest_timestamp, test_auto_performer_from_authors, test_auto_performed_date_from_latest_timestamp, test_explicit_metadata_not_overwritten, test_no_responses_no_auto_metadata, test_auto_metadata_in_compilation | PASS |
| REQ-INT-024 | Block Rendering | test_interact_compiler::test_standalone_response_blockquoted, test_attribution_below_blockquote, test_label_context_also_block_rendered, test_table_context_not_wrapped, test_empty_block_not_wrapped | PASS |
| REQ-INT-025 | Step Subsection Numbering | test_interact_compiler::test_step_subsection_headings, test_step_expected_blockquoted, test_step_actual_code_fenced | PASS |

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
| test_document_types.py | test_create_add_under_cr | Create ADD document type as child of CLOSED CR. |
| test_document_types.py | test_create_vr_under_cr | Create VR document type as child of IN_EXECUTION CR. |

---

#### REQ-DOC-002: Child Document Relationships

**Requirement:** The CLI shall enforce parent-child relationships: TP is a child of CR; ER is a child of TP; VAR is a child of CR or INV; ADD is a child of CR, INV, VAR, or ADD; VR is a child of CR, VAR, or ADD.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_document_types.py | test_create_tp_under_cr | TP is created as a child of CR. |
| test_document_types.py | test_create_var_under_cr | VAR is created as a child of CR. |
| test_document_types.py | test_create_var_under_inv | VAR can also be created as a child of INV. |
| test_document_types.py | test_create_add_under_inv | ADD is created as a child of CLOSED INV. |
| test_document_types.py | test_create_add_under_var | ADD is created as a child of CLOSED VAR. |
| test_document_types.py | test_create_add_requires_parent | ADD creation requires --parent flag. |
| test_document_types.py | test_create_add_rejects_invalid_parent_type | ADD rejects invalid parent types (e.g., TP). |
| test_document_types.py | test_create_vr_under_cr | VR is created as a child of IN_EXECUTION CR. |
| test_document_types.py | test_create_vr_under_var | VR is created as a child of IN_EXECUTION VAR. |
| test_document_types.py | test_create_vr_under_add | VR is created as a child of IN_EXECUTION ADD. |
| test_document_types.py | test_vr_requires_parent | VR creation requires --parent flag. |
| test_document_types.py | test_vr_rejects_invalid_parent_type | VR rejects invalid parent types (e.g., TP). |

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
| test_document_types.py | test_add_sequential_id_generation | ADD IDs generated sequentially (ADD-001, ADD-002, ADD-003). |
| test_document_types.py | test_create_vr_under_var | VR ID follows nested format (CR-001-VAR-001-VR-001). |
| test_document_types.py | test_create_vr_under_add | VR ID follows nested format (CR-001-ADD-001-VR-001). |
| test_document_types.py | test_vr_sequential_id_generation | VR IDs generated sequentially (VR-001, VR-002, VR-003). |

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
| test_document_types.py | test_create_add_under_cr | ADD stored in parent CR's folder. |

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

#### REQ-DOC-015: Addendum Parent State

**Requirement:** ADD documents shall only be created against parents in CLOSED state. The CLI shall reject ADD creation when the parent is not CLOSED.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_document_types.py | test_create_add_requires_closed_parent | ADD creation rejected when parent is not CLOSED. |
| test_document_types.py | test_create_add_under_cr | ADD successfully created when parent CR is CLOSED. |

---

#### REQ-DOC-016: VR Parent State

**Requirement:** VR documents shall only be created against parents in IN_EXECUTION state. The CLI shall reject VR creation when the parent is not IN_EXECUTION.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_document_types.py | test_create_vr_under_cr | VR successfully created when parent CR is IN_EXECUTION. |
| test_document_types.py | test_vr_requires_in_execution_parent | VR creation rejected when parent is not IN_EXECUTION. |

---

#### REQ-DOC-017: VR Initial Status

**Requirement:** VR documents shall be created with initial status IN_EXECUTION at version 1.0 with execution_phase set to post_release. The approved VR template serves as the pre-approval authority (batch record model).

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_document_types.py | test_vr_born_in_execution | VR created with status IN_EXECUTION, version 1.0, execution_phase post_release, checked out. |

---

#### REQ-DOC-018: Attachment Document Classification

**Requirement:** Document types may be classified as attachments via the `attachment` property in the DOCUMENT_TYPES registry. VR is an attachment type.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_attachment_lifecycle.py | test_vr_is_attachment | VR document type has attachment: True. |
| test_attachment_lifecycle.py | test_cr_not_attachment | CR is not classified as an attachment. |
| test_attachment_lifecycle.py | test_sop_not_attachment | SOP is not classified as an attachment. |
| test_attachment_lifecycle.py | test_add_not_attachment | ADD is not classified as an attachment. |
| test_attachment_lifecycle.py | test_attachment_types_are_executable | All attachment types are also executable. |

---

#### REQ-DOC-019: Terminal State Checkout Guard

**Requirement:** The CLI shall reject checkout of documents in terminal states (CLOSED, RETIRED).

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_attachment_lifecycle.py | test_closed_is_terminal | CLOSED is recognized as a terminal state. |
| test_attachment_lifecycle.py | test_retired_is_terminal | RETIRED is recognized as a terminal state. |
| test_attachment_lifecycle.py | test_draft_is_not_terminal | DRAFT is not a terminal state. |
| test_attachment_lifecycle.py | test_effective_is_not_terminal | EFFECTIVE is not a terminal state. |

---

#### REQ-DOC-020: Cascade Close of Attachments

**Requirement:** When a parent document is closed, the CLI shall automatically close all child attachment documents not in a terminal state, auto-compiling interactive attachments if needed.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_attachment_lifecycle.py | test_attachment_types_discoverable | Attachment types can be discovered from DOCUMENT_TYPES registry. |
| test_attachment_lifecycle.py | test_vr_id_pattern_matches_parent | VR IDs match parent document pattern for cascade discovery. |
| test_attachment_lifecycle.py | test_nested_parent_pattern | Nested parent patterns (e.g., CR-001-VAR-001-VR-001) match correctly. |
| test_attachment_lifecycle.py | test_terminal_states_rejected | Attachments in terminal states are skipped during cascade close. |
| test_attachment_lifecycle.py | test_non_terminal_states_allowed | Attachments in non-terminal states are eligible for cascade close. |
| test_attachment_lifecycle.py | test_compile_from_source_data | Auto-compilation produces valid markdown from source data. |
| test_attachment_lifecycle.py | test_compile_empty_source | Auto-compilation handles empty source gracefully. |

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

**Requirement:** Non-executable documents shall follow: DRAFT -> IN_REVIEW -> REVIEWED -> IN_APPROVAL -> APPROVED -> EFFECTIVE.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_sop_lifecycle.py | test_sop_full_lifecycle | Complete non-executable lifecycle verification. |

---

#### REQ-WF-003: Executable Document Lifecycle

**Requirement:** Executable documents (CR, INV, TP, ER, VAR, ADD, VR) shall follow the dual review/approval cycle with execution phase. VR documents enter at IN_EXECUTION per REQ-DOC-017.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_cr_lifecycle.py | test_cr_full_lifecycle | Complete executable lifecycle verification. |
| test_document_types.py | test_vr_born_in_execution | VR enters executable lifecycle at IN_EXECUTION v1.0. |

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

#### REQ-WF-015: Route Auto-Checkin for Owner

**Requirement:** When the document owner routes a checked-out document for review or approval, the CLI shall auto-checkin the document first (per REQ-WF-023), then proceed with routing. If the document is checked out by a different user, routing shall be rejected.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_sop_lifecycle.py | test_routing_auto_checkin | Routing a checked-out document auto-checks-in and succeeds. |
| test_cr087_workflow.py | test_route_auto_checkin_for_review | Auto-checkin during route for review, verifies CHECKIN audit event. |
| test_cr087_workflow.py | test_route_auto_checkin_blocked_for_non_owner | Non-owner cannot route checked-out document. |
| test_cr087_workflow.py | test_route_auto_checkin_for_sop | Auto-checkin works for non-executable (SOP) documents. |
| test_cr087_workflow.py | test_route_auto_checkin_workspace_cleaned | Workspace copy removed after auto-checkin. |

---

#### REQ-WF-016: Pre-Release Revision

**Requirement:** When a document in PRE_APPROVED status is checked out, the CLI shall: (1) transition status to DRAFT, (2) clear all pre-review/pre-approval tracking fields (pending_assignees, completed_reviewers, review_outcomes), and (3) copy the document to the user workspace. This allows scope revision through re-review before execution begins.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_cr048_workflow.py | test_checkout_from_pre_approved_reverts_to_draft | Verifies PRE_APPROVED checkout transitions to DRAFT and clears tracking fields. |

---

#### REQ-WF-017: Post-Review Continuation

**Requirement:** When a document in POST_REVIEWED status is checked out, the CLI shall: (1) transition status to IN_EXECUTION, (2) clear all post-review tracking fields, and (3) copy the document to the user workspace. This allows continued execution work without an intermediate DRAFT state.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_cr048_workflow.py | test_checkout_from_post_reviewed_returns_to_execution | Verifies POST_REVIEWED checkout transitions to IN_EXECUTION. |

---

#### REQ-WF-018: Withdraw Command

**Requirement:** The CLI shall provide a `withdraw` command that allows the responsible user to abort an in-progress review or approval workflow. Withdraw shall: (1) transition from IN_REVIEW to DRAFT, IN_APPROVAL to REVIEWED, IN_PRE_REVIEW to DRAFT, IN_PRE_APPROVAL to PRE_REVIEWED, IN_POST_REVIEW to IN_EXECUTION, IN_POST_APPROVAL to POST_REVIEWED; (2) clear pending_assignees and remove related inbox tasks; and (3) log a WITHDRAW event to the audit trail. Only the responsible_user may withdraw.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_cr048_workflow.py | test_withdraw_from_in_review_returns_to_draft | Verifies IN_REVIEW withdraw transitions to DRAFT. |
| test_cr048_workflow.py | test_withdraw_from_in_pre_review_returns_to_draft | Verifies IN_PRE_REVIEW withdraw transitions to DRAFT. |
| test_cr048_workflow.py | test_withdraw_from_in_post_review_returns_to_execution | Verifies IN_POST_REVIEW withdraw transitions to IN_EXECUTION. |
| test_cr048_workflow.py | test_withdraw_only_allowed_for_responsible_user | Verifies only document owner can withdraw. |
| test_cr048_workflow.py | test_withdraw_clears_assignees_and_inbox | Verifies withdraw clears pending_assignees and removes inbox tasks. |

---

#### REQ-WF-019: Revert Command Deprecation

**Requirement:** The `revert` command is deprecated. When invoked, the CLI shall print a deprecation warning recommending checkout from POST_REVIEWED as the preferred alternative. The command shall remain functional for backward compatibility.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_cr048_workflow.py | test_revert_shows_deprecation_warning | Verifies revert command shows deprecation warning. |

---

#### REQ-WF-020: Effective Version Preservation

**Requirement:** When a non-executable document in EFFECTIVE status is checked out, the CLI shall: (1) keep the effective version (N.0) in the QMS directory (still "in force"), (2) create a new draft version (N.1) in the QMS directory, and (3) copy N.1 to user workspace. The effective version shall NOT be archived on checkout; archival occurs on approval per REQ-WF-006.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_document_types.py | test_checkout_effective_creates_archive | Verifies checkout of EFFECTIVE creates N.1 draft without archiving N.0. |

---

#### REQ-WF-021: Execution Version Tracking

**Requirement:** During execution of an executable document: (1) release creates version N.0 in IN_EXECUTION status; (2) first checkout creates N.1 in workspace while N.0 remains current in QMS; (3) first checkin archives N.0 and commits N.1 as current IN_EXECUTION version; (4) subsequent checkout creates N.(X+1) in workspace while N.X remains current; (5) subsequent checkin archives N.X and commits N.(X+1); (6) closure transitions to (N+1).0 POST_APPROVED then CLOSED. Archive on commit (checkin), not on checkout.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_cr048_workflow.py | test_execution_checkout_creates_minor_version | Verifies checkout during IN_EXECUTION increments minor version. |
| test_cr048_workflow.py | test_execution_checkin_archives_previous | Verifies checkin during IN_EXECUTION archives previous version. |
| test_cr048_workflow.py | test_closure_increments_major_version | Verifies closure transitions to (N+1).0 POST_APPROVED then CLOSED. |

---

#### REQ-WF-022: Checkout Auto-Withdraw

**Requirement:** When a document in an active workflow state (IN_REVIEW, IN_APPROVAL, IN_PRE_REVIEW, IN_PRE_APPROVAL, IN_POST_REVIEW, IN_POST_APPROVAL) is checked out by the responsible user, the CLI shall first withdraw the document (per REQ-WF-018 transitions), then proceed with checkout. Non-owners shall be rejected.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_cr087_workflow.py | test_checkout_auto_withdraws_from_in_pre_review | Auto-withdraw from IN_PRE_REVIEW to DRAFT, then checkout. |
| test_cr087_workflow.py | test_checkout_auto_withdraws_from_in_pre_approval | Auto-withdraw from IN_PRE_APPROVAL to PRE_REVIEWED, then checkout. |
| test_cr087_workflow.py | test_checkout_auto_withdraws_from_in_post_review | Auto-withdraw from IN_POST_REVIEW to IN_EXECUTION, then checkout. |
| test_cr087_workflow.py | test_checkout_auto_withdraw_clears_inbox_tasks | Auto-withdraw clears all inbox tasks for assignees. |
| test_cr087_workflow.py | test_checkout_auto_withdraw_blocked_for_non_owner | Non-owner checkout from active workflow state is rejected. |
| test_cr087_workflow.py | test_checkout_auto_withdraws_from_non_executable_in_review | Auto-withdraw works for non-executable documents (SOP IN_REVIEW). |

---

#### REQ-WF-023: Route Auto-Checkin

**Requirement:** When a checked-out document is routed for review or approval by the responsible user, the CLI shall first check in the document, then proceed with routing. If checked out by a different user, routing shall be rejected.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_cr087_workflow.py | test_route_auto_checkin_for_review | Auto-checkin during route for review, verifies CHECKIN audit event. |
| test_cr087_workflow.py | test_route_auto_checkin_blocked_for_non_owner | Non-owner cannot route checked-out document. |
| test_cr087_workflow.py | test_route_auto_checkin_for_sop | Auto-checkin works for non-executable (SOP) documents. |
| test_cr087_workflow.py | test_route_auto_checkin_workspace_cleaned | Workspace copy removed after auto-checkin during route. |

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

**Requirement:** The CLI shall log all 16 required event types to the audit trail: CREATE, CHECKOUT, CHECKIN, ROUTE_REVIEW, ROUTE_APPROVAL, ASSIGN, REVIEW, APPROVE, REJECT, EFFECTIVE, RELEASE, REVERT, CLOSE, RETIRE, STATUS_CHANGE, WITHDRAW.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_sop_lifecycle.py | test_sop_full_lifecycle | Event types logged during lifecycle. |
| test_cr_lifecycle.py | test_cr_full_lifecycle | Event types logged during lifecycle. |
| test_queries.py | test_history_shows_all_event_types | All event types visible in history. |
| test_audit_completeness.py | test_all_audit_event_types | Comprehensive lifecycle verifying all 16 required audit event types are logged (SOP for EFFECTIVE/RETIRE, CR for ASSIGN/WITHDRAW/REJECT/RELEASE/REVERT/CLOSE). |
| test_audit_completeness.py | test_audit_event_constants_match_requirement | Verifies qms_audit module defines exactly the 16 EVENT_* constants per REQ-AUDIT-002. |

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
| test_mcp.py | test_register_tools_creates_all_tools | Verifies all 20 MCP tools are registered. |

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

**Requirement:** The MCP server shall expose workflow tools: qms_route, qms_assign, qms_review, qms_approve, qms_reject, and qms_withdraw.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_mcp.py | test_register_tools_creates_all_tools | Verifies all 20 workflow tools are registered. |
| test_mcp.py | test_qms_route_review_equivalence | Verifies qms_route for review produces equivalent results. |
| test_mcp.py | test_qms_route_approval_equivalence | Verifies qms_route for approval produces equivalent results. |
| test_mcp.py | test_qms_assign_equivalence | Verifies qms_assign produces equivalent results to CLI. |
| test_mcp.py | test_qms_review_equivalence | Verifies qms_review produces equivalent results to CLI. |
| test_mcp.py | test_qms_approve_equivalence | Verifies qms_approve produces equivalent results to CLI. |
| test_mcp.py | test_qms_reject_equivalence | Verifies qms_reject produces equivalent results to CLI. |
| test_mcp.py | test_qms_withdraw_equivalence | Verifies qms_withdraw produces equivalent results to CLI. |
| test_mcp.py | test_qms_review_mcp_layer_recommend | Verifies qms_review MCP-to-CLI arg mapping for recommend outcome. |
| test_mcp.py | test_qms_review_mcp_layer_request_updates | Verifies qms_review MCP-to-CLI arg mapping for request-updates outcome. |
| test_mcp.py | test_qms_route_mcp_layer | Verifies qms_route MCP-to-CLI arg mapping for review/approval. |
| test_mcp.py | test_qms_withdraw_mcp_layer | Verifies qms_withdraw MCP-to-CLI arg mapping. |
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
| test_mcp.py | test_qms_withdraw_equivalence | CLI/MCP equivalence for withdraw. |
| test_mcp.py | test_qms_review_mcp_layer_recommend | MCP-to-CLI arg mapping for review recommend. |
| test_mcp.py | test_qms_review_mcp_layer_request_updates | MCP-to-CLI arg mapping for review request-updates. |
| test_mcp.py | test_qms_route_mcp_layer | MCP-to-CLI arg mapping for route types. |
| test_mcp.py | test_qms_withdraw_mcp_layer | MCP-to-CLI arg mapping for withdraw. |
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

### 5.14 Remote Transport and Identity (REQ-MCP-011 through REQ-MCP-016)

#### REQ-MCP-011: Remote Transport Support

**Requirement:** The MCP server shall support SSE (Server-Sent Events) transport in addition to stdio, enabling remote connections from containerized Claude agents.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_mcp.py | test_mcp_cli_args_sse_transport | Verifies --transport sse is accepted and parsed correctly. |
| test_mcp.py | test_mcp_transport_choices | Verifies transport argument accepts only valid choices (stdio, sse). |
| test_mcp.py | test_mcp_sse_transport_configuration | Verifies mcp.settings.host/port can be configured for SSE transport. |
| test_mcp.py | test_mcp_sse_transport_security_allows_docker | Verifies transport security settings allow container connections. |

---

#### REQ-MCP-012: Transport CLI Configuration

**Requirement:** The MCP server shall accept CLI arguments --transport (stdio|sse), --host, and --port for configuring transport mode and binding address.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_mcp.py | test_mcp_cli_args_default | Verifies default transport is stdio, host is 127.0.0.1, port is 8000. |
| test_mcp.py | test_mcp_cli_args_sse_transport | Verifies --transport sse argument is parsed correctly. |
| test_mcp.py | test_mcp_cli_args_host_port | Verifies --host and --port arguments are parsed correctly. |
| test_mcp.py | test_mcp_transport_choices | Verifies transport argument validates choices. |
| test_mcp.py | test_mcp_sse_transport_configuration | Verifies SSE settings (host/port) are applied to mcp.settings before run(). |

---

#### REQ-MCP-013: Project Root Configuration

**Requirement:** The MCP server shall support project root configuration via --project-root CLI argument or QMS_PROJECT_ROOT environment variable, falling back to directory walking.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_mcp.py | test_mcp_cli_args_project_root | Verifies --project-root argument is parsed correctly. |
| test_mcp.py | test_mcp_project_root_env_var | Verifies QMS_PROJECT_ROOT env var is respected when valid. |
| test_mcp.py | test_mcp_project_root_env_var_invalid | Verifies invalid env var falls back to directory walking. |

---

#### REQ-MCP-014: Streamable-HTTP Transport

**Requirement:** When configured for streamable-http transport, the MCP server shall: (1) bind to the specified host and port, (2) expose the MCP endpoint at /mcp, (3) allow connections from host.docker.internal for Docker container access, and (4) support the standard MCP streamable-http protocol as the recommended transport for remote connections.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_mcp.py | test_mcp_streamable_http_transport_configuration | Verifies host/port settings can be configured for streamable-http transport. |
| test_mcp.py | test_mcp_streamable_http_transport_security_allows_docker | Verifies host.docker.internal can be added to allowed hosts/origins. |
| test_mcp.py | test_mcp_streamable_http_cli_args | Verifies full Docker access CLI configuration (--transport streamable-http --host 0.0.0.0 --port 8000). |
| test_mcp.py | test_mcp_streamable_http_is_recommended_over_sse | Verifies help text indicates SSE is deprecated and streamable-http is recommended. |

---

#### REQ-MCP-015: Header-Based Identity Resolution

**Requirement:** The MCP server shall resolve caller identity based on the presence of the `X-QMS-Identity` HTTP request header. All MCP tools SHALL require a `user` parameter with no default value; calls omitting the parameter or providing an empty value SHALL be rejected with a helpful error. When the header is present (enforced mode): the `user` parameter SHALL match the header value; a mismatch SHALL return an error identifying the caller's authenticated identity and instructing them to use it, with a warning that impersonation is a QMS violation. When the header is absent (trusted mode): identity shall be read from the `user` tool parameter. The `resolve_identity` function SHALL NOT silently fall back when request context is unavailable; non-HTTP contexts (e.g., stdio) SHALL be handled as an explicit trusted-mode path. All MCP tools shall accept a `ctx: Context` parameter for request context access.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_mcp.py | test_resolve_identity_missing_user_raises_error | Verifies TypeError when user_param is omitted (no default). |
| test_mcp.py | test_resolve_identity_empty_user_raises_error | Verifies ValueError for empty string and whitespace-only user. |
| test_mcp.py | test_resolve_identity_stdio_mode_custom_user | Verifies custom user parameter in stdio/non-HTTP context (trusted mode). |
| test_mcp.py | test_resolve_identity_http_header_enforced | Verifies X-QMS-Identity header is used for enforced mode with matching user param. |
| test_mcp.py | test_resolve_identity_enforced_mode_mismatch_raises_error | Verifies ValueError when header identity mismatches user parameter. |
| test_mcp.py | test_resolve_identity_enforced_mode_match_succeeds | Verifies success when header and user param match in enforced mode. |
| test_mcp.py | test_resolve_identity_mismatch_error_message_helpful | Verifies error message includes real identity, claimed identity, corrective instruction, and violation warning. |
| test_mcp.py | test_resolve_identity_http_no_header_trusted_mode | Verifies user parameter is used when header is absent (trusted mode). |
| test_mcp.py | test_resolve_identity_unknown_agent_still_resolves | Verifies unknown agent identities are accepted from headers. |
| test_mcp.py | test_known_agents_set | Verifies KNOWN_AGENTS contains all expected agent identities. |
| test_mcp.py | test_resolve_identity_non_starlette_context_uses_trusted_mode | Verifies trusted mode for non-Starlette context (explicit non-HTTP path). |
| test_mcp.py | test_resolve_identity_tools_receive_resolved_identity | End-to-end: tools pass resolved identity to run_qms_command. |

---

#### REQ-MCP-016: Identity Collision Prevention

**Requirement:** The MCP server shall prevent identity collisions between concurrent callers. When an identity is active in enforced mode (request with X-QMS-Identity header), the server shall: (1) reject trusted-mode requests (no X-QMS-Identity header) attempting to use the same identity with a terminal error message, (2) reject enforced-mode requests from a different container instance claiming the same identity (using X-QMS-Instance header for disambiguation), and (3) maintain identity locks with TTL-based expiry for crash recovery. The proxy shall inject a unique instance identifier (X-QMS-Instance header) per proxy lifecycle for duplicate container detection.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_mcp.py | test_identity_collision_exception_class | Verifies IdentityCollisionError exception class exists and is importable. |
| test_mcp.py | test_identity_lock_ttl_constant | Verifies IDENTITY_LOCK_TTL_SECONDS constant exists and is positive. |
| test_mcp.py | test_identity_collision_enforced_locks_trusted | Verifies enforced-mode identity blocks trusted-mode (HTTP no header) requests for the same identity. |
| test_mcp.py | test_identity_collision_enforced_locks_stdio_mode | Verifies enforced-mode identity blocks stdio-mode (no context) requests for the same identity. |
| test_mcp.py | test_identity_collision_error_message_terminal | Verifies error message contains "IDENTITY LOCKED", "Trusted-mode request rejected", and "Do not attempt to troubleshoot". |
| test_mcp.py | test_identity_lock_ttl_expiry | Verifies identity lock expires after TTL, allowing trusted-mode access. |
| test_mcp.py | test_identity_lock_heartbeat_refreshes | Verifies enforced-mode heartbeat refreshes lock TTL, preventing expiry. |
| test_mcp.py | test_identity_collision_different_identities_ok | Verifies different identities do not collide (qa lock does not block tu_ui). |
| test_mcp.py | test_identity_collision_trusted_mode_does_not_lock | Verifies trusted-mode calls do not create registry entries (no self-collision). |
| test_mcp.py | test_identity_collision_duplicate_container | Verifies different instance_id for same identity raises collision error. |
| test_mcp.py | test_identity_collision_same_instance_heartbeat | Verifies same instance_id refreshes heartbeat without collision. |
| test_mcp.py | test_identity_collision_duplicate_after_ttl | Verifies expired lock allows new instance to register. |
| test_mcp.py | test_identity_registry_cleanup | Verifies _cleanup_expired_locks removes expired entries. |
| test_mcp.py | test_identity_lock_empty_instance_id | Verifies registration works with empty X-QMS-Instance header. |
| test_mcp.py | test_identity_collision_tool_returns_error | End-to-end: tool call with colliding identity returns error response. |

---

### 5.15 Interaction System (REQ-INT-001 through REQ-INT-025)

#### REQ-INT-001: Tag Vocabulary

**Requirement:** The system shall recognize @prompt, @gate, @loop, @end-loop, @end, and @end-prompt tags in HTML comment syntax within templates.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_interact_parser.py | test_recognizes_prompt_tag | Verifies @prompt tag is recognized and parsed. |
| test_interact_parser.py | test_recognizes_gate_tag | Verifies @gate tag is recognized and parsed. |
| test_interact_parser.py | test_recognizes_loop_tags | Verifies @loop and @end-loop tags are recognized. |
| test_interact_parser.py | test_recognizes_end_tag | Verifies @end tag is recognized. |
| test_interact_parser.py | test_tags_must_be_html_comments | Verifies tags must be in HTML comment syntax. |
| test_interact_parser.py | test_all_five_tags_in_one_template | Verifies all five tag types coexist in a single template. |
| test_interact_parser.py | test_end_prompt_recognized_as_tag | Verifies @end-prompt is recognized as a valid tag. |
| test_interact_parser.py | test_guidance_stops_at_end_prompt | Verifies guidance extraction stops at @end-prompt boundary. |
| test_interact_parser.py | test_guidance_without_end_prompt_includes_scaffold | Verifies fallback behavior without @end-prompt includes scaffold. |
| test_interact_parser.py | test_end_prompt_with_gate | Verifies @end-prompt works with @gate tags. |
| test_interact_parser.py | test_end_prompt_stripped_from_vr_template | Verifies @end-prompt stripped from VR template output. |
| test_interact_parser.py | test_all_vr_prompts_have_guidance | Verifies all VR prompts have guidance text. |

---

#### REQ-INT-002: Template Header

**Requirement:** The system shall parse @template header tags specifying template name, version, and start prompt.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_interact_parser.py | test_parses_template_name | Verifies template name is extracted from header. |
| test_interact_parser.py | test_parses_template_version | Verifies template version is extracted from header. |
| test_interact_parser.py | test_parses_start_prompt | Verifies start prompt ID is extracted from header. |
| test_interact_parser.py | test_missing_name_raises | Verifies error when template name is missing. |
| test_interact_parser.py | test_missing_start_raises | Verifies error when start prompt is missing. |
| test_interact_parser.py | test_missing_header_raises | Verifies error when no @template header exists. |
| test_interact_parser.py | test_multiline_header_comment | Verifies multi-line header comments are parsed. |

---

#### REQ-INT-003: Prompt Attributes

**Requirement:** @prompt tags shall support id, next, and commit attributes.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_interact_parser.py | test_prompt_has_id | Verifies prompt node has id attribute. |
| test_interact_parser.py | test_prompt_has_next | Verifies prompt node has next attribute. |
| test_interact_parser.py | test_prompt_commit_defaults_false | Verifies commit defaults to false. |
| test_interact_parser.py | test_prompt_commit_true | Verifies commit: true is parsed. |
| test_interact_parser.py | test_prompt_missing_id_raises | Verifies error when id is missing. |
| test_interact_parser.py | test_prompt_missing_next_raises | Verifies error when next is missing. |
| test_interact_parser.py | test_prompt_has_guidance | Verifies guidance text is captured between tags. |

---

#### REQ-INT-004: Gate Attributes

**Requirement:** @gate tags shall support id, type, yes, and no attributes; type: yesno gates accept yes/no decisions.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_interact_parser.py | test_gate_has_id | Verifies gate node has id attribute. |
| test_interact_parser.py | test_gate_has_type | Verifies gate node has type attribute. |
| test_interact_parser.py | test_gate_has_yes_target | Verifies gate has yes target. |
| test_interact_parser.py | test_gate_has_no_target | Verifies gate has no target. |
| test_interact_parser.py | test_gate_missing_targets_raises | Verifies error when yes/no targets missing. |
| test_interact_parser.py | test_gate_missing_id_raises | Verifies error when gate id is missing. |

---

#### REQ-INT-005: Loop Semantics

**Requirement:** @loop/@end-loop pairs shall define repeating blocks with an iteration counter; loops close via gate decision.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_interact_parser.py | test_loop_defined_by_pair | Verifies loop is defined by @loop/@end-loop pair. |
| test_interact_parser.py | test_loop_tracks_first_prompt | Verifies loop records its first prompt ID. |
| test_interact_parser.py | test_prompts_inside_loop_marked | Verifies prompts inside loop have loop_name set. |
| test_interact_parser.py | test_prompts_outside_loop_not_marked | Verifies prompts outside loop have no loop_name. |
| test_interact_parser.py | test_gate_inside_loop_marked | Verifies gate inside loop has loop_name set. |
| test_interact_parser.py | test_unclosed_loop_raises | Verifies error on unclosed loop. |
| test_interact_parser.py | test_mismatched_end_loop_raises | Verifies error on mismatched end-loop name. |

---

#### REQ-INT-006: Source File Structure

**Requirement:** Interactive documents shall produce .source.json files containing doc_id, template reference, cursor state, responses, loop state, gate decisions, and metadata.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_interact_source.py | test_create_source_has_doc_id | Verifies source contains doc_id field. |
| test_interact_source.py | test_create_source_has_template_reference | Verifies source contains template reference. |
| test_interact_source.py | test_create_source_has_cursor | Verifies source contains cursor state. |
| test_interact_source.py | test_create_source_has_responses | Verifies source contains responses dict. |
| test_interact_source.py | test_create_source_has_loops | Verifies source contains loops dict. |
| test_interact_source.py | test_create_source_has_gates | Verifies source contains gates dict. |
| test_interact_source.py | test_create_source_has_metadata | Verifies source contains metadata dict. |
| test_interact_source.py | test_create_source_default_metadata | Verifies default metadata values. |
| test_interact_source.py | test_source_serializes_to_json | Verifies source is valid JSON. |

---

#### REQ-INT-007: Session File Lifecycle

**Requirement:** Checkout of interactive documents shall produce .interact session files in the workspace; checkin moves session data to .source.json in .meta/.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_interact_source.py | test_save_and_load_session | Verifies session round-trip save/load. |
| test_interact_source.py | test_save_and_load_source | Verifies source round-trip save/load. |
| test_interact_source.py | test_load_nonexistent_session_returns_none | Verifies graceful handling of missing session. |
| test_interact_source.py | test_load_nonexistent_source_returns_none | Verifies graceful handling of missing source. |
| test_interact_source.py | test_session_creates_parent_dirs | Verifies parent directories are created. |
| test_interact_source.py | test_source_creates_parent_dirs | Verifies parent directories are created. |
| test_interact_source.py | test_session_file_is_valid_json | Verifies session file is valid JSON on disk. |
| test_interact_integration.py | test_checkout_creates_interact_session | Verifies checkout creates .interact file. |
| test_interact_integration.py | test_checkin_stores_source_json | Verifies checkin stores .source.json in .meta/. |
| test_interact_integration.py | test_checkin_removes_interact_session | Verifies checkin removes .interact file. |

---

#### REQ-INT-008: Append-Only Responses

**Requirement:** Each response shall be stored as a list of entries with value, author, timestamp, and optional reason and commit fields; amendments append (never replace or delete).

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_interact_source.py | test_response_entry_has_value | Verifies entry contains value field. |
| test_interact_source.py | test_response_entry_has_author | Verifies entry contains author field. |
| test_interact_source.py | test_response_entry_has_timestamp | Verifies entry contains timestamp field. |
| test_interact_source.py | test_response_entry_optional_reason | Verifies entry supports optional reason. |
| test_interact_source.py | test_response_entry_no_reason_by_default | Verifies no reason by default. |
| test_interact_source.py | test_response_entry_optional_commit | Verifies entry supports optional commit. |
| test_interact_source.py | test_response_entry_no_commit_by_default | Verifies no commit by default. |
| test_interact_source.py | test_responses_stored_as_list | Verifies responses are stored as list of entries. |
| test_interact_source.py | test_append_only_multiple_entries | Verifies multiple entries append without replacing. |
| test_interact_source.py | test_get_active_response_returns_last | Verifies active response is the last entry. |

---

#### REQ-INT-009: Amendment Trail

**Requirement:** Amendments to completed prompts shall require a reason; original entries are preserved; compiled output renders superseded entries with strikethrough.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_interact_source.py | test_amendment_preserves_original | Verifies original entry is preserved after amendment. |
| test_interact_source.py | test_amendment_has_reason | Verifies amendment entry includes reason. |
| test_interact_source.py | test_original_entry_has_no_reason | Verifies original entry has no reason field. |
| test_interact_source.py | test_multiple_amendments_all_preserved | Verifies all amendment entries are preserved. |
| test_interact_compiler.py | test_amendment_shows_strikethrough_on_original | Verifies superseded entries render with strikethrough. |
| test_interact_compiler.py | test_multiple_amendments_all_superseded_struck | Verifies all superseded entries have strikethrough. |
| test_interact_compiler.py | test_compiled_document_shows_amendments | End-to-end amendment rendering in compiled output. |

---

#### REQ-INT-010: Interact Entry Point

**Requirement:** `qms interact DOC_ID` with no flags shall display document status and current prompt with guidance text.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_interact_engine.py | test_shows_current_prompt_id | Verifies current prompt ID is shown. |
| test_interact_engine.py | test_shows_guidance_text | Verifies guidance text is displayed. |
| test_interact_engine.py | test_shows_awaiting_response_status | Verifies awaiting response status shown. |
| test_interact_engine.py | test_shows_complete_when_done | Verifies complete status when all prompts answered. |
| test_interact_engine.py | test_shows_commit_flag | Verifies commit flag is indicated. |
| test_interact_engine.py | test_shows_gate_type | Verifies gate type is shown. |
| test_interact_engine.py | test_shows_loop_context | Verifies loop context is shown. |

---

#### REQ-INT-011: Response Flags

**Requirement:** The interact command shall support --respond "value" and --respond --file path; all prompts require an explicit response (no default values).

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_interact_engine.py | test_respond_records_value | Verifies response value is recorded. |
| test_interact_engine.py | test_respond_advances_cursor | Verifies cursor advances after response. |
| test_interact_engine.py | test_respond_returns_next_prompt_info | Verifies next prompt info returned. |
| test_interact_engine.py | test_respond_on_complete_raises | Verifies error when responding after completion. |
| test_interact_integration.py | test_cli_interact_has_all_flags | Verifies --respond and --file flags exist. |

---

#### REQ-INT-012: Navigation Flags

**Requirement:** The interact command shall support --goto prompt_id, --cancel-goto, and --reopen loop_name; --goto and --reopen require --reason.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_interact_engine.py | test_goto_navigates_to_previous_prompt | Verifies goto navigates to a previously answered prompt. |
| test_interact_engine.py | test_goto_requires_reason | Verifies goto requires a reason. |
| test_interact_engine.py | test_goto_to_unanswered_raises | Verifies goto to unanswered prompt raises error. |
| test_interact_engine.py | test_goto_amendment_mode | Verifies engine enters amendment mode on goto. |
| test_interact_engine.py | test_goto_amendment_returns_to_original | Verifies engine returns to original cursor after amendment. |
| test_interact_engine.py | test_cancel_goto | Verifies cancel-goto returns to original position. |
| test_interact_engine.py | test_cancel_goto_no_active_raises | Verifies error when no active goto to cancel. |
| test_interact_engine.py | test_reopen_loop | Verifies reopen re-enters a closed loop. |
| test_interact_engine.py | test_reopen_requires_reason | Verifies reopen requires a reason. |
| test_interact_engine.py | test_reopen_nonclosed_raises | Verifies error when reopening a non-closed loop. |

---

#### REQ-INT-013: Query Flags

**Requirement:** The interact command shall support --progress and --compile (output compiled markdown preview to stdout).

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_interact_engine.py | test_progress_shows_all_prompts | Verifies progress shows all prompt IDs. |
| test_interact_engine.py | test_progress_shows_filled_status | Verifies progress shows filled/empty status. |
| test_interact_engine.py | test_progress_shows_commit_prompts | Verifies progress marks commit-enabled prompts. |
| test_interact_engine.py | test_progress_shows_loop_iterations | Verifies progress shows loop iteration details. |
| test_interact_compiler.py | test_compile_preview_matches_compile_document | Verifies compile_preview output matches compile_document. |

---

#### REQ-INT-014: Sequential Enforcement

**Requirement:** The engine shall not accept responses to prompts that have not been presented; prompts must be answered in template-defined order.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_interact_engine.py | test_cannot_skip_prompts | Verifies engine rejects responses to future prompts. |
| test_interact_engine.py | test_cursor_at_correct_start | Verifies cursor starts at template-defined start prompt. |
| test_interact_engine.py | test_cursor_advances_sequentially | Verifies cursor advances through prompts in order. |
| test_interact_engine.py | test_respond_on_gate_raises_if_not_gate | Verifies gate response rejected on non-gate prompt. |
| test_interact_engine.py | test_respond_on_prompt_raises_if_gate | Verifies regular response rejected on gate prompt. |

---

#### REQ-INT-015: Contextual Interpolation

**Requirement:** Prompt guidance text may reference previous responses using {{id}} syntax; the engine shall substitute known values before presenting.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_interact_engine.py | test_interpolates_previous_response | Verifies previous response values are substituted. |
| test_interact_engine.py | test_unresolved_placeholder_left_intact | Verifies unresolved placeholders remain as-is. |
| test_interact_engine.py | test_interpolates_metadata | Verifies metadata values are substituted. |
| test_interact_engine.py | test_interpolates_loop_counter | Verifies loop counter {{_n}} is substituted. |

---

#### REQ-INT-016: Compilation

**Requirement:** The system shall compile source files into markdown by stripping tags and guidance, substituting placeholders with active responses, and rendering amendment trails.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_interact_compiler.py | test_strips_template_header | Verifies @template header is stripped from output. |
| test_interact_compiler.py | test_strips_prompt_tags | Verifies @prompt tags are stripped from output. |
| test_interact_compiler.py | test_strips_guidance_text | Verifies guidance prose is stripped from output. |
| test_interact_compiler.py | test_substitutes_placeholders | Verifies {{placeholder}} values are substituted. |
| test_interact_compiler.py | test_preserves_markdown_structure | Verifies headings, tables, code blocks preserved. |
| test_interact_compiler.py | test_substitutes_metadata | Verifies metadata placeholders are substituted. |
| test_interact_compiler.py | test_empty_responses_leave_blank | Verifies unfilled placeholders render as empty. |
| test_interact_compiler.py | test_vr_compiles_with_filled_responses | End-to-end VR template compilation with data. |
| test_interact_compiler.py | test_vr_compiles_empty_gracefully | VR template compiles gracefully with no responses. |
| test_interact_compiler.py | test_template_fm_removed | D1: Template's own frontmatter stripped from output. |
| test_interact_compiler.py | test_document_fm_kept | D1: Document frontmatter with placeholders preserved. |
| test_interact_compiler.py | test_notice_stripped | D1: Template notice comment stripped from output. |
| test_interact_compiler.py | test_single_fm_preserved | D1: Single FM block kept as-is. |
| test_interact_compiler.py | test_compiled_output_has_one_fm | D1: Full compilation produces exactly one FM block. |
| test_interact_compiler.py | test_real_template_preamble_stripped | D1: TEMPLATE-VR preamble stripped in compilation. |
| test_interact_compiler.py | test_table_rows_no_attribution | D2: Table cell substitution omits attribution. |
| test_interact_compiler.py | test_table_row_single_line | D2: Table row remains single line after substitution. |
| test_interact_compiler.py | test_table_amendment_active_only | D2: Table cell shows only active value. |
| test_interact_compiler.py | test_loop_bold_not_broken | D2: Bold markers wrap only value, not attribution. |
| test_interact_compiler.py | test_loop_attribution_outside_code_fence | D2: Attribution outside code fences in step_actual. |
| test_interact_compiler.py | test_guidance_stripped_before_end_prompt | D3: Guidance between @prompt and @end-prompt stripped. |
| test_interact_compiler.py | test_scaffold_preserved_after_end_prompt | D3: Scaffold after @end-prompt preserved. |
| test_interact_compiler.py | test_end_prompt_tag_stripped_from_output | D3: @end-prompt tag itself not in output. |
| test_interact_compiler.py | test_fallback_without_end_prompt | D3: Without @end-prompt, guidance skipped until structural. |
| test_interact_compiler.py | test_block_context_wrapped | D4: Block-context response in blockquote. |
| test_interact_compiler.py | test_block_context_attribution_in_blockquote | D4: Attribution inside blockquote for block context. |
| test_interact_compiler.py | test_label_context_not_wrapped | D4: Label-context response not blockquoted. |
| test_interact_compiler.py | test_table_context_not_wrapped | D4: Table-context response not blockquoted. |
| test_interact_compiler.py | test_empty_block_not_wrapped | D4: Empty block context not wrapped. |

---

#### REQ-INT-017: Interactive Checkout

**Requirement:** Checkout of interactive documents shall initialize a .interact session file; if a .source.json exists, it seeds the session.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_interact_integration.py | test_checkout_creates_interact_session | Verifies checkout creates .interact session file. |
| test_interact_integration.py | test_checkout_seeds_from_source_json | Verifies checkout seeds from existing .source.json. |
| test_interact_integration.py | test_checkout_creates_placeholder_md | Verifies checkout creates placeholder markdown. |

---

#### REQ-INT-018: Interactive Checkin

**Requirement:** Checkin of interactive documents shall compile to markdown, store .source.json in .meta/, and remove the .interact session.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_interact_integration.py | test_checkin_compiles_to_markdown | Verifies checkin compiles source to markdown. |
| test_interact_integration.py | test_checkin_stores_source_json | Verifies checkin stores .source.json in .meta/. |
| test_interact_integration.py | test_checkin_removes_interact_session | Verifies checkin removes .interact file from workspace. |

---

#### REQ-INT-019: Source-Aware Read

**Requirement:** qms read shall compile from .interact (if checked out) or .source.json (if checked in) when available, falling back to standard markdown.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_interact_integration.py | test_read_compiles_from_session | Verifies read compiles from active .interact session. |
| test_interact_integration.py | test_read_compiles_from_source_json | Verifies read compiles from stored .source.json. |
| test_interact_integration.py | test_read_falls_back_to_standard_for_non_interactive | Verifies read falls back to standard for non-interactive docs. |

---

#### REQ-INT-020: Engine-Managed Commits

**Requirement:** On prompts with commit: true, the engine shall stage changes, commit with a system-generated message, and record the resulting commit hash.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_interact_integration.py | test_commit_message_format | Verifies commit message format: [QMS] {DOC_ID} | {context} | {prompt_id}. |
| test_interact_integration.py | test_commit_hash_recorded_in_response | Verifies commit hash is recorded in response entry. |
| test_interact_integration.py | test_engine_commit_function_exists | Verifies _do_engine_commit function exists. |
| test_interact_integration.py | test_engine_commit_returns_empty_on_no_project_root | Verifies graceful handling when no project root. |
| test_interact_integration.py | test_engine_commit_in_git_repo | End-to-end: commit in real git repo records hash. |

---

#### REQ-INT-021: Commit Staging Scope

**Requirement:** Engine-managed commits shall stage changes scoped to the project working tree.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_interact_integration.py | test_stages_all_changes | Verifies all working tree changes are staged. |
| test_interact_integration.py | test_no_commit_when_no_changes | Verifies no commit created when no changes exist. |

---

#### REQ-INT-022: MCP Interact Tool

**Requirement:** The MCP server shall expose a qms_interact tool functionally equivalent to the qms interact CLI command.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_interact_integration.py | test_mcp_tools_module_has_qms_interact | Verifies qms_interact function exists in MCP tools. |
| test_interact_integration.py | test_mcp_interact_has_respond_param | Verifies respond parameter in MCP tool. |
| test_interact_integration.py | test_mcp_interact_has_file_param | Verifies file parameter in MCP tool. |
| test_interact_integration.py | test_mcp_interact_has_reason_param | Verifies reason parameter in MCP tool. |
| test_interact_integration.py | test_mcp_interact_has_goto_param | Verifies goto parameter in MCP tool. |
| test_interact_integration.py | test_mcp_interact_has_cancel_goto_param | Verifies cancel_goto parameter in MCP tool. |
| test_interact_integration.py | test_mcp_interact_has_reopen_param | Verifies reopen parameter in MCP tool. |
| test_interact_integration.py | test_mcp_interact_has_progress_param | Verifies progress parameter in MCP tool. |
| test_interact_integration.py | test_mcp_interact_has_compile_param | Verifies compile parameter in MCP tool. |
| test_interact_integration.py | test_mcp_interact_calls_interact_command | Verifies MCP tool delegates to CLI interact command. |
| test_interact_integration.py | test_cli_interact_command_registered | Verifies interact command is registered in CLI. |
| test_interact_integration.py | test_cli_interact_has_all_flags | Verifies CLI interact has all required flags. |
| test_interact_integration.py | test_interact_registered_in_command_registry | Verifies interact in CommandRegistry. |
| test_interact_integration.py | test_interact_requires_doc_id | Verifies interact command requires doc_id. |
| test_interact_integration.py | test_new_modules_import_cleanly | Verifies all new interaction modules import without error. |

---

#### REQ-INT-023: Auto-Generated Metadata

**Requirement:** The compiler shall auto-generate date, performer, and performed_date metadata fields from response timestamps and authors when not explicitly present.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_interact_compiler.py | test_auto_date_from_earliest_timestamp | date auto-generated from earliest response timestamp. |
| test_interact_compiler.py | test_auto_performer_from_authors | performer auto-generated from unique response authors. |
| test_interact_compiler.py | test_auto_performed_date_from_latest_timestamp | performed_date auto-generated from latest response timestamp. |
| test_interact_compiler.py | test_explicit_metadata_not_overwritten | Explicit metadata values are preserved over auto-generated. |
| test_interact_compiler.py | test_no_responses_no_auto_metadata | No auto-metadata when no responses exist. |
| test_interact_compiler.py | test_auto_metadata_in_compilation | Auto-generated metadata appears in compiled output. |

---

#### REQ-INT-024: Block Rendering

**Requirement:** All non-table lines containing response substitutions shall use block rendering with attribution below the blockquote.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_interact_compiler.py | test_standalone_response_blockquoted | Standalone response gets blockquote wrapping. |
| test_interact_compiler.py | test_attribution_below_blockquote | Attribution is below the blockquote, not inside it. |
| test_interact_compiler.py | test_label_context_also_block_rendered | Label-context responses are also block-rendered. |
| test_interact_compiler.py | test_table_context_not_wrapped | Table-context responses are NOT blockquoted. |
| test_interact_compiler.py | test_empty_block_not_wrapped | Empty block-context placeholder is not wrapped. |

---

#### REQ-INT-025: Step Subsection Numbering

**Requirement:** Loop-expanded step headings shall use subsection numbering in the format ### N.n Step n.

| Test File | Test Function | Description |
|-----------|---------------|-------------|
| test_interact_compiler.py | test_step_subsection_headings | Steps produce 4.1 Step 1, 4.2 Step 2 headings. |
| test_interact_compiler.py | test_step_expected_blockquoted | Step expected values are rendered as blockquotes. |
| test_interact_compiler.py | test_step_actual_code_fenced | Step actual values are in code fences. |

---

## 6. Test Execution Summary

### 6.1 Qualified Baseline

| Attribute | Value |
|-----------|-------|
| Requirements Spec | SDLC-QMS-RS v18.0 |
| Repository | whharris917/qms-cli |
| Branch | cr-095 |
| Commit | 31f8306 |
| Total Tests | 673 |
| Passed | 673 |
| Failed | 0 |

### 6.2 Test Protocol Results

#### 6.2.1 Qualification Tests (tests/qualification/)

| Test Protocol | Tests | Passed | Failed |
|---------------|-------|--------|--------|
| test_sop_lifecycle.py | 15 | 15 | 0 |
| test_cr_lifecycle.py | 11 | 11 | 0 |
| test_cr048_workflow.py | 11 | 11 | 0 |
| test_cr087_workflow.py | 10 | 10 | 0 |
| test_audit_completeness.py | 2 | 2 | 0 |
| test_security.py | 19 | 19 | 0 |
| test_document_types.py | 37 | 37 | 0 |
| test_queries.py | 16 | 16 | 0 |
| test_prompts.py | 7 | 7 | 0 |
| test_templates.py | 9 | 9 | 0 |
| test_init.py | 15 | 15 | 0 |
| test_mcp.py | 74 | 74 | 0 |
| **Subtotal** | **226** | **226** | **0** |

#### 6.2.2 Unit Tests (tests/)

| Test File | Tests | Passed | Failed |
|-----------|-------|--------|--------|
| test_interact_parser.py | 49 | 49 | 0 |
| test_interact_source.py | 46 | 46 | 0 |
| test_interact_engine.py | 44 | 44 | 0 |
| test_interact_compiler.py | 58 | 58 | 0 |
| test_interact_integration.py | 31 | 31 | 0 |
| test_attachment_lifecycle.py | 16 | 16 | 0 |
| Other unit tests | 203 | 203 | 0 |
| **Subtotal** | **447** | **447** | **0** |

#### 6.2.3 Full Test Suite Summary

| Category | Tests | Passed | Failed |
|----------|-------|--------|--------|
| Qualification Tests | 226 | 226 | 0 |
| Unit Tests | 447 | 447 | 0 |
| **Total** | **673** | **673** | **0** |

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

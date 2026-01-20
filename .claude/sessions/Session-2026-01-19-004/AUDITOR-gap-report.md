# AUDITOR: RS Validation Gap Report

## Executive Summary

| Metric | Count | Percentage |
|--------|-------|------------|
| **Total REQs** | 64 | 100% |
| **Accurate** | 42 | 65.6% |
| **Accurate with Issues** | 15 | 23.4% |
| **Inaccurate** | 7 | 10.9% |
| **Complete** | 39 | 60.9% |
| **Incomplete** | 25 | 39.1% |
| **Sufficient for Rebuild** | 42 | 65.6% |
| **Insufficient for Rebuild** | 22 | 34.4% |

### Key Findings

1. **7 inaccurate requirements** need immediate correction - they describe behavior that does not match implementation
2. **15 accurate-with-issues requirements** need revision for completeness or edge case coverage
3. **22 requirements** are insufficient for rebuilding the system from specification alone
4. **2 implementation gaps** exist where code does not implement what the requirement describes (REQ-WF-005, REQ-WF-012)
5. **18+ undocumented features** need new requirements or explicit documentation

---

## Findings Matrix

| REQ ID | Domain | Assessment | Complete | Rebuild | Recommendation |
|--------|--------|------------|----------|---------|----------------|
| REQ-SEC-001 | SEC | ACCURATE | COMPLETE | SUFFICIENT | PASS |
| REQ-SEC-002 | SEC | INACCURATE | INCOMPLETE | INSUFFICIENT | REVISE |
| REQ-SEC-003 | SEC | ACCURATE* | INCOMPLETE | INSUFFICIENT | REVISE |
| REQ-SEC-004 | SEC | ACCURATE* | INCOMPLETE | INSUFFICIENT | REVISE |
| REQ-SEC-005 | SEC | ACCURATE | COMPLETE | SUFFICIENT | PASS |
| REQ-SEC-006 | SEC | ACCURATE | COMPLETE | SUFFICIENT | PASS |
| REQ-DOC-001 | DOC | INACCURATE | INCOMPLETE | INSUFFICIENT | REVISE |
| REQ-DOC-002 | DOC | PARTIAL | INCOMPLETE | INSUFFICIENT | REVISE |
| REQ-DOC-003 | DOC | ACCURATE | COMPLETE | SUFFICIENT | PASS |
| REQ-DOC-004 | DOC | ACCURATE | COMPLETE | SUFFICIENT | PASS |
| REQ-DOC-005 | DOC | PARTIAL | INCOMPLETE | INSUFFICIENT | REVISE |
| REQ-DOC-006 | DOC | ACCURATE | COMPLETE | SUFFICIENT | PASS |
| REQ-DOC-007 | DOC | ACCURATE | INCOMPLETE | INSUFFICIENT | REVISE |
| REQ-DOC-008 | DOC | PARTIAL | INCOMPLETE | INSUFFICIENT | REVISE |
| REQ-DOC-009 | DOC | PARTIAL | INCOMPLETE | INSUFFICIENT | REVISE |
| REQ-DOC-010 | DOC | ACCURATE | INCOMPLETE | INSUFFICIENT | REVISE |
| REQ-DOC-011 | DOC | PARTIAL | INCOMPLETE | INSUFFICIENT | REVISE |
| REQ-DOC-012 | DOC | INACCURATE | INCOMPLETE | INSUFFICIENT | REVISE |
| REQ-WF-001 | WF | ACCURATE | COMPLETE | SUFFICIENT | PASS |
| REQ-WF-002 | WF | ACCURATE | COMPLETE | SUFFICIENT | PASS |
| REQ-WF-003 | WF | ACCURATE | COMPLETE | SUFFICIENT | REVISE (minor) |
| REQ-WF-004 | WF | ACCURATE | COMPLETE | SUFFICIENT | PASS |
| REQ-WF-005 | WF | INACCURATE | INCOMPLETE | INSUFFICIENT | REVISE (impl gap) |
| REQ-WF-006 | WF | ACCURATE | INCOMPLETE | SUFFICIENT | REVISE |
| REQ-WF-007 | WF | ACCURATE | COMPLETE | SUFFICIENT | PASS |
| REQ-WF-008 | WF | ACCURATE | COMPLETE | SUFFICIENT | PASS |
| REQ-WF-009 | WF | ACCURATE | COMPLETE | SUFFICIENT | PASS |
| REQ-WF-010 | WF | ACCURATE | COMPLETE | SUFFICIENT | PASS |
| REQ-WF-011 | WF | ACCURATE | COMPLETE | SUFFICIENT | PASS |
| REQ-WF-012 | WF | PARTIAL | INCOMPLETE | INSUFFICIENT | REVISE (impl gap) |
| REQ-WF-013 | WF | ACCURATE | COMPLETE | SUFFICIENT | PASS |
| REQ-META-001 | META | ACCURATE | COMPLETE | SUFFICIENT | PASS |
| REQ-META-002 | META | ACCURATE | COMPLETE | SUFFICIENT | PASS |
| REQ-META-003 | META | ACCURATE | COMPLETE | SUFFICIENT | PASS |
| REQ-META-004 | META | ACCURATE | COMPLETE | SUFFICIENT | PASS |
| REQ-AUDIT-001 | META | ACCURATE | COMPLETE | SUFFICIENT | PASS |
| REQ-AUDIT-002 | META | ACCURATE | COMPLETE | SUFFICIENT | PASS |
| REQ-AUDIT-003 | META | ACCURATE* | COMPLETE | SUFFICIENT | PASS |
| REQ-AUDIT-004 | META | ACCURATE | COMPLETE | SUFFICIENT | PASS |
| REQ-TASK-001 | TASK | ACCURATE | COMPLETE | SUFFICIENT | PASS |
| REQ-TASK-002 | TASK | ACCURATE | COMPLETE | SUFFICIENT | PASS |
| REQ-TASK-003 | TASK | INACCURATE | INCOMPLETE | INSUFFICIENT | REVISE |
| REQ-TASK-004 | TASK | ACCURATE | INCOMPLETE | INSUFFICIENT | REVISE |
| REQ-CFG-001 | TASK | ACCURATE | COMPLETE | SUFFICIENT | PASS |
| REQ-CFG-002 | TASK | ACCURATE | COMPLETE | SUFFICIENT | PASS |
| REQ-CFG-003 | TASK | ACCURATE | COMPLETE | SUFFICIENT | PASS |
| REQ-CFG-004 | TASK | ACCURATE | INCOMPLETE | INSUFFICIENT | REVISE |
| REQ-CFG-005 | TASK | ACCURATE | INCOMPLETE | INSUFFICIENT | REVISE |
| REQ-QRY-001 | QUERY | ACCURATE | COMPLETE | SUFFICIENT | PASS |
| REQ-QRY-002 | QUERY | ACCURATE | COMPLETE | SUFFICIENT | PASS |
| REQ-QRY-003 | QUERY | ACCURATE | COMPLETE | SUFFICIENT | PASS |
| REQ-QRY-004 | QUERY | ACCURATE | COMPLETE | SUFFICIENT | PASS |
| REQ-QRY-005 | QUERY | ACCURATE | COMPLETE | SUFFICIENT | PASS |
| REQ-QRY-006 | QUERY | ACCURATE | COMPLETE | SUFFICIENT | PASS |
| REQ-PROMPT-001 | QUERY | ACCURATE | COMPLETE | SUFFICIENT | PASS |
| REQ-PROMPT-002 | QUERY | ACCURATE | COMPLETE | SUFFICIENT | PASS |
| REQ-PROMPT-003 | QUERY | ACCURATE | COMPLETE | SUFFICIENT | PASS |
| REQ-PROMPT-004 | QUERY | ACCURATE | COMPLETE | SUFFICIENT | PASS |
| REQ-PROMPT-005 | QUERY | ACCURATE | COMPLETE | SUFFICIENT | PASS |
| REQ-PROMPT-006 | QUERY | ACCURATE* | INCOMPLETE | SUFFICIENT | REVISE |
| REQ-TEMPLATE-001 | QUERY | ACCURATE | COMPLETE | SUFFICIENT | PASS |
| REQ-TEMPLATE-002 | QUERY | ACCURATE | COMPLETE | SUFFICIENT | PASS |
| REQ-TEMPLATE-003 | QUERY | ACCURATE* | COMPLETE | SUFFICIENT | REVISE |
| REQ-TEMPLATE-004 | QUERY | ACCURATE | COMPLETE | SUFFICIENT | PASS |

**Legend:**
- ACCURATE* = Accurate with minor issues noted
- PARTIAL = Partially accurate, some statements do not match implementation
- INACCURATE = Major discrepancy between requirement and implementation

---

## Cross-Domain Issues

### 1. Document Type List Inconsistency (DOC / WF / SEC)

**Affected REQs:** REQ-DOC-001, REQ-WF-003, REQ-SEC-002

The document type list in REQ-DOC-001 lists 9 types, but the implementation supports 16 types. This cascades to:
- REQ-WF-003 lists executable types but omits CAPA
- REQ-SEC-002 references action authorization but omits several document types' special behaviors

**Recommendation:** Create a single authoritative list of document types in REQ-DOC-001 and have other requirements reference it rather than re-listing.

### 2. Permission Model Complexity (SEC / TASK)

**Affected REQs:** REQ-SEC-002, REQ-SEC-003, REQ-SEC-004, REQ-CFG-004

The permission model has three layers not fully captured:
1. Group-based permissions (initiators/qa/reviewers)
2. Owner-only restrictions with initiator cross-action exception
3. Assignment-based access (assigned_only)

REQ-CFG-004 only mentions groups but does not mention the PERMISSIONS dictionary with owner_only and assigned_only modifiers.

**Recommendation:** Consolidate permission documentation. Either expand REQ-CFG-004 to cover the full permission model, or add cross-references between SEC and CFG requirements.

### 3. Workflow State vs. Metadata Coupling (WF / META / DOC)

**Affected REQs:** REQ-WF-005, REQ-META-003, REQ-DOC-009

Review outcomes are logged to audit (per META requirements) but REQ-WF-005 expects them to block approval routing. However:
- Code does NOT store review outcomes in .meta (where they would be accessible for routing checks)
- Code logs to audit only (append-only, not designed for runtime queries)

This is an architectural gap: the workflow requirement assumes state that is not stored in the metadata layer.

**Recommendation:** Either:
- Add review_outcomes to REQ-META-003 required fields
- Or revise REQ-WF-005 to acknowledge this gate is not currently enforced

### 4. Archive Behavior Timing (DOC / WF)

**Affected REQs:** REQ-DOC-007, REQ-DOC-008, REQ-WF-006

Archiving occurs at multiple points:
- On checkout of effective document (creates archive before draft creation)
- On approval (archives current version before version bump)
- On retirement (archives before removing working copy)

REQ-DOC-007 and REQ-DOC-008 describe checkin/checkout archive behavior incompletely. REQ-WF-006 mentions archiving on approval.

**Recommendation:** Add a new requirement documenting the complete archive lifecycle, or ensure each trigger point is documented in its respective requirement.

### 5. Task Removal Asymmetry (TASK / WF)

**Affected REQs:** REQ-TASK-004, REQ-WF-007

When a document is rejected:
- REQ-WF-007 transitions status back to REVIEWED (accurate)
- REQ-TASK-004 says tasks are removed but does not specify that rejection removes ALL pending approval tasks across ALL user inboxes (bulk removal)

This asymmetry between individual task removal (review complete) and bulk removal (rejection) is not captured.

**Recommendation:** Revise REQ-TASK-004 to specify different removal scopes.

---

## Undocumented Functionality (Prioritized)

### P1 - Critical (Missing REQs Needed)

These are core security or behavioral features that must be documented for compliance and rebuilding:

| # | Feature | Location | Impact |
|---|---------|----------|--------|
| 1 | **Workspace/Inbox Isolation** | qms_auth.py:121-135 | Security: users cannot access other users' directories |
| 2 | **CAPA Document Type** | qms_config.py:82 | Document Management: child of INV, executable |
| 3 | **DS/CS/OQ Document Types** | qms_config.py:87-90 | Document Management: SDLC-FLOW singletons |
| 4 | **QMS-RS/QMS-RTM Document Types** | qms_config.py:92-93 | Document Management: SDLC-QMS singletons |
| 5 | **Singleton Document Behavior** | qms_config.py (singleton flag) | ID generation: name-based not numbered |
| 6 | **Initiator Cross-Action Exception** | qms_auth.py:87-88 | Security: any initiator can act on any other initiator's docs |
| 7 | **Checked-out Document Restrictions** | cancel.py:58-62, route.py:65-80 | Workflow: blocking condition for cancel and route |
| 8 | **Execution Phase Tracking** | qms_meta.py:93-104 | Workflow: pre_release vs post_release phase |

### P2 - Moderate (Enhancements Needed)

Important behaviors and edge cases that improve rebuildability:

| # | Feature | Location | Impact |
|---|---------|----------|--------|
| 9 | **TP Singular ID Format** | create.py:83-85 | ID generation: CR-001-TP not CR-001-TP-001 |
| 10 | **folder_per_doc Configuration** | qms_config.py:80-81 | Storage: CR and INV get subdirectories |
| 11 | **Archive on Effective Checkout** | checkout.py:87-90 | Archiving: effective version archived before draft |
| 12 | **Workspace Deletion on Checkin** | checkin.py:81 | Cleanup: workspace copy removed after checkin |
| 13 | **QA Default Assignment** | route.py:132 | Task: QA assigned only when no explicit assignees |
| 14 | **Task Filename Format** | prompts.py | Task: task-{doc_id}-{workflow_type}-v{version}.md |
| 15 | **Comments Visibility Restriction** | comments.py:52-60 | Query: no comments visible during active review |
| 16 | **Assign Command Post-Routing** | assign.py | Task: add reviewers after initial routing |
| 17 | **Cancel --confirm Requirement** | cancel.py:65-73 | Safety: confirmation required for deletion |
| 18 | **Checkout from Terminal States** | cr_lifecycle test | Amendment: allowed to create new revision |

### P3 - Minor (Implementation Details)

Lower-priority items that are nice-to-have:

| # | Feature | Location | Impact |
|---|---------|----------|--------|
| 19 | **Unknown Command Permissiveness** | qms_auth.py:64-65 | Security: undefined commands pass authorization |
| 20 | **checked_out_date Metadata Field** | qms_meta.py:107 | Audit: timestamp of checkout |
| 21 | **effective_version Metadata Field** | qms_meta.py:108 | History: version when doc became effective |
| 22 | **supersedes Metadata Field** | qms_meta.py:109 | History: reference to superseded doc |
| 23 | **Review Tracking Fields** | qms_meta.py:160-163 | Workflow: pending/completed reviewers lists |
| 24 | **In-Memory Prompt Fallback** | prompts.py:360-372 | Config: fallback when YAML files missing |
| 25 | **Template Comment Stripping** | qms_templates.py:110-119 | Creation: removes template notice |
| 26 | **Minimal Fallback Template** | qms_templates.py:122-147 | Creation: generated when no template file |

---

## Redundancy Analysis

### Potential Consolidation Opportunities

1. **REQ-SEC-004 and REQ-SEC-005:** Both describe assignment-based access. REQ-SEC-005 could be merged into REQ-SEC-004 as: "Review, approve, and reject actions require assignment to pending_assignees."

2. **REQ-DOC-007 and REQ-DOC-008:** Checkout and checkin are complementary operations. Consider whether they should reference a shared "document editing cycle" concept.

3. **REQ-WF-006 and REQ-WF-013:** Both describe approval outcomes (version bump, archive). Could share common "approval completion" language.

### Overlapping Coverage

| REQ Pair | Overlap | Recommendation |
|----------|---------|----------------|
| REQ-SEC-002 / REQ-CFG-004 | Both describe group-based authorization | Consolidate into CFG-004, reference from SEC |
| REQ-DOC-001 / REQ-DOC-012 | Document types listed twice | DOC-012 should reference DOC-001 list |
| REQ-META-003 / REQ-AUDIT-003 | Both require timestamp fields | Consider shared "common fields" requirement |

---

## Prioritized Action Items

### P1 - Must Fix Before Approval

These are blocking issues - either inaccurate requirements or implementation gaps:

| # | Action | REQ | Change |
|---|--------|-----|--------|
| 1 | **REVISE** REQ-SEC-002 | SEC | Update to reflect: route allowed for Initiators AND QA; fix uses user-level auth (qa, lead user), not group-level |
| 2 | **REVISE** REQ-SEC-003 | SEC | Add exception: "Any Initiator may perform these actions on documents owned by another Initiator" |
| 3 | **REVISE** REQ-DOC-001 | DOC | Expand list from 9 to 16 document types (add CAPA, DS, CS, OQ, QMS-RS, QMS-RTM) |
| 4 | **REVISE** REQ-DOC-008 | DOC | Remove "archive any previous draft version" - drafts are NOT archived on checkin |
| 5 | **REVISE** REQ-WF-005 | WF | Mark as NOT IMPLEMENTED: approval gate check does not exist in code. Add note: "Implementation required" |
| 6 | **REVISE** REQ-WF-012 | WF | Mark version >= 1.0 check as NOT IMPLEMENTED: code allows retirement of never-effective docs |
| 7 | **REVISE** REQ-TASK-003 | TASK | Correct: QA is default only when NO explicit assignees provided (fallback, not additive) |
| 8 | **ADD** REQ-SEC-007 | SEC | Workspace/Inbox Isolation: users cannot access other users' workspace or inbox |

### P2 - Should Fix

Important for completeness and rebuildability:

| # | Action | REQ | Change |
|---|--------|-----|--------|
| 9 | **REVISE** REQ-SEC-004 | SEC | Clarify dual-gate: group membership AND assignment required. Note Initiators cannot approve. |
| 10 | **REVISE** REQ-DOC-002 | DOC | Add CAPA as child of INV. Document TP singular ID format. |
| 11 | **REVISE** REQ-DOC-005 | DOC | Clarify: TP uses singular format (CR-001-TP), only VAR/ER use sequential |
| 12 | **REVISE** REQ-DOC-007 | DOC | Add: effective version is archived before draft creation; mention checked_out_date |
| 13 | **REVISE** REQ-DOC-009 | DOC | Clarify: ALL reviewed states revert to DRAFT (no special executable behavior). Add review field clearing. |
| 14 | **REVISE** REQ-DOC-010 | DOC | Add: --confirm required, checked-out docs cannot be cancelled, workspace/inbox cleanup |
| 15 | **REVISE** REQ-DOC-011 | DOC | Clarify: --name is optional with sequential fallback; mention uppercase conversion |
| 16 | **REVISE** REQ-DOC-012 | DOC | Add DS, CS, OQ; explain singleton behavior; clarify type-to-ID mapping |
| 17 | **REVISE** REQ-WF-003 | WF | Add CAPA to list of executable document types |
| 18 | **REVISE** REQ-WF-006 | WF | Clarify: responsible_user only cleared for non-executable docs going EFFECTIVE |
| 19 | **REVISE** REQ-TASK-004 | TASK | Specify: review removes individual task; rejection removes ALL pending approval tasks across ALL users |
| 20 | **REVISE** REQ-CFG-004 | CFG | Add: command-level permissions with owner_only and assigned_only modifiers |
| 21 | **REVISE** REQ-CFG-005 | CFG | Add: singleton flag for name-based document identification |
| 22 | **REVISE** REQ-TEMPLATE-003 | TEMPLATE | Update placeholder syntax: {{TITLE}} and {TYPE}-XXX pattern |
| 23 | **ADD** REQ-WF-014 | WF | Execution phase tracking: pre_release vs post_release; determines workflow path |
| 24 | **ADD** REQ-WF-015 | WF | Checked-in requirement before routing: documents must be checked in to route |
| 25 | **ADD** REQ-DOC-013 | DOC | folder_per_doc behavior: CR and INV documents stored in subdirectories |

### P3 - Nice to Have

Improvements for documentation completeness:

| # | Action | REQ | Change |
|---|--------|-----|--------|
| 26 | **REVISE** REQ-PROMPT-006 | PROMPT | Clarify: custom_header/custom_footer loaded but not currently rendered |
| 27 | **ADD** REQ-QRY-007 | QRY | Comments visibility: not visible during active review states |
| 28 | **ADD** REQ-TASK-005 | TASK | Assign command: QA can add reviewers/approvers after initial routing |
| 29 | **ADD** REQ-DOC-014 | DOC | Archive lifecycle: when archives are created (checkout effective, approval, retirement) |
| 30 | **ADD** REQ-TEMPLATE-005 | TEMPLATE | Fallback template generation when no template file exists |
| 31 | **NOTE** | META | Optional fields documented (checked_out_date, effective_version, supersedes) |
| 32 | **NOTE** | SEC | Unknown commands pass authorization (permissive-by-default) |

---

## Implementation Recommendation

### Phase 1: Critical Fixes (Can be done in parallel)

These can be edited independently as they touch different sections of the RS:

| Parallel Track | REQs to Fix | Estimated Effort |
|----------------|-------------|------------------|
| **Track A: Security** | REQ-SEC-002, REQ-SEC-003, REQ-SEC-004, ADD REQ-SEC-007 | Low |
| **Track B: Document Types** | REQ-DOC-001, REQ-DOC-002, REQ-DOC-012 | Medium |
| **Track C: Workflow Flags** | REQ-WF-005, REQ-WF-012 (mark as unimplemented) | Low |
| **Track D: Task** | REQ-TASK-003 | Low |

### Phase 2: Completeness Enhancements (Sequential by section)

After Phase 1, update remaining REQs section-by-section:

1. **DOC Section:** REQ-DOC-005, 007, 008, 009, 010, 011 (interconnected behaviors)
2. **WF Section:** REQ-WF-003, 006, ADD 014, 015 (workflow state machine)
3. **TASK/CFG Section:** REQ-TASK-004, REQ-CFG-004, 005 (configuration model)
4. **QUERY/TEMPLATE Section:** REQ-PROMPT-006, REQ-TEMPLATE-003 (minor fixes)

### Phase 3: New Requirements (After approval of existing REQ fixes)

Add new requirements in a separate revision cycle:

- REQ-SEC-007 (workspace isolation)
- REQ-WF-014, 015 (execution phase, checked-in gate)
- REQ-DOC-013, 014 (folder structure, archive lifecycle)
- REQ-QRY-007 (comments visibility)
- REQ-TASK-005 (assign command)
- REQ-TEMPLATE-005 (fallback template)

---

## Summary Statistics by Domain

| Domain | Total | Accurate | Issues | Inaccurate | Complete | Rebuildable |
|--------|-------|----------|--------|------------|----------|-------------|
| SEC | 6 | 3 | 2 | 1 | 3 | 3 |
| DOC | 12 | 3 | 6 | 3 | 3 | 3 |
| WF | 13 | 9 | 2 | 2 | 10 | 11 |
| META | 8 | 7 | 1 | 0 | 8 | 8 |
| TASK/CFG | 9 | 6 | 2 | 1 | 5 | 5 |
| QUERY | 16 | 14 | 2 | 0 | 14 | 16 |
| **TOTAL** | **64** | **42** | **15** | **7** | **43** | **46** |

### Best Performing Domain: META (100% accurate, 100% complete)

The Metadata & Audit Trail requirements are well-written and match the implementation precisely.

### Domains Needing Most Work: DOC (50% inaccurate/partial), SEC (50% issues)

The Document Management and Security domains have the most discrepancies between specification and implementation.

---

**Report Generated:** 2026-01-19
**Auditor:** AUDITOR Agent
**Input Sources:** A1-SEC, A2-DOC, A3-WF, A4-META, A5-TASK, A6-QUERY domain reports

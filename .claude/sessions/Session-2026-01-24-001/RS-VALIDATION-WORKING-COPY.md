# SDLC-QMS-RS Validation Report — Working Copy

**Original Date:** 2026-01-19
**Working Copy Created:** 2026-01-24
**Purpose:** Track discussion outcomes for CR preparation

---

## Discussion Log

This section tracks decisions made during requirement-by-requirement discussion.

| REQ ID | Status | Decision Summary | Date |
|--------|--------|------------------|------|
| REQ-SEC-001 | DISCUSSED | Update to four groups; add administrator group | 2026-01-24 |
| REQ-SEC-002 | DISCUSSED | Rewrite with hierarchical group model; remove quality from route; strengthen with "only permit/reject" | 2026-01-24 |
| REQ-SEC-003 | DISCUSSED | Strengthen with "reject" language; CODE FIX to remove cross-initiator exception | 2026-01-24 |
| REQ-SEC-004 | DISCUSSED | Clarify dual-gate; strengthen with "reject unless" pattern | 2026-01-24 |
| REQ-SEC-005 | DISCUSSED | No change needed; references approve rules | 2026-01-24 |
| REQ-SEC-006 | DISCUSSED | No change needed; validated as accurate | 2026-01-24 |
| REQ-SEC-008 | DISCUSSED | NEW — Workspace/Inbox Isolation | 2026-01-24 |
| REQ-DOC-001 | DISCUSSED | Simplify; add SDLC namespace architecture (SC-002); strengthen with "only/reject" | 2026-01-24 |
| REQ-DOC-002 | DISCUSSED | No REQ change; CODE FIX for TP sequential IDs | 2026-01-24 |
| REQ-DOC-003 | DISCUSSED | Add boundary rejection clause | 2026-01-24 |
| REQ-DOC-004 | PENDING | |
| REQ-DOC-005 | DISCUSSED | No REQ change; CC-007 aligns code with REQ | 2026-01-24 |
| REQ-DOC-006 | PENDING | |
| REQ-DOC-007 | DISCUSSED | Add archive step for effective checkout | 2026-01-24 |
| REQ-DOC-008 | DISCUSSED | Fix incorrect archive claim; add workspace deletion | 2026-01-24 |
| REQ-DOC-009 | DISCUSSED | Simplify (all revert to DRAFT); add field clearing | 2026-01-24 |
| REQ-DOC-010 | DISCUSSED | Add --confirm, checkout check, cleanup behaviors | 2026-01-24 |
| REQ-DOC-011 | DISCUSSED | No REQ change; CODE FIX to make --name required | 2026-01-24 |
| REQ-DOC-012 | DISCUSSED | DELETE — superseded by REQ-DOC-014, REQ-DOC-015 | 2026-01-24 |
| REQ-DOC-013 | DISCUSSED | NEW — Folder-per-Document Storage | 2026-01-24 |
| REQ-WF-001 | PENDING | |
| REQ-WF-002 | PENDING | |
| REQ-WF-003 | DISCUSSED | No change; CAPA removal resolves issue | 2026-01-24 |
| REQ-WF-004 | PENDING | |
| REQ-WF-005 | DISCUSSED | REVISED: Add quality gate requirement; CODE FIX to implement | 2026-01-24 |
| REQ-WF-006 | DISCUSSED | Clarify responsible_user only cleared for non-executable | 2026-01-24 |
| REQ-WF-007 | PENDING | |
| REQ-WF-008 | PENDING | |
| REQ-WF-009 | PENDING | |
| REQ-WF-010 | PENDING | |
| REQ-WF-011 | PENDING | |
| REQ-WF-012 | DISCUSSED | No REQ change; CODE FIX to implement version check | 2026-01-24 |
| REQ-WF-013 | PENDING | |
| REQ-WF-014 | DISCUSSED | NEW — Execution Phase Tracking | 2026-01-24 |
| REQ-WF-015 | DISCUSSED | NEW — Checked-in Requirement for Routing | 2026-01-24 |
| REQ-META-002 | DISCUSSED | Add boundary clause for compliance violation | 2026-01-24 |
| REQ-META-* | PENDING | Domain scored 100% accurate |
| REQ-TASK-003 | DISCUSSED | DELETE — replaced by quality gate in REQ-WF-005 | 2026-01-24 |
| REQ-TASK-004 | DISCUSSED | Add bulk removal on rejection | 2026-01-24 |
| REQ-TASK-005 | DISCUSSED | NEW — Assign Command | 2026-01-24 |
| REQ-TASK-* | PENDING | |
| REQ-CFG-004 | DISCUSSED | Update groups (SC-001); add permission registry | 2026-01-24 |
| REQ-CFG-005 | DISCUSSED | Skip singleton flag; add SDLC namespace registry | 2026-01-24 |
| REQ-CFG-* | PENDING | |
| REQ-QRY-007 | DISCUSSED | NEW — Comments Visibility Restriction | 2026-01-24 |
| REQ-QUERY-* | PENDING | |
| REQ-PROMPT-006 | DISCUSSED | No REQ change; CODE FIX to render custom_header/footer | 2026-01-24 |
| REQ-PROMPT-* | PENDING | |
| REQ-TEMPLATE-003 | DISCUSSED | Fix placeholder syntax documentation | 2026-01-24 |
| REQ-TEMPLATE-005 | DISCUSSED | NEW — Fallback Template Generation | 2026-01-24 |
| REQ-TEMPLATE-* | PENDING | |

---

## REQ Strengthening (Style Guide Compliance)

These rewrites apply the RDD style guide principles to strengthen existing requirements with closed-system language.

### High-Impact Rewrites

**REQ-SEC-002** (in addition to SC-001 group restructuring):

*Before:*
> The CLI shall authorize actions based on user group membership...

*After:*
> The CLI shall **only permit** actions when the user's group is authorized per the PERMISSIONS registry. The CLI shall **reject** any action for which the user's group is not explicitly permitted.

---

**REQ-SEC-003** (strengthening):

*Before:*
> The CLI shall restrict checkin, route, release, revert, and close actions to the document's responsible_user (owner).

*After:*
> The CLI shall **reject** checkin, route, release, revert, and close commands when the user is not the document's responsible_user.

---

**REQ-SEC-004** (in addition to dual-gate revision):

*Before:*
> The CLI shall permit review and approve actions only for users listed in the document's pending_assignees.

*After:*
> The CLI shall **reject** review and approve actions unless the user is: (1) listed in the document's pending_assignees, AND (2) a member of an authorized group for that action.

---

**REQ-DOC-001** (in addition to SC-002 type changes):

*Before:*
> The CLI shall support creation and management of the following document types...

*After:*
> The CLI shall **only** support creation and management of the following document types... The CLI shall **reject** create commands for undefined document types.

---

### Medium-Impact Rewrites

**REQ-DOC-003** (add boundary clause):

*Current:*
> The CLI shall maintain the following folder structure...

*Addition:*
> ...The CLI shall **reject** operations that would store controlled documents outside this structure.

---

**REQ-META-002** (add boundary clause):

*Current:*
> The CLI shall be the sole mechanism for modifying .meta/ sidecar files. Workflow state (version, status, responsible_user, pending_assignees) shall never be stored in document frontmatter.

*Addition:*
> ...Direct modification of .meta/ files outside the CLI constitutes a compliance violation and may result in undefined behavior.

---

### Already Strong (No Change Needed)

These REQs already follow good constraint patterns:
- **REQ-SEC-006**: "shall reject any command..."
- **REQ-WF-001**: "shall reject any status transition..."
- **REQ-WF-011**: "shall reject all transitions from terminal states"
- **REQ-AUDIT-001**: "shall never modify or delete..."
- **REQ-DOC-010**: "shall only permit cancellation..."
- **REQ-WF-012**: "shall only be permitted for..."

---

## Structural Changes (Cross-Cutting)

These changes affect multiple requirements:

### SC-001: User Group Restructuring

**Decision:** Restructure user groups with hierarchical model.

| Old Group | New Group | Members | Notes |
|-----------|-----------|---------|-------|
| initiators | administrator | lead, claude | Inherits initiator + fix |
| (new) | initiator | (empty) | Placeholder for future non-admin initiators |
| qa | quality | qa | Renamed to singular; disambiguates from username |
| reviewers | reviewer | tu_ui, tu_scene, tu_sketch, tu_sim, bu | Renamed to singular |

**Hierarchy:** Administrator extends initiator permissions, adding `fix`.

**Affected Requirements:** REQ-SEC-001, REQ-SEC-002, REQ-SEC-003, REQ-SEC-004

---

### SC-002: SDLC Namespace Architecture

**Decision:** Implement programmatic SDLC namespace management.

**Current State (problematic):**
- Namespaces (FLOW, QMS) are hardcoded in `qms_paths.py`, `qms_schema.py`
- Adding a namespace requires editing 3 source files
- Document types include obsolete entries (DS, CS, OQ)
- CAPA listed as document type but is actually an EI type within INV

**New Architecture:**
1. **Namespace registry** in config (or separate config section)
2. **Dynamic resolution** — `qms_paths.py` and `qms_schema.py` read from registry
3. **`qms namespace add <NAME>` command** — registers namespace and creates `QMS/SDLC-<NAME>/` directory
4. **RS and RTM available per namespace** — no other SDLC doc types needed

**Removals:**
- CAPA from DOCUMENT_TYPES (EI type, not standalone)
- DS, CS, OQ from DOCUMENT_TYPES (obsolete)
- QMS-RS, QMS-RTM as separate types (become RS/RTM in QMS namespace)

**Affected Requirements:** REQ-DOC-001, REQ-DOC-012 (plus new REQs for namespace command)

**Affected Code:**
- `qms_config.py` — add SDLC_NAMESPACES registry, remove obsolete types
- `qms_paths.py` — refactor `get_doc_type()` for dynamic namespace lookup
- `qms_schema.py` — refactor `DOC_ID_PATTERNS` for dynamic patterns
- New `commands/namespace.py` — implement `qms namespace add`

---

## Discussed Requirements — Final Wording

### REQ-SEC-001: User Group Classification (REVISED)

**Original:**
> The CLI shall classify all users into exactly one of three groups: Initiators, QA, or Reviewers.

**Revised:**
> The CLI shall classify all users into exactly one of four groups: administrator, initiator, quality, or reviewer. The administrator group inherits all initiator permissions.

---

### REQ-SEC-002: Group-Based Action Authorization (REVISED)

**Original:**
> The CLI shall authorize actions based on user group membership: create, checkout, checkin, route, release, revert, close (Initiators); assign (QA); fix (QA, lead).

**Revised:**
> The CLI shall **only permit** actions when the user's group is authorized per the PERMISSIONS registry:
> - **initiator** (and administrator): create, checkout, checkin, route, release, revert, close
> - **quality:** assign
> - **administrator:** fix
>
> The CLI shall **reject** any action for which the user's group is not explicitly permitted.

**Note:** Route was previously granted to quality (CR-032) but this was dead code — the owner-only check in route.py always blocked non-owners. Quality has been removed from route to simplify the permission model.

**Rationale (strengthening):** Applied RDD style guide Rule 1 ("shall only") and Rule 2 (explicit rejection).

---

### REQ-SEC-003: Owner-Only Restrictions (REVISED)

**Original:**
> The CLI shall restrict checkin, route, release, revert, and close actions to the document's responsible_user (owner).

**Revised:**
> The CLI shall **reject** checkin, route, release, revert, and close commands when the user is not the document's responsible_user.

**Rationale (strengthening):** Changed from "restrict" to explicit "reject" per RDD style guide Rule 2.

**Code Change Required:** Remove the undocumented cross-initiator exception at `qms_auth.py:86-88`. The code currently allows any initiator to act on documents owned by another initiator; this exception should be removed to enforce strict owner-only behavior as specified.

---

### REQ-SEC-004: Assignment-Based Review and Approval Access (REVISED)

**Original:**
> The CLI shall permit review and approve actions only for users listed in the document's pending_assignees.

**Revised:**
> The CLI shall **reject** review and approve actions unless the user meets both conditions:
> 1. Listed in the document's pending_assignees, AND
> 2. Member of an authorized group for that action
>
> Authorized groups:
> - **review:** administrator, initiator, quality, reviewer
> - **approve:** quality, reviewer

**Rationale:** Documents the dual-gate authorization (group membership + assignment). Initiator-level users can review but cannot approve.

**Rationale (strengthening):** Changed from "permit only" to "reject unless" per RDD style guide Rule 2.

---

### REQ-SEC-007: Assignment Validation (NEW)

**Proposed:**
> The CLI shall validate workflow assignments to ensure only authorized users are assigned:
> - **Review workflows:** Only users in administrator, initiator, quality, or reviewer groups may be assigned
> - **Approval workflows:** Only users in quality or reviewer groups may be assigned
>
> The CLI shall reject assignment attempts for users who would not be authorized to complete the workflow action.

**Rationale:** Prevents permission mismatches where a user is assigned but cannot complete the action. Assignment validation matches completion permissions.

**Code Change Required:** Add group validation to `assign` command and `route --assign` handling.

---

### REQ-DOC-001: Supported Document Types (REVISED)

**Original:**
> The CLI shall support creation and management of the following document types: SOP, CR, INV, TP, ER, VAR, RS, RTM, and TEMPLATE.

**Revised:**
> The CLI shall **only** support creation and management of the following document types:
> - **Core types:** SOP, CR, INV, TP, ER, VAR, TEMPLATE
> - **SDLC types:** RS, RTM (available per registered SDLC namespace)
>
> The CLI shall **reject** create commands for undefined document types.

**Rationale:**
- Removed CAPA (EI type within INV, not a standalone document type)
- Removed DS, CS, OQ (obsolete)
- RS/RTM are now dynamically available per namespace rather than hardcoded per-namespace variants

**Rationale (strengthening):** Added "only" and explicit rejection clause per RDD style guide Rules 1 and 2.

---

### REQ-DOC-014: SDLC Namespace Registration (NEW)

**Proposed:**
> The CLI shall support SDLC namespace registration via the `namespace add` command:
> - `qms namespace add <NAME>` registers a new SDLC namespace
> - Registration creates the `QMS/SDLC-<NAME>/` directory structure
> - Registration enables RS and RTM document types for that namespace (e.g., `SDLC-MYPROJ-RS`, `SDLC-MYPROJ-RTM`)
>
> Registered namespaces shall be persisted in configuration.

**Rationale:** Enables users to add SDLC projects without editing source code. Supports the tool's use beyond the original FLOW and QMS namespaces.

---

### REQ-DOC-015: SDLC Document Identification (NEW)

**Proposed:**
> SDLC documents shall be identified by the pattern `SDLC-<NAMESPACE>-<TYPE>` where:
> - `<NAMESPACE>` is a registered SDLC namespace
> - `<TYPE>` is RS or RTM
>
> The CLI shall resolve document type and path dynamically from the namespace registry.

**Rationale:** Replaces hardcoded namespace handling in `qms_paths.py` and `qms_schema.py` with dynamic lookup.

---

### REQ-DOC-003: QMS Folder Structure (REVISED)

**Original:**
> The CLI shall maintain the following folder structure: QMS/ for controlled documents organized by type; QMS/.meta/ for workflow state sidecar files; QMS/.audit/ for audit trail logs; QMS/.archive/ for superseded versions; and per-user workspace and inbox directories.

**Revised:**
> The CLI shall maintain the following folder structure: QMS/ for controlled documents organized by type; QMS/.meta/ for workflow state sidecar files; QMS/.audit/ for audit trail logs; QMS/.archive/ for superseded versions; and per-user workspace and inbox directories. The CLI shall **reject** operations that would store controlled documents outside this structure.

**Rationale:** Added explicit boundary constraint per RDD style guide Rule 2.

---

### REQ-DOC-007: Checkout Behavior (REVISED)

**Original:**
> The CLI shall permit checkout of any document not currently checked out by another user. On checkout, the CLI shall: (1) copy the document to the user's workspace, (2) set the user as responsible_user, (3) mark the document as checked_out, and (4) if the document is EFFECTIVE, create a new draft version at N.1.

**Revised:**
> The CLI shall permit checkout of any document not currently checked out by another user. On checkout, the CLI shall: (1) copy the document to the user's workspace, (2) set the user as responsible_user, (3) mark the document as checked_out, and (4) if the document is EFFECTIVE, archive the current effective version and create a new draft version at N.1.

**Rationale:** Documents the archive step that occurs when checking out an effective document for revision.

---

### REQ-DOC-008: Checkin Updates QMS (REVISED)

**Original:**
> When a user checks in a document, the CLI shall: (1) copy the document from workspace to QMS working directory, (2) archive any previous draft version, and (3) maintain the user as responsible_user.

**Revised:**
> When a user checks in a document, the CLI shall: (1) copy the document from workspace to QMS working directory, (2) remove the workspace copy, and (3) maintain the user as responsible_user.

**Rationale:** Drafts are NOT archived on checkin (this was incorrect). Workspace copy deletion was undocumented.

---

### REQ-DOC-009: Checkin Reverts Reviewed Status (REVISED)

**Original:**
> When a document in REVIEWED, PRE_REVIEWED, or POST_REVIEWED status is checked in, the CLI shall revert the status to DRAFT (for non-executable) or the appropriate pre-review state (for executable) to require a new review cycle.

**Revised:**
> When a document in REVIEWED, PRE_REVIEWED, or POST_REVIEWED status is checked in, the CLI shall revert the status to DRAFT and clear all review tracking fields (pending_assignees, review outcomes) to require a new review cycle.

**Rationale:** Code treats all document types the same (revert to DRAFT). Removed executable distinction that wasn't implemented. Added field clearing behavior.

---

### REQ-DOC-010: Cancel Restrictions (REVISED)

**Original:**
> The CLI shall only permit cancellation of documents with version < 1.0 (never approved). Cancellation shall permanently delete the document file, metadata, and audit trail.

**Revised:**
> The CLI shall only permit cancellation of documents with version < 1.0 (never approved) that are not currently checked out. Cancellation requires the `--confirm` flag and shall permanently delete the document file, metadata, audit trail, any workspace copies, and any related inbox tasks.

**Rationale:** Documents the --confirm safety requirement, checkout restriction, and full cleanup scope.

---

### REQ-WF-005: Approval Gate (REVISED)

**Original:**
> The CLI shall block routing for approval if any reviewer submitted a review with `request-updates` outcome. All reviews must have `recommend` outcome before approval routing is permitted.

**Revised:**
> The CLI shall block routing for approval unless:
> 1. All submitted reviews have `recommend` outcome (no `request-updates`), AND
> 2. At least one review was submitted by a quality group member
>
> This ensures both unanimous recommendation and mandatory quality oversight before approval.

**Rationale:** Replaces the removed REQ-TASK-003 (QA auto-assignment) with a gate check. Instead of forcing QA assignment at routing time, the system enforces that quality must have participated and recommended before approval can proceed. This is more flexible — any combination of reviewers can be assigned, but approval is blocked until quality has reviewed.

---

### REQ-WF-006: Approval Version Bump (REVISED)

**Original:**
> Upon successful approval (all approvers complete), the CLI shall: (1) increment the major version (N.X → N+1.0), (2) archive the previous version, (3) transition to EFFECTIVE (non-executable) or PRE_APPROVED/POST_APPROVED (executable), and (4) clear the responsible_user.

**Revised:**
> Upon successful approval (all approvers complete), the CLI shall: (1) increment the major version (N.X → N+1.0), (2) archive the previous version, (3) transition to EFFECTIVE (non-executable) or PRE_APPROVED/POST_APPROVED (executable), and (4) for non-executable documents, clear the responsible_user.

**Rationale:** Executable documents retain their owner during execution phase; only non-executable documents have owner cleared upon becoming effective.

---

### REQ-TASK-003: QA Auto-Assignment (DELETED)

**Original:**
> When routing for review, the CLI shall automatically add QA to the pending_assignees list regardless of explicit assignment.

**Decision:** DELETE this requirement.

**Rationale:** The auto-assignment behavior was inaccurate (code used fallback, not additive logic). Rather than fixing the code or requirement, this functionality is replaced by the quality gate in REQ-WF-005. The new approach:
- Does NOT force quality assignment at review routing time
- DOES require quality participation before approval routing
- More flexible: any reviewers can be assigned, but quality oversight is enforced at the approval gate

---

### REQ-TASK-004: Task Removal on Completion (REVISED)

**Original:**
> When a user completes a review or approval action, the CLI shall remove their corresponding task file from their inbox.

**Revised:**
> When a user completes a review or approval action, the CLI shall remove their corresponding task file from their inbox. Additionally, when a document is rejected during approval, the CLI shall remove ALL pending approval tasks for that document from ALL user inboxes.

**Rationale:** Documents the bulk removal behavior on rejection. When one approver rejects, the pending tasks for other approvers become invalid and should be cleaned up.

---

### REQ-CFG-004: User Registry (REVISED)

**Original:**
> The CLI shall maintain a registry of valid users, including: (1) the set of all valid user identifiers, and (2) group membership for each user (Initiators, QA, or Reviewers).

**Revised:**
> The CLI shall maintain a registry of valid users, including: (1) the set of all valid user identifiers, and (2) group membership for each user (administrator, initiator, quality, or reviewer). The CLI shall also maintain a permission registry mapping commands to: (1) authorized groups, (2) owner_only modifier (restricts to document owner), and (3) assigned_only modifier (restricts to assigned users).

**Rationale:**
- Updates group names per SC-001 restructuring
- Documents the PERMISSIONS configuration that controls command authorization with modifiers

---

### REQ-CFG-005: Document Type Registry (REVISED)

**Original:**
> The CLI shall maintain a registry of document types, including for each type: (1) storage path relative to QMS root, (2) executable flag, (3) ID prefix, (4) parent type (if child document), and (5) folder-per-document flag.

**Revised:**
> The CLI shall maintain a registry of document types, including for each type: (1) storage path relative to QMS root, (2) executable flag, (3) ID prefix, (4) parent type (if child document), and (5) folder-per-document flag. The CLI shall also maintain an SDLC namespace registry enabling dynamic RS and RTM document types per registered namespace.

**Rationale:**
- Singleton flag not added — singletons (DS, CS, OQ) are removed per SC-002, and TEMPLATE now requires explicit naming (CC-008)
- Added SDLC namespace registry per SC-002 architecture

---

### REQ-META-002: CLI-Exclusive Metadata Management (REVISED)

**Original:**
> The CLI shall be the sole mechanism for modifying .meta/ sidecar files. Workflow state (version, status, responsible_user, pending_assignees) shall never be stored in document frontmatter.

**Revised:**
> The CLI shall be the sole mechanism for modifying .meta/ sidecar files. Workflow state (version, status, responsible_user, pending_assignees) shall never be stored in document frontmatter. Direct modification of .meta/ files outside the CLI constitutes a compliance violation and may result in undefined behavior.

**Rationale:** Added explicit boundary clause per RDD style guide Rule 2.

---

### REQ-PROMPT-006: Custom Sections (NO CHANGE)

**Original:**
> Prompt configurations shall support custom header text, custom footer text, additional named sections, and critical reminder lists that are included in the generated prompt.

**Decision:** No requirement change needed. Requirement is correct; code needs to implement.

**Code Change Required:** CC-011 — Implement rendering of custom_header and custom_footer fields in prompt output.

---

### REQ-TEMPLATE-003: Variable Substitution (REVISED)

**Original:**
> Templates shall support variable placeholders that the CLI substitutes at creation time. Required variables include: `{DOC_ID}` for the generated document ID, and `{TITLE}` for the user-provided title.

**Revised:**
> Templates shall support variable placeholders that the CLI substitutes at creation time. Supported patterns:
> - `{{TITLE}}` — substituted with user-provided title (double braces)
> - `{TYPE}-XXX` — substituted with generated document ID (e.g., `CR-XXX` becomes `CR-029`)

**Rationale:** Documents the actual placeholder syntax used in the codebase.

---

### REQ-SEC-008: Workspace/Inbox Isolation (NEW)

**Proposed:**
> The CLI shall restrict workspace and inbox operations to the requesting user's own directories. Users shall not access, view, or modify other users' workspaces or inboxes.

**Rationale:** Documents existing security boundary implemented in `qms_auth.py:121-135` (`verify_folder_access`). Critical for multi-user integrity.

---

### REQ-DOC-013: Folder-per-Document Storage (NEW)

**Proposed:**
> CR and INV documents shall be stored in dedicated subdirectories using the pattern `QMS/{TYPE}/{DOC_ID}/`. Child documents (TP, VAR, ER, CAPA) shall be stored within their parent document's directory.

**Rationale:** Documents the folder-per-document storage pattern that affects path resolution. Other document types (SOP, TEMPLATE) use flat storage.

---

### REQ-WF-014: Execution Phase Tracking (NEW)

**Proposed:**
> For executable document types (CR, INV), the CLI shall track execution phase in metadata:
> - `pre_release`: Document approved but not yet released (PRE_APPROVED state)
> - `post_release`: Document released and execution complete (POST_APPROVED state)
>
> The execution phase determines the correct workflow path (pre-release vs post-release review/approval cycles).

**Rationale:** Documents the phase tracking that distinguishes pre-release from post-release workflows for executable documents.

---

### REQ-WF-015: Checked-in Requirement for Routing (NEW)

**Proposed:**
> The CLI shall require documents to be checked in before routing for review or approval. Routing shall be rejected with an error if the document is currently checked out.

**Rationale:** Documents existing behavior that prevents routing while document is being edited.

---

### REQ-QRY-007: Comments Visibility Restriction (NEW)

**Proposed:**
> The CLI shall restrict visibility of document comments during active workflow states. Comments shall not be displayed when a document is in IN_REVIEW or IN_APPROVAL status.

**Rationale:** Documents existing behavior that hides comments during active review/approval to prevent bias.

---

### REQ-TASK-005: Assign Command (NEW)

**Proposed:**
> The CLI shall provide an `assign` command allowing quality group members to add reviewers or approvers to a document after initial routing. Assignment shall validate that assignees are authorized for the workflow type per REQ-SEC-007.

**Rationale:** Documents existing `assign` command functionality for QA to manage workflow participants.

---

### REQ-TEMPLATE-005: Fallback Template Generation (NEW)

**Proposed:**
> When creating a document for which no template file exists, the CLI shall generate a minimal document structure containing: (1) YAML frontmatter with title and revision_summary fields, and (2) placeholder heading with document ID.

**Rationale:** Documents existing fallback behavior when template files are missing.

---

## Code Changes Required

This section tracks code modifications identified during requirement review.

### CC-001: Remove Cross-Initiator Exception

**File:** `qms-cli/qms_auth.py`
**Lines:** 86-88
**Current Code:**
```python
if user_group == "initiators" and doc_owner in USER_GROUPS.get("initiators", set()):
    pass  # Allow initiators to act on each other's documents
```
**Action:** Remove this exception block. Owner-only restrictions should be strictly enforced.
**Related REQ:** REQ-SEC-003

---

### CC-002: Remove Quality from Route Permission

**File:** `qms-cli/qms_config.py`
**Line:** 119
**Current Code:**
```python
"route":     {"groups": ["initiators", "qa"], "owner_only": True},  # CR-032
```
**New Code:**
```python
"route":     {"groups": ["initiators"], "owner_only": True},
```
**Action:** Remove `"qa"` from route groups. The owner-only check makes this permission dead code for QA (they can never be owner because they can't checkout). Simplify by removing.
**Related REQ:** REQ-SEC-002

**Note:** With SC-001 group restructuring, this will become `["administrator", "initiator"]`.

---

### CC-003: Add Assignment Validation

**Files:** `qms-cli/commands/assign.py`, `qms-cli/commands/route.py`

**Action:** Add validation when assigning users to workflows:
- Review workflows: Validate assignees are in `["administrator", "initiator", "quality", "reviewer"]`
- Approval workflows: Validate assignees are in `["quality", "reviewer"]`

Reject with clear error message if assignee's group is not authorized for the workflow type.

**Related REQ:** REQ-SEC-007 (new)

---

### CC-004: Remove Obsolete Document Types

**File:** `qms-cli/qms_config.py`

**Action:** Remove from DOCUMENT_TYPES:
- `CAPA` (EI type, not standalone document)
- `DS`, `CS`, `OQ` (obsolete SDLC types)
- `QMS-RS`, `QMS-RTM` (replaced by dynamic namespace lookup)

Keep only: SOP, CR, INV, TP, ER, VAR, RS, RTM, TEMPLATE

**Related REQ:** REQ-DOC-001

---

### CC-005: Implement SDLC Namespace Registry

**Files:**
- `qms-cli/qms_config.py` — Add `SDLC_NAMESPACES` registry (initially `{"FLOW", "QMS"}`)
- `qms-cli/qms_paths.py` — Refactor `get_doc_type()` to dynamically match `SDLC-<NAMESPACE>-<TYPE>` pattern against registry
- `qms-cli/qms_schema.py` — Refactor `DOC_ID_PATTERNS` to generate patterns dynamically from namespace registry

**Action:** Replace hardcoded `SDLC-FLOW-` and `SDLC-QMS-` handling with dynamic lookup:
```python
# Example new logic in get_doc_type()
for namespace in SDLC_NAMESPACES:
    prefix = f"SDLC-{namespace}-"
    if doc_id.startswith(prefix):
        suffix = doc_id[len(prefix):]
        if suffix in ["RS", "RTM"]:
            return suffix  # or return (namespace, suffix) tuple
```

**Related REQ:** REQ-DOC-015

---

### CC-006: Implement Namespace Add Command

**File:** `qms-cli/commands/namespace.py` (new)

**Action:** Create `qms namespace add <NAME>` command that:
1. Validates namespace name (uppercase alphanumeric)
2. Adds namespace to `SDLC_NAMESPACES` registry
3. Creates `QMS/SDLC-<NAME>/` directory
4. Creates corresponding `.meta/` and `.audit/` directories
5. Persists namespace to config (file-based or in qms_config.py)

**Related REQ:** REQ-DOC-014

---

### CC-007: Make TP Sequential (Remove Singular Exception)

**Files:** `qms-cli/commands/create.py`, `qms-cli/qms_paths.py`, `qms-cli/qms_schema.py`

**Current behavior:** TP uses singular ID format `CR-001-TP` (one TP per CR)

**New behavior:** TP uses sequential ID format `CR-001-TP-001`, `CR-001-TP-002` (multiple TPs per CR, like VAR)

**Action:**
- Update `create.py` TP ID generation to use sequential numbering
- Update `qms_paths.py` pattern matching for TP IDs
- Update `qms_schema.py` regex pattern for TP validation

**Rationale:** Eliminates special case; TP now follows same pattern as VAR and ER.

**Related REQ:** REQ-DOC-002, REQ-DOC-005

---

### CC-008: Make TEMPLATE --name Required

**File:** `qms-cli/commands/create.py`

**Current behavior:** `--name` is optional for TEMPLATE; falls back to sequential (TEMPLATE-001)

**New behavior:** `--name` is required for TEMPLATE; error if not provided

**Action:**
- Add validation in `create.py` that requires `--name` when `doc_type == "TEMPLATE"`
- Remove sequential fallback for TEMPLATE
- Return clear error message: "TEMPLATE documents require --name argument"

**Rationale:** REQ-DOC-011 says "name shall be specified at creation time". Code should enforce this.

**Related REQ:** REQ-DOC-011

---

### CC-009: Implement Approval Gate (Review Outcome + Quality Check)

**Files:** `qms-cli/commands/route.py`, `qms-cli/qms_meta.py`, `qms-cli/qms_config.py`

**Current behavior:** Approval routing is always permitted regardless of review outcomes

**New behavior:** Block approval routing unless:
1. All reviews have `recommend` outcome (no `request-updates`)
2. At least one review was submitted by a quality group member

**Action:**
1. Store review outcomes in metadata with reviewer identity (add to `update_meta_review_complete()`)
   - Store as list of `{reviewer: username, outcome: RECOMMEND|UPDATES_REQUIRED}`
2. In `route.py`, when `--approval` is specified:
   - Query stored review outcomes from metadata
   - Check 1: If any outcome is `UPDATES_REQUIRED`, reject with error: "Cannot route for approval: reviewer X requested updates"
   - Check 2: If no reviewer is in the quality group, reject with error: "Cannot route for approval: no quality review on record"
   - Only permit approval routing if both checks pass

**Related REQ:** REQ-WF-005

**Note:** This replaces the deleted REQ-TASK-003 auto-assignment behavior with a gate check.

---

### CC-010: Implement Retirement Version Check

**File:** `qms-cli/commands/route.py`

**Current behavior:** Any document can be routed for retirement

**New behavior:** Only documents with version >= 1.0 can be routed for retirement

**Action:**
- In `route.py`, when `--retire` flag is present:
  - Check document version from metadata
  - If major version < 1, reject with error: "Cannot retire document that was never effective (version < 1.0)"

**Related REQ:** REQ-WF-012

---

### CC-011: Implement Custom Header/Footer Rendering

**File:** `qms-cli/prompts.py`

**Current behavior:** `custom_header` and `custom_footer` fields are loaded from prompt YAML but not rendered in output

**New behavior:** Render custom_header at start of prompt and custom_footer at end

**Action:**
- In `prompts.py`, modify prompt generation to:
  - If `custom_header` is present, render it before the main prompt content
  - If `custom_footer` is present, render it after the main prompt content

**Related REQ:** REQ-PROMPT-006

---

## Original Report Content

*(Below is the original validation report for reference)*

---

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

**DISCUSSION OUTCOME:** See "Discussed Requirements — Final Wording" section above. Adopting hierarchical group model with administrator group.

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

**DISCUSSION OUTCOME:** PENDING

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

**DISCUSSION OUTCOME:** PENDING

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

**DISCUSSION OUTCOME:** PENDING

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

**DISCUSSION OUTCOME:** PENDING — Decision required

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

**DISCUSSION OUTCOME:** PENDING — Decision required

---

### 3.7 REQ-TASK-003: QA Auto-Assignment

**Current Text:**
> When routing for review, the CLI shall automatically add QA to the pending_assignees list regardless of explicit assignment.

**Issue:** QA is the DEFAULT assignee only when NO explicit `--assign` argument is provided. This is fallback behavior, not additive behavior.

**Evidence:** route.py:132 (`assignees = args.assign if args.assign else ['qa']`)

**Recommended Fix:**
> When routing for review, if no explicit assignees are specified via the --assign argument, the CLI shall default to assigning QA. When explicit assignees are provided, only those assignees shall be added to pending_assignees.

**DISCUSSION OUTCOME:** PENDING

---

## 4. Requirements Needing Revision (Should Fix)

These requirements are accurate but incomplete or need clarification.

### 4.1 Security Domain

| REQ | Issue | Recommended Change |
|-----|-------|-------------------|
| REQ-SEC-003 | Missing initiator cross-action exception | Add: "Exception: Any Initiator may perform owner-only actions on documents owned by another Initiator." |
| REQ-SEC-004 | Dual-gate nuance not captured | Clarify: "Both group membership AND assignment are required. Note: Initiators may review but cannot approve." |

**DISCUSSION OUTCOME:** PENDING — Will need to update for new group names

---

### 4.2 Document Management Domain

| REQ | Issue | Recommended Change |
|-----|-------|-------------------|
| REQ-DOC-002 | Missing CAPA as child of INV | Add CAPA to child relationships |
| REQ-DOC-005 | TP uses singular ID format | Clarify: "TP uses singular format (CR-001-TP), VAR and ER use sequential (CR-001-VAR-001)" |
| REQ-DOC-007 | Missing archive-on-effective behavior | Add: "If the document is EFFECTIVE, archive the current version before creating the draft" |
| REQ-DOC-009 | Missing review field clearing | Add: "The CLI shall also clear pending_assignees and review tracking fields" |
| REQ-DOC-010 | Missing --confirm and checkout check | Add: "--confirm flag required; checked-out documents cannot be cancelled" |
| REQ-DOC-011 | Missing --name optional behavior | Clarify: "--name is optional; if omitted, sequential fallback (TEMPLATE-001) is used" |

**DISCUSSION OUTCOME:** PENDING

---

### 4.3 Workflow Domain

| REQ | Issue | Recommended Change |
|-----|-------|-------------------|
| REQ-WF-003 | Missing CAPA | Add CAPA to list of executable document types |
| REQ-WF-006 | responsible_user clearing nuance | Clarify: "Clear responsible_user only for non-executable documents transitioning to EFFECTIVE" |

**DISCUSSION OUTCOME:** PENDING

---

### 4.4 Task & Config Domain

| REQ | Issue | Recommended Change |
|-----|-------|-------------------|
| REQ-TASK-004 | Missing bulk removal on rejection | Add: "Rejection removes ALL pending approval tasks across ALL user inboxes" |
| REQ-CFG-004 | Missing permission modifiers | Add: "Including command-level permissions with owner_only and assigned_only modifiers" |
| REQ-CFG-005 | Missing singleton flag | Add: "singleton flag for name-based (not sequential) document identification" |

**DISCUSSION OUTCOME:** PENDING

---

### 4.5 Query/Template Domain

| REQ | Issue | Recommended Change |
|-----|-------|-------------------|
| REQ-PROMPT-006 | custom_header/footer not rendered | Clarify: "These fields are loaded but not currently rendered in prompt output" |
| REQ-TEMPLATE-003 | Wrong placeholder syntax | Update: "{{TITLE}} (double braces) and {TYPE}-XXX pattern (e.g., CR-XXX becomes CR-029)" |

**DISCUSSION OUTCOME:** PENDING

---

## 5. Missing Requirements (New REQs Needed)

### 5.1 Critical (P1) - Must Add

| Proposed ID | Feature | Justification |
|-------------|---------|---------------|
| REQ-SEC-007 | **Workspace/Inbox Isolation** | Security boundary: users cannot access other users' workspace or inbox directories. Implemented in qms_auth.py:121-135 |
| REQ-DOC-013 | **Folder-per-Document Storage** | CR and INV documents are stored in dedicated subdirectories (QMS/CR/CR-001/). Affects path resolution. |
| REQ-WF-014 | **Execution Phase Tracking** | Metadata tracks pre_release vs post_release phase to determine correct workflow path for executable documents. |

**DISCUSSION OUTCOME:** PENDING

---

### 5.2 Moderate (P2) - Should Add

| Proposed ID | Feature | Justification |
|-------------|---------|---------------|
| REQ-WF-015 | **Checked-in Requirement for Routing** | Documents must be checked in before routing for review or approval. |
| REQ-DOC-014 | **Archive Lifecycle** | Consolidated documentation of when archives are created (checkout effective, approval, retirement). |
| REQ-QRY-007 | **Comments Visibility Restriction** | Comments not visible during active IN_REVIEW or IN_APPROVAL states. |
| REQ-TASK-005 | **Assign Command** | QA can add reviewers/approvers after initial routing. |

**DISCUSSION OUTCOME:** PENDING

---

### 5.3 Minor (P3) - Nice to Have

| Proposed ID | Feature | Justification |
|-------------|---------|---------------|
| REQ-TEMPLATE-005 | **Fallback Template Generation** | When no template file exists, CLI generates minimal structure automatically. |

**DISCUSSION OUTCOME:** PENDING

---

## 6. Cross-Domain Issues

### 6.1 Document Type List Inconsistency

**Affected:** REQ-DOC-001, REQ-WF-003, REQ-SEC-002

The document type list appears in multiple requirements with different subsets. Recommend:
- Define authoritative list in REQ-DOC-001
- Other requirements should reference REQ-DOC-001 rather than re-listing

**DISCUSSION OUTCOME:** PENDING

---

### 6.2 Review Outcome Storage Gap

**Affected:** REQ-WF-005, REQ-META-003, REQ-AUDIT-003

REQ-WF-005 expects review outcomes to be queryable for approval gating, but:
- Outcomes are logged to audit trail (append-only, not designed for queries)
- Outcomes are NOT stored in .meta/ where they would be accessible

This is an architectural gap. Resolution options:
1. Add review_outcomes to REQ-META-003 required fields and implement
2. Remove REQ-WF-005 approval gate requirement

**DISCUSSION OUTCOME:** PENDING

---

### 6.3 Archive Behavior Documentation

**Affected:** REQ-DOC-007, REQ-DOC-008, REQ-WF-006, REQ-WF-013

Archive triggers are scattered across multiple requirements. Consider consolidating into a single REQ-DOC-014 for clarity.

**DISCUSSION OUTCOME:** PENDING

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

**DISCUSSION OUTCOME:** PENDING

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

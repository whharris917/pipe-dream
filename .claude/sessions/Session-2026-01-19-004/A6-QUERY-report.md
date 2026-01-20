# A6-QUERY: Query, Prompt & Template Domain Review

## Summary
- Total REQs reviewed: 16
- Accurate: 14
- Accurate with issues: 2
- Inaccurate: 0

## Requirement Analysis

---

### REQ-QRY-001: Document Reading

**Requirement**: The CLI shall provide the ability to read any document's content. Reading shall support: (1) the current effective version, (2) the current draft version if one exists, and (3) any archived version by version number.

**Assessment**: ACCURATE
**Completeness**: COMPLETE
**Rebuildability**: SUFFICIENT

**Evidence**:
- `qms-cli/commands/read.py` lines 28-54 implement the read command
- Lines 33-42 implement all three reading modes:
  - `--version` flag: reads archived version via `get_archive_path(doc_id, args.version)` (line 35)
  - `--draft` flag: reads draft via `get_doc_path(doc_id, draft=True)` (line 37)
  - Default: reads effective version with fallback to draft (lines 40-42)
- `qms_paths.py` lines 113-140 implement `get_archive_path()` for versioned retrieval

**Issues**: None

**Recommendation**: PASS

---

### REQ-QRY-002: Document Status Query

**Requirement**: The CLI shall provide the ability to query a document's current workflow state, including: doc_id, title, version, status, document type, executable flag, responsible_user, and checked_out status.

**Assessment**: ACCURATE
**Completeness**: COMPLETE
**Rebuildability**: SUFFICIENT

**Evidence**:
- `qms-cli/commands/status.py` lines 26-73 implement the status command
- All required fields are displayed (lines 51-59):
  - `doc_id`: line 51 (`Document: {doc_id}`)
  - `title`: line 52 (from frontmatter)
  - `version`: line 53 (from meta)
  - `status`: line 54 (from meta)
  - `doc_type`: line 56 (`Type: {doc_type}`)
  - `executable`: line 57 (from meta)
  - `responsible_user`: line 58 (from meta)
  - `checked_out`: line 59 (from meta)
- Additional info displayed: `location` (line 55), `effective_version` (lines 61-62), `pending_assignees` (lines 64-71)

**Issues**: None

**Recommendation**: PASS

---

### REQ-QRY-003: Audit History Query

**Requirement**: The CLI shall provide the ability to retrieve the complete audit trail for a document, displaying all recorded events in chronological order.

**Assessment**: ACCURATE
**Completeness**: COMPLETE
**Rebuildability**: SUFFICIENT

**Evidence**:
- `qms-cli/commands/history.py` lines 26-54 implement the history command
- Line 37: `events = read_audit_log(doc_id, doc_type)` retrieves all events
- `qms_audit.py` lines 85-109 implement `read_audit_log()`:
  - Reads JSONL file line by line (lines 97-105)
  - Returns events in order they appear (chronological, since append-only)
- Lines 50-52 in history.py format and display the complete history via `format_audit_history(events)`
- `qms_audit.py` lines 313-401 implement comprehensive event formatting

**Issues**: None

**Recommendation**: PASS

---

### REQ-QRY-004: Review Comments Query

**Requirement**: The CLI shall provide the ability to retrieve review comments for a document, filtered by version. Comments shall be extracted from REVIEW and REJECT events in the audit trail.

**Assessment**: ACCURATE
**Completeness**: COMPLETE
**Rebuildability**: SUFFICIENT

**Evidence**:
- `qms-cli/commands/comments.py` lines 30-81 implement the comments command
- Line 27: `--version` flag for filtering by version
- Lines 63-68 handle version filtering:
  - Specific version: `get_comments(doc_id, doc_type, version=args.version)`
  - Current version: `get_latest_version_comments(doc_id, doc_type, version)`
- `qms_audit.py` lines 112-144 implement `get_comments()`:
  - Default event types: `[EVENT_REVIEW, EVENT_REJECT]` (lines 129-130)
  - Version filtering at line 140-141
- `qms_audit.py` lines 147-157 implement `get_latest_version_comments()`

**Issues**: None

**Recommendation**: PASS

---

### REQ-QRY-005: Inbox Query

**Requirement**: The CLI shall provide the ability for a user to list all pending tasks in their inbox, showing task type, document ID, and assignment date.

**Assessment**: ACCURATE
**Completeness**: COMPLETE
**Rebuildability**: SUFFICIENT

**Evidence**:
- `qms-cli/commands/inbox.py` lines 24-53 implement the inbox command
- Lines 45-51 display each task with required fields:
  - Task type: line 47 (`[{frontmatter.get('task_type', '?')}]`)
  - Document ID: line 47 (`{frontmatter.get('doc_id', '?')}`)
  - Assignment date: line 50 (`Date: {frontmatter.get('assigned_date', '?')}`)
- Additional info displayed: workflow_type (line 48), assigned_by (line 49)

**Issues**: None

**Recommendation**: PASS

---

### REQ-QRY-006: Workspace Query

**Requirement**: The CLI shall provide the ability for a user to list all documents currently checked out to their workspace.

**Assessment**: ACCURATE
**Completeness**: COMPLETE
**Rebuildability**: SUFFICIENT

**Evidence**:
- `qms-cli/commands/workspace.py` lines 24-52 implement the workspace command
- Line 31: `workspace_path = USERS_ROOT / user / "workspace"`
- Line 37: `docs = list(workspace_path.glob("*.md"))` lists all docs
- Lines 45-50 display each document with doc_id, version, and status

**Issues**: None

**Recommendation**: PASS

---

### REQ-PROMPT-001: Task Prompt Generation

**Requirement**: When creating task files for review or approval, the CLI shall generate structured prompt content that guides the assigned user through the task.

**Assessment**: ACCURATE
**Completeness**: COMPLETE
**Rebuildability**: SUFFICIENT

**Evidence**:
- `qms-cli/prompts.py` lines 443-573 implement `generate_review_content()` for review tasks
- `qms-cli/prompts.py` lines 575-661 implement `generate_approval_content()` for approval tasks
- `qms-cli/qms_templates.py` lines 34-67 delegate to `PromptRegistry` methods
- Generated content includes:
  - Frontmatter with task metadata (lines 498-506, 611-619)
  - Task header (lines 508-514, 621-627)
  - Verification checklist (lines 516-523, 629-641)
  - Response format guidance (lines 525-557, 643-660)
  - Critical reminders (lines 549-557, 643-647)

**Issues**: None

**Recommendation**: PASS

---

### REQ-PROMPT-002: YAML-Based Configuration

**Requirement**: Prompt content shall be configurable via external YAML files stored in the `prompts/` directory. The CLI shall not require code changes to modify prompt content.

**Assessment**: ACCURATE
**Completeness**: COMPLETE
**Rebuildability**: SUFFICIENT

**Evidence**:
- `qms-cli/prompts.py` line 57: `PROMPTS_DIR = Path(__file__).parent / "prompts"`
- Lines 60-121 implement `load_config_from_yaml()` for loading YAML files
- Lines 124-176 implement `get_prompt_file_path()` for locating YAML files
- Lines 420-425 in `get_config()` try file-based lookup first before falling back to in-memory defaults
- YAML files exist in `qms-cli/prompts/` directory (confirmed via Glob)

**Issues**: None

**Recommendation**: PASS

---

### REQ-PROMPT-003: Hierarchical Prompt Lookup

**Requirement**: The CLI shall resolve prompt configuration using hierarchical lookup: (1) document-type and workflow-phase specific (e.g., `review/post_review/cr.yaml`), (2) workflow-phase specific (e.g., `review/post_review/default.yaml`), (3) task-type default (e.g., `review/default.yaml`). The first matching configuration shall be used.

**Assessment**: ACCURATE
**Completeness**: COMPLETE
**Rebuildability**: SUFFICIENT

**Evidence**:
- `qms-cli/prompts.py` lines 124-176 implement `get_prompt_file_path()`:
  - Lines 157-159: First tries `{task_type}/{workflow_type}/{doc_type}.yaml` (exact match)
  - Lines 162-165: Then tries `{task_type}/{workflow_type}/default.yaml` (workflow default)
  - Lines 167-169: Finally tries `{task_type}/default.yaml` (task type default)
  - Lines 172-174: Returns first matching path
- Example files exist confirming hierarchy:
  - `prompts/review/post_review/cr.yaml` (doc-type specific)
  - `prompts/review/post_review/default.yaml` (workflow default)
  - `prompts/review/default.yaml` (task type default)

**Issues**: None

**Recommendation**: PASS

---

### REQ-PROMPT-004: Checklist Generation

**Requirement**: Review and approval prompts shall include a verification checklist. Each checklist item shall specify a category and verification item text. Items may optionally include an evidence prompt.

**Assessment**: ACCURATE
**Completeness**: COMPLETE
**Rebuildability**: SUFFICIENT

**Evidence**:
- `qms-cli/prompts.py` lines 24-28 define `ChecklistItem` dataclass with `category`, `item`, and optional `evidence_prompt`
- YAML parsing at lines 81-98 supports both simple string items and dict items with `evidence_prompt`
- Review prompt generation at lines 470-488 groups items by category and renders checklist tables
- Approval prompt generation at lines 602-606 renders checklist with YES/NO verification
- Example YAML (`review/post_review/cr.yaml`) shows structure with categories and evidence prompts (lines 5-13)

**Issues**: None

**Recommendation**: PASS

---

### REQ-PROMPT-005: Prompt Content Structure

**Requirement**: Generated prompts shall include: (1) task header identifying the document and workflow phase, (2) verification checklist organized by category, (3) critical reminders section, and (4) response format guidance.

**Assessment**: ACCURATE
**Completeness**: COMPLETE
**Rebuildability**: SUFFICIENT

**Evidence**:
- `qms-cli/prompts.py` `generate_review_content()` lines 498-573:
  1. Task header: lines 508-514 (`# REVIEW REQUEST: {doc_id}`, workflow, version, date)
  2. Verification checklist: lines 516-523, organized by category (lines 470-488)
  3. Critical reminders: lines 549-557 (`## CRITICAL REMINDERS` with reminders_text)
  4. Response format guidance: lines 525-547 (`## STRUCTURED REVIEW RESPONSE FORMAT`)
- Approval prompts at lines 611-661 follow similar structure

**Issues**: None

**Recommendation**: PASS

---

### REQ-PROMPT-006: Custom Sections

**Requirement**: Prompt configurations shall support custom header text, custom footer text, additional named sections, and critical reminder lists that are included in the generated prompt.

**Assessment**: ACCURATE with minor issue
**Completeness**: INCOMPLETE
**Rebuildability**: SUFFICIENT

**Evidence**:
- `qms-cli/prompts.py` lines 31-49 define `PromptConfig` with all custom fields:
  - `custom_header` (line 47)
  - `custom_footer` (line 48)
  - `additional_sections` (line 46)
  - `critical_reminders` (line 45)
- YAML loading at lines 101-117 parses all these fields
- Review prompt generation at lines 491-496 renders `additional_sections`

**Issues**:
- `custom_header` and `custom_footer` fields are loaded but NOT rendered in the generated prompts. Lines 494-496 add additional_sections but custom_header/custom_footer are not used in the template strings (lines 498-573 for review, 611-661 for approval).
- The requirement says they "are included in the generated prompt" but the code loads them without using them.

**Recommendation**: REVISE - Either update the code to actually use custom_header/custom_footer, or update the requirement to indicate these are loaded but not currently rendered (deferred feature).

---

### REQ-TEMPLATE-001: Template-Based Creation

**Requirement**: When creating a new document, the CLI shall populate the document with initial content from a template appropriate to the document type.

**Assessment**: ACCURATE
**Completeness**: COMPLETE
**Rebuildability**: SUFFICIENT

**Evidence**:
- `qms-cli/qms_templates.py` lines 150-196 implement `load_template_for_type()`
- Line 157-158: Constructs template path as `QMS/TEMPLATE/TEMPLATE-{doc_type}.md`
- Lines 160-161: Falls back to minimal template if not found
- Lines 163-196: Parses template, extracts example frontmatter and body, performs substitution

**Issues**: None

**Recommendation**: PASS

---

### REQ-TEMPLATE-002: Template Location

**Requirement**: Document templates shall be stored in `QMS/TEMPLATE/` as controlled documents following the naming convention `TEMPLATE-{TYPE}.md` (e.g., `TEMPLATE-CR.md`, `TEMPLATE-SOP.md`).

**Assessment**: ACCURATE
**Completeness**: COMPLETE
**Rebuildability**: SUFFICIENT

**Evidence**:
- `qms-cli/qms_templates.py` lines 157-158:
  ```python
  template_id = f"TEMPLATE-{doc_type}"
  template_path = QMS_ROOT / "TEMPLATE" / f"{template_id}.md"
  ```
- This exactly matches the naming convention: `QMS/TEMPLATE/TEMPLATE-{TYPE}.md`

**Issues**: None

**Recommendation**: PASS

---

### REQ-TEMPLATE-003: Variable Substitution

**Requirement**: Templates shall support variable placeholders that the CLI substitutes at creation time. Required variables include: `{DOC_ID}` for the generated document ID, and `{TITLE}` for the user-provided title.

**Assessment**: ACCURATE with notation difference
**Completeness**: COMPLETE
**Rebuildability**: SUFFICIENT

**Evidence**:
- `qms-cli/qms_templates.py` lines 187-189:
  ```python
  body = body.replace("{{TITLE}}", title)
  body = body.replace(f"{doc_type}-XXX", doc_id)
  ```
- Title substitution uses `{{TITLE}}` placeholder
- Doc ID substitution uses `{TYPE}-XXX` pattern (e.g., `CR-XXX` becomes `CR-029`)

**Issues**:
- The requirement specifies `{DOC_ID}` placeholder syntax, but the code uses `{TYPE}-XXX` pattern substitution.
- The requirement specifies `{TITLE}` but the code uses `{{TITLE}}` (double braces).
- This is a notation difference, not a functional gap - both achieve the stated goal.

**Recommendation**: REVISE - Update requirement to match actual implementation: "Required variables include: `{{TITLE}}` for the user-provided title. The document ID is substituted by replacing the `{TYPE}-XXX` pattern (e.g., `CR-XXX`) with the generated document ID."

---

### REQ-TEMPLATE-004: Frontmatter Initialization

**Requirement**: The CLI shall initialize new documents with valid YAML frontmatter containing the `title` field (from user input or default) and `revision_summary` field (set to "Initial draft").

**Assessment**: ACCURATE
**Completeness**: COMPLETE
**Rebuildability**: SUFFICIENT

**Evidence**:
- `qms-cli/qms_templates.py` lines 191-194:
  ```python
  frontmatter = {
      "title": title,
      "revision_summary": "Initial draft",
  }
  ```
- This exactly matches the requirement for both fields and the default value.

**Issues**: None

**Recommendation**: PASS

---

## Undocumented Functionality

### 1. Comments Visibility Restrictions (comments.py lines 52-60)

The `comments` command enforces visibility rules that prevent viewing comments while a document is in active review states (`IN_REVIEW`, `IN_PRE_REVIEW`, `IN_POST_REVIEW`). This access control behavior is not documented in REQ-QRY-004.

**Recommendation**: ADD_REQ or update REQ-QRY-004 to include: "Comments shall not be visible while the document is in an active review state (IN_REVIEW, IN_PRE_REVIEW, IN_POST_REVIEW)."

### 2. Legacy Frontmatter Migration Notice (comments.py lines 74-77, history.py lines 44-46)

Both commands include special handling for pre-migration documents that have frontmatter history but no audit log. They display notices suggesting the user run `qms migrate`. This is operational guidance, not core functionality, so no requirement needed.

### 3. Prompt Registry Legacy Fallback (prompts.py lines 427-441)

The prompt system has a complete in-memory registry (`_register_defaults()`, lines 360-372) that serves as fallback when YAML files are missing. The hierarchy includes:
- (task_type, workflow_type, doc_type) - exact match
- (task_type, workflow_type, None) - any doc type
- (task_type, None, doc_type) - any workflow
- (task_type, None, None) - task type default
- (None, None, None) - global default

This provides more granular fallback than REQ-PROMPT-003 describes. The requirement only covers file-based lookup; the in-memory fallback is undocumented.

**Recommendation**: Consider documenting the in-memory fallback behavior in an informative note, or simply leave it as implementation detail since YAML files are the primary configuration mechanism.

### 4. Status Command Shows Additional Fields (status.py lines 61-71)

The status command displays `effective_version` and `pending_assignees` (showing reviewers or approvers depending on status). These are useful but not listed in REQ-QRY-002.

**Recommendation**: Consider expanding REQ-QRY-002 to include optional additional fields, or leave as implementation enhancement.

### 5. Template Comment Stripping (qms_templates.py lines 110-119)

The `strip_template_comments()` function removes the `TEMPLATE DOCUMENT NOTICE` block from templates when creating new documents. This is a cleanup function that preserves the `TEMPLATE USAGE GUIDE` for authors. Not documented but reasonable implementation detail.

### 6. Minimal Fallback Template (qms_templates.py lines 122-147)

When no template file exists for a document type, `create_minimal_template()` generates a basic structure. This fallback behavior is hinted at in REQ-TEMPLATE-001 ("populate... from a template") but the fallback mechanism is not explicit.

**Recommendation**: Consider adding a note to REQ-TEMPLATE-001: "If no template exists for the document type, the CLI shall generate a minimal document structure."

---

## Recommended Actions

### Priority 1: Revisions Required

1. **REQ-PROMPT-006 (Custom Sections)**: The requirement states that custom_header and custom_footer "are included in the generated prompt" but the code does not render them. Either:
   - Update the code to use these fields, OR
   - Revise the requirement to clarify they are supported for future use but not currently rendered

2. **REQ-TEMPLATE-003 (Variable Substitution)**: Update to match actual placeholder syntax:
   - Change `{DOC_ID}` to `{TYPE}-XXX` pattern description
   - Change `{TITLE}` to `{{TITLE}}`

### Priority 2: Consider Adding Requirements

3. **Comments Visibility**: Add requirement or update REQ-QRY-004 to document that comments are not visible during active review phases.

4. **Fallback Template**: Consider adding note to REQ-TEMPLATE-001 about minimal fallback template generation when no template file exists.

### Priority 3: No Action Required (Implementation Details)

5. In-memory prompt registry fallback - acceptable implementation detail
6. Additional status fields - enhancement beyond requirements
7. Template comment stripping - reasonable implementation behavior
8. Migration notices - operational guidance, not core functionality

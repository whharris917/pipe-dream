# A5-TASK: Task & Configuration Domain Review

## Summary
- Total REQs reviewed: 9
- Accurate: 6
- Accurate with issues: 2
- Inaccurate: 1

---

## Requirement Analysis

### REQ-TASK-001
**Assessment**: ACCURATE
**Completeness**: COMPLETE
**Rebuildability**: SUFFICIENT
**Evidence**:
- `route.py` lines 153-185: Iterates through `assignees` list and creates task files in each user's inbox
- `assign.py` lines 127-158: Also creates tasks when additional users are assigned via `qms assign`
- Task path: `get_inbox_path(assignee) / f"{task_id}.md"`
**Issues**: None
**Recommendation**: PASS

---

### REQ-TASK-002
**Assessment**: ACCURATE
**Completeness**: COMPLETE
**Rebuildability**: SUFFICIENT
**Evidence**:
- `prompts.py` lines 498-506 (review) and 611-619 (approval) generate frontmatter with:
  - `task_id: {task_id}` - unique identifier (format: `task-{doc_id}-{workflow_type.lower()}-v{version.replace('.', '-')}`)
  - `task_type: REVIEW` or `APPROVAL`
  - `workflow_type: {workflow_type}`
  - `doc_id: {doc_id}`
  - `version: {version}`
  - `assigned_by: {assigned_by}`
  - `assigned_date: {today()}`
**Issues**: None - all fields specified in REQ-TASK-002 are present
**Recommendation**: PASS

---

### REQ-TASK-003
**Assessment**: INACCURATE
**Completeness**: INCOMPLETE
**Rebuildability**: INSUFFICIENT
**Evidence**:
- `route.py` line 132: `assignees = args.assign if args.assign else ["qa"]`
- This sets QA as the DEFAULT assignee only when no `--assign` argument is provided
- It does NOT "automatically add QA to the pending_assignees list regardless of explicit assignment"
- If user specifies `--assign tu_ui tu_scene`, QA is NOT added
**Issues**:
- REQ-TASK-003 claims QA is auto-assigned "regardless of explicit assignment" but the code shows QA is only assigned when NO explicit assignment is provided (fallback behavior, not additive behavior)
- The requirement is misleading about actual behavior
**Recommendation**: REVISE - Change to: "When routing for review without explicit assignees, the CLI shall default to assigning QA. When explicit assignees are provided via --assign, only those assignees receive tasks."

---

### REQ-TASK-004
**Assessment**: ACCURATE
**Completeness**: INCOMPLETE
**Rebuildability**: INSUFFICIENT
**Evidence**:
- `review.py` lines 152-155: Removes task from reviewer's inbox after review
  ```python
  inbox_path = get_inbox_path(user)
  for task_file in inbox_path.glob(f"task-{doc_id}-*.md"):
      task_file.unlink()
  ```
- `approve.py` lines 176-179: Same pattern for approval
- `reject.py` lines 111-117: Removes ALL pending approval tasks across ALL users:
  ```python
  for user_dir in USERS_ROOT.iterdir():
      if user_dir.is_dir():
          inbox = user_dir / "inbox"
          if inbox.exists():
              for task_file in inbox.glob(f"task-{doc_id}-*approval*.md"):
                  task_file.unlink()
  ```
**Issues**:
- REQ does not specify the different task removal behaviors for review (individual) vs reject (bulk removal across all users)
- The glob pattern `task-{doc_id}-*.md` removes all tasks for that doc_id (review + approval) - this is different for reject which only removes approval tasks
**Recommendation**: REVISE - Expand to specify: "When reviewing, the CLI removes only the current user's task. When rejecting, the CLI removes all pending approval tasks for the document across all user inboxes."

---

### REQ-CFG-001
**Assessment**: ACCURATE
**Completeness**: COMPLETE
**Rebuildability**: SUFFICIENT
**Evidence**:
- `qms_paths.py` lines 17-29 `find_project_root()`:
  ```python
  current = Path.cwd()
  while current != current.parent:
      if (current / "QMS").is_dir():
          return current
      current = current.parent
  ```
- Also includes fallback logic for current directory and parent directory checks
**Issues**: None
**Recommendation**: PASS

---

### REQ-CFG-002
**Assessment**: ACCURATE
**Completeness**: COMPLETE
**Rebuildability**: SUFFICIENT
**Evidence**:
- `qms_paths.py` lines 33-34:
  ```python
  PROJECT_ROOT = find_project_root()
  QMS_ROOT = PROJECT_ROOT / "QMS"
  ```
- All document paths resolved relative to QMS_ROOT (see `get_doc_path()`, `get_archive_path()`)
**Issues**: None
**Recommendation**: PASS

---

### REQ-CFG-003
**Assessment**: ACCURATE
**Completeness**: COMPLETE
**Rebuildability**: SUFFICIENT
**Evidence**:
- `qms_paths.py` line 36:
  ```python
  USERS_ROOT = PROJECT_ROOT / ".claude" / "users"
  ```
- Used by `get_workspace_path()` (line 143-145) and `get_inbox_path()` (line 148-150)
**Issues**: None
**Recommendation**: PASS

---

### REQ-CFG-004
**Assessment**: ACCURATE
**Completeness**: INCOMPLETE
**Rebuildability**: INSUFFICIENT
**Evidence**:
- `qms_config.py` line 104:
  ```python
  VALID_USERS = {"lead", "claude", "qa", "bu", "tu_ui", "tu_scene", "tu_sketch", "tu_sim"}
  ```
- `qms_config.py` lines 107-111:
  ```python
  USER_GROUPS = {
      "initiators": {"lead", "claude"},
      "qa": {"qa"},
      "reviewers": {"tu_ui", "tu_scene", "tu_sketch", "tu_sim", "bu"},
  }
  ```
**Issues**:
- REQ says "Initiators, QA, or Reviewers" but actual code also has PERMISSIONS dict (lines 115-131) which controls what actions each group can perform
- The group guidance messages (lines 134-171) are undocumented
- REQ doesn't mention that permissions are defined per-command with additional modifiers like `owner_only` and `assigned_only`
**Recommendation**: REVISE - Expand to include: "The CLI shall also maintain command-level permissions specifying which groups can execute each command, with optional modifiers for owner-only or assigned-only access."

---

### REQ-CFG-005
**Assessment**: ACCURATE
**Completeness**: INCOMPLETE
**Rebuildability**: INSUFFICIENT
**Evidence**:
- `qms_config.py` lines 78-96 `DOCUMENT_TYPES`:
  ```python
  DOCUMENT_TYPES = {
      "SOP": {"path": "SOP", "executable": False, "prefix": "SOP"},
      "CR": {"path": "CR", "executable": True, "prefix": "CR", "folder_per_doc": True},
      "INV": {"path": "INV", "executable": True, "prefix": "INV", "folder_per_doc": True},
      "CAPA": {"path": "INV", "executable": True, "prefix": "CAPA", "parent_type": "INV"},
      # ... etc
  }
  ```
**Issues**:
- REQ lists 5 attributes but code also has `singleton` flag (used for SDLC documents like RS, RTM) - see lines 86-93
- Example: `"RS": {"path": "SDLC-FLOW", "executable": False, "prefix": "SDLC-FLOW-RS", "singleton": True}`
- Singleton documents are name-based rather than numbered (different ID generation logic)
**Recommendation**: REVISE - Add: "(6) singleton flag indicating name-based rather than numbered identification"

---

## Undocumented Functionality

### 1. Archive Path Resolution (`qms_paths.py` lines 113-140)
- `get_archive_path()` function resolves archive paths for versioned document storage
- Archive path structure mirrors QMS structure but under `.archive/` directory
- Not covered by any REQ-CFG requirement

### 2. Next Document Number Generation (`qms_paths.py` lines 153-201)
- `get_next_number()` scans existing documents to determine next sequential ID
- `get_next_nested_number()` handles child document numbering (e.g., CR-028-VAR-001)
- Not covered by any requirement

### 3. Document Type Detection (`qms_paths.py` lines 43-69)
- `get_doc_type()` parses doc_id to determine document type
- Complex prefix matching logic for SDLC documents, nested documents, etc.
- Not covered by any requirement

### 4. Task Assignment via `assign` Command
- `assign.py` allows QA to add additional reviewers/approvers AFTER initial routing
- Creates inbox tasks for newly assigned users
- Updates `pending_assignees` in meta
- This is a separate workflow from route-time assignment
- REQ-TASK-001 mentions routing but not the assign command

### 5. Task Filename Format
- Task files are named: `task-{doc_id}-{workflow_type.lower()}-v{version.replace('.', '-')}.md`
- This naming convention enables glob-based task removal
- Not explicitly documented in requirements

### 6. Transition Rules (`qms_config.py` lines 47-71)
- `TRANSITIONS` dict defines valid status transitions
- Complex branching for executable vs non-executable workflows
- Not covered by REQ-CFG section (likely should be in workflow requirements)

### 7. Author-Maintainable Frontmatter Fields (`qms_config.py` line 179)
- `AUTHOR_FRONTMATTER_FIELDS = {"title", "revision_summary"}`
- Defines which frontmatter fields authors can modify (vs system-managed fields)
- Not documented

### 8. Group Guidance Messages (`qms_config.py` lines 134-171)
- User-facing help text explaining permissions per group
- Displayed when permission denied
- Not documented

---

## Recommended Actions

### Priority 1 - Accuracy Corrections
1. **REVISE REQ-TASK-003**: Current wording incorrectly describes QA auto-assignment as unconditional. Actual behavior is QA is assigned by default ONLY when no explicit assignees provided.

### Priority 2 - Completeness Improvements
2. **REVISE REQ-TASK-004**: Expand to document different task removal behaviors (individual vs bulk on rejection).

3. **REVISE REQ-CFG-004**: Add documentation of command-level permissions with modifiers.

4. **REVISE REQ-CFG-005**: Add singleton flag to document type registry specification.

### Priority 3 - New Requirements for Coverage
5. **ADD_REQ**: Archive path resolution and versioned document storage structure.

6. **ADD_REQ**: Document ID generation (sequential numbering and nested document numbering).

7. **ADD_REQ**: Document type detection from ID parsing.

8. **ADD_REQ**: Task assignment workflow via `assign` command (separate from routing).

9. **ADD_REQ**: Task filename format specification.

---

## Code Quality Observations

The codebase is well-structured with clear separation between:
- Path resolution (`qms_paths.py`)
- Configuration constants (`qms_config.py`)
- Command implementations (`commands/*.py`)
- Template/prompt generation (`qms_templates.py`, `prompts.py`)

The requirements capture the high-level behaviors but miss several implementation details that would be necessary for rebuilding the system from requirements alone.

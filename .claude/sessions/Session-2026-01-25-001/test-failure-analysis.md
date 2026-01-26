# Deep-Dive Analysis: 6 Test Failures in CR-036-VAR-003

**Date:** 2026-01-25
**Analyst:** Claude
**Context:** VAR-003 EI execution revealed 6 tests marked as xfail - per Lead's feedback, these are FAILURES, not passes

---

## Executive Summary

All 6 failing tests reveal **true implementation gaps in qms-cli**. These are not test design issues - the tests correctly identify missing or buggy functionality. A VAR-005 (Type 1) will be required to fix the underlying code bugs.

| Test | Root Cause | Severity |
|------|------------|----------|
| `test_create_er_under_tp` | ER document type not handled in create command | HIGH |
| `test_document_type_registry` | ER creation fails, cascading test failure | HIGH |
| `test_all_audit_event_types` | ASSIGN event never logged | MEDIUM |
| `test_terminal_state_superseded` | `--supersedes` flag doesn't exist | MEDIUM |
| `test_task_content_all_fields` | Task files missing 3 of 7 required fields | MEDIUM |
| `test_project_root_discovery_via_config` | Subdirectory discovery not implemented | LOW |

---

## Detailed Analysis

### Failure 1: `test_create_er_under_tp` (test_document_types.py:618)

**Requirement:** REQ-DOC-001, REQ-DOC-002
**Test Purpose:** Verify ER (Execution Record) can be created as child of TP

**Root Cause Analysis:**

The `create.py` command (lines 60-79) only handles `VAR` and `TP` for parent document validation:

```python
if doc_type in ("VAR", "TP"):  # <-- ER is missing!
    if not parent_id:
        print(f"Error: {doc_type} documents require --parent flag")
        ...
```

When ER is passed with `--parent`, it falls through to the generic ID generation (line 108):
```python
else:
    next_num = get_next_number(doc_type)
    doc_id = f"{config['prefix']}-{next_num:03d}"  # Generates "ER-001"
```

The generated ID "ER-001" is then not recognized by `get_doc_type()` in `qms_paths.py` because:
- It checks for `-TP-ER-` pattern (line 57-58)
- "ER-001" doesn't match this pattern
- Result: `ValueError: Unknown document type for: ER-001`

**Fix Required:**
1. Add `"ER"` to the parent-requiring types in `create.py`
2. Validate ER parent must be a TP (not CR or other types)
3. Generate nested ID: `CR-001-TP-001-ER-001`

---

### Failure 2: `test_document_type_registry` (test_document_types.py:656)

**Requirement:** REQ-CFG-005
**Test Purpose:** Verify document type registry correctly tracks executable flag and parent types

**Root Cause Analysis:**

This test fails because it attempts to create an ER document (line 683-685):
```python
# Create ER under TP to test child executable type
result = run_qms(temp_project, "claude", "create", "ER", "--parent", "CR-001-TP-001", ...)
```

This triggers the same bug as Failure 1 - ER creation doesn't work at all. The test is correct; the implementation is incomplete.

**Fix Required:**
Same as Failure 1 - fixing ER creation will also fix this test.

---

### Failure 3: `test_all_audit_event_types` (test_cr_lifecycle.py:592)

**Requirement:** REQ-AUDIT-002
**Test Purpose:** Verify all 14 required audit event types are logged

**Root Cause Analysis:**

Examined `assign.py` (lines 160-163):
```python
if added:
    # Update .meta with new pending_assignees
    meta["pending_assignees"] = pending_assignees
    write_meta(doc_id, doc_type, meta)
    # <-- NO log_assign() call here!
```

Examined `qms_audit.py` (lines 18-32):
```python
EVENT_CREATE = "CREATE"
EVENT_CHECKOUT = "CHECKOUT"
...
EVENT_STATUS_CHANGE = "STATUS_CHANGE"
# <-- NO EVENT_ASSIGN defined!
```

The assign command:
1. Does NOT define an `EVENT_ASSIGN` constant
2. Does NOT have a `log_assign()` function
3. Does NOT call any audit logging after assignment

**REQ-AUDIT-002 explicitly requires logging of the ASSIGN event type.**

**Fix Required:**
1. Add `EVENT_ASSIGN = "ASSIGN"` constant to `qms_audit.py`
2. Add `log_assign()` function to `qms_audit.py`
3. Call `log_assign()` in `assign.py` after successful assignment

---

### Failure 4: `test_terminal_state_superseded` (test_sop_lifecycle.py:714)

**Requirement:** REQ-WF-011
**Test Purpose:** Verify SUPERSEDED is a terminal state blocking workflow transitions

**Root Cause Analysis:**

The test attempts (line 739):
```python
run_qms(temp_project, "qa", "approve", "SOP-002", "--supersedes", "SOP-001")
```

Examined `approve.py` - the command registration (lines 27-32):
```python
@CommandRegistry.register(
    name="approve",
    help="Approve a document",
    requires_doc_id=True,
    doc_id_help="Document ID to approve",
)
```

There is NO `--supersedes` argument defined. The flag simply doesn't exist.

The Status enum in `qms_config.py` does include `SUPERSEDED`, but there's no mechanism to transition a document to this state.

**Fix Required:**
1. Add `--supersedes` argument to approve command registration
2. Implement logic in `cmd_approve()` to:
   - Validate the superseded document exists
   - Transition superseded document to SUPERSEDED status
   - Store reference in metadata (superseded_by field)
3. Block checkout/routing for SUPERSEDED documents

---

### Failure 5: `test_task_content_all_fields` (test_sop_lifecycle.py:763)

**Requirement:** REQ-TASK-002
**Test Purpose:** Verify all 7 required fields are present in task files

**Root Cause Analysis:**

Examined the task generation in `prompts.py` (lines 508-515):
```python
return f"""---
task_id: {task_id}
task_type: REVIEW
workflow_type: {workflow_type}
doc_id: {doc_id}
assigned_by: {assigned_by}
assigned_date: {today()}
version: {version}
---
```

**Fields Present (4):**
1. task_id (as `task_id`)
2. doc_id
3. version
4. assigned_date

**Fields Missing (3):**
5. **title** - document title not passed to generation function
6. **status** - current document status not passed
7. **responsible_user** - document owner not passed

The `generate_review_content()` function signature (line 443-451) doesn't even accept these parameters:
```python
def generate_review_content(
    self,
    doc_id: str,
    version: str,
    workflow_type: str,
    assignee: str,
    assigned_by: str,
    task_id: str,
    doc_type: str = ""
) -> str:
```

**Fix Required:**
1. Add `title`, `status`, `responsible_user` parameters to both `generate_review_content()` and `generate_approval_content()`
2. Update callers in `route.py` and `assign.py` to pass these values (read from meta)
3. Include these fields in the task file frontmatter

---

### Failure 6: `test_project_root_discovery_via_config` (test_init.py:388)

**Requirement:** REQ-CFG-001
**Test Purpose:** Verify project root discovered from subdirectory via qms.config.json

**Root Cause Analysis:**

Examined `qms_paths.py` `find_project_root()` (lines 17-29):
```python
def find_project_root() -> Path:
    """Find the project root by looking for QMS/ directory."""
    current = Path.cwd()
    while current != current.parent:
        if (current / "QMS").is_dir():
            return current
        current = current.parent
    # Fallback: assume we're in project root or .claude/
    if Path("QMS").is_dir():
        return Path.cwd()
    elif Path("../QMS").is_dir():
        return Path.cwd().parent
    raise FileNotFoundError("Cannot find QMS/ directory. Are you in the project?")
```

The function only looks for `QMS/` directory, not `qms.config.json`. While it does walk up the directory tree, the test creates a deep subdirectory (`some/nested/directory`) and expects discovery to work.

**Subtle Issue:** The function searches for `QMS/` and does walk parent directories. The test *should* work theoretically. Need to verify:
- Is the test running from the correct working directory?
- Is `subprocess.run(..., cwd=subdir)` correctly setting the working directory?

After re-reading the test (lines 398-404):
```python
# [REQ-CFG-001] Commands should work from subdirectory (finds root via config)
result = run_qms(subdir, "claude", "create", "SOP", "--title", "Discovery Test")
```

The `run_qms()` helper passes `cwd=subdir` to subprocess. The command runs from `some/nested/directory/`. Walking up should find `QMS/` at the project root.

**Possible Issue:** The init command creates qms.config.json but the path discovery prioritizes QMS/ over config file. However, the requirement REQ-CFG-001 states:
> "Project root SHALL be discovered via qms.config.json presence"

The implementation looks for QMS/, not qms.config.json. This is a requirement mismatch.

**Fix Required:**
1. Modify `find_project_root()` to first look for `qms.config.json`
2. Fall back to `QMS/` directory only if config not found
3. This aligns with REQ-CFG-001 intent: config file is the primary marker

---

## Summary of Fixes Required for VAR-005

| Bug ID | File(s) to Modify | Description |
|--------|-------------------|-------------|
| BUG-001 | `commands/create.py` | Add ER to parent-requiring types, generate nested ID |
| BUG-002 | `qms_audit.py`, `commands/assign.py` | Add EVENT_ASSIGN and log_assign() |
| BUG-003 | `commands/approve.py` | Add --supersedes flag and SUPERSEDED transition |
| BUG-004 | `prompts.py`, `commands/route.py`, `commands/assign.py` | Add 3 missing task fields |
| BUG-005 | `qms_paths.py` | Prioritize qms.config.json for root discovery |

---

## Impact Assessment

**Test Coverage Impact:**
- 6 tests marked xfail = 6 requirement gaps
- These gaps affect: REQ-DOC-001, REQ-DOC-002, REQ-CFG-001, REQ-CFG-005, REQ-WF-011, REQ-AUDIT-002, REQ-TASK-002

**Risk if Not Fixed:**
- ER document type is completely non-functional
- Audit trail incomplete for assign operations (compliance gap)
- Document supersession workflow broken
- Task files non-compliant with REQ-TASK-002
- Root discovery may fail in subdirectories

**Recommendation:**
Create CR-036-VAR-005 (Type 1) to:
1. Fix all 5 bugs identified above
2. Remove xfail markers from tests
3. Achieve full qualification test pass (123/123)

---

## Appendix: Test Function Locations

| Test | File | Line |
|------|------|------|
| test_create_er_under_tp | test_document_types.py | 618 |
| test_document_type_registry | test_document_types.py | 656 |
| test_all_audit_event_types | test_cr_lifecycle.py | 592 |
| test_terminal_state_superseded | test_sop_lifecycle.py | 714 |
| test_task_content_all_fields | test_sop_lifecycle.py | 763 |
| test_project_root_discovery_via_config | test_init.py | 388 |

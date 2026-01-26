---
title: Incorrect Code Modification Target During VAR-005 Execution
revision_summary: Updated root cause to focus on lack of technical controls; revised
  CAPA-003 to explore edit blocking for main submodule; restored execution sections
  to placeholders
---

# INV-006: Incorrect Code Modification Target During VAR-005 Execution

## 1. Purpose

This investigation addresses a procedural deviation that occurred during execution of CR-036-VAR-005. Code modifications intended for the qualification test environment were incorrectly applied to the main qms-cli submodule, requiring emergency rollback actions.

---

## 2. Scope

### 2.1 Context

The deviation was discovered when qualification tests failed after code modifications. Investigation revealed the modifications were made to the wrong target directory.

- **Triggering Event:** Qualification test failures during VAR-005 EI-17 execution
- **Related Document:** CR-036-VAR-005

### 2.2 Deviation Type

- **Type:** Procedural

### 2.3 Systems/Documents Affected

- `qms-cli/` (main submodule) - Incorrectly modified, then reverted
- `.test-env/test-project/qms-cli/` - Corrupted by file copy, then reverted
- CR-036-VAR-005 - Execution interrupted

---

## 3. Background

### 3.1 Expected Behavior

During CR-036-VAR-005 execution, code modifications should have been made to the test environment copy at `.test-env/test-project/qms-cli/` where qualification tests are executed.

### 3.2 Actual Behavior

Code modifications were made to the main `qms-cli/` submodule instead of the test environment copy. When tests failed, an attempt to copy the modified files to the test environment corrupted that environment due to incompatible code versions (the test-env version contains a `require_project_root` function that doesn't exist in the main copy).

### 3.3 Discovery

The deviation was discovered when running `pytest tests/qualification/` returned import errors, indicating the test environment was broken.

### 3.4 Timeline

| Date | Event |
|------|-------|
| 2026-01-25 | VAR-005 released for execution |
| 2026-01-25 | EI-1 through EI-16 executed - code changes made to wrong target (main qms-cli) |
| 2026-01-25 | EI-17 - Qualification tests failed |
| 2026-01-25 | Attempted fix by copying files - corrupted test environment |
| 2026-01-25 | Lead intervened, requested git rollback |
| 2026-01-25 | Emergency rollback executed via git checkout |

---

## 4. Description of Deviation(s)

### 4.1 Facts and Observations

1. CR-036-VAR-005 EI-1 through EI-15 specified code changes to fix qualification test failures
2. Abundant context existed that changes should target the test environment (test files themselves are in `.test-env/`)
3. The agent (claude) incorrectly modified files in `qms-cli/` (the main submodule) instead of `.test-env/test-project/qms-cli/`
4. Files modified in main submodule:
   - `commands/assign.py`, `commands/create.py`, `commands/migrate.py`, `commands/route.py`
   - `prompts.py`, `qms_audit.py`, `qms_config.py`, `qms_meta.py`
   - `qms_paths.py`, `qms_schema.py`, `qms_templates.py`
5. Qualification tests (EI-17) failed because changes weren't in the test environment
6. Attempting to copy modified files from main to test-env caused import errors due to code divergence between the two copies
7. Lead detected the issue and directed immediate emergency rollback via git

### 4.2 Evidence

- Git status in `qms-cli/` showed 11 modified files before rollback:
  ```
  modified: commands/assign.py, commands/create.py, commands/migrate.py,
            commands/route.py, prompts.py, qms_audit.py, qms_config.py,
            qms_meta.py, qms_paths.py, qms_schema.py, qms_templates.py
  ```
- Git status in `.test-env/test-project/qms-cli/` showed 16 modified files before rollback (11 code files + 5 test files)
- Import error after file copy: `require_project_root` function not found (exists in test-env version but not in main)
- No commits were made to either repository - all changes were working directory modifications only

---

## 5. Impact Assessment

### 5.1 Systems Affected

| System | Impact | Description |
|--------|--------|-------------|
| qms-cli (main) | Low | Uncommitted changes, easily reverted |
| .test-env qms-cli | Low | Uncommitted changes, easily reverted |

### 5.2 Documents Affected

| Document | Impact | Description |
|----------|--------|-------------|
| CR-036-VAR-005 | Medium | Execution interrupted, requires restart |

### 5.3 Other Impacts

- No commits were made, so no persistent damage occurred
- VAR-005 execution must restart with correct target

---

## 6. Root Cause Analysis

### 6.1 Contributing Factors

- Two separate qms-cli copies exist: main submodule and test environment
- The main submodule (`qms-cli/`) is directly editable by the agent
- Context consolidation may have lost awareness of the dual-repository structure
- No technical barrier prevented direct modification of the production codebase

### 6.2 Root Cause(s)

**Primary Root Cause:** Lack of technical controls preventing direct edits to production code

The agent had unrestricted write access to `pipe-dream/qms-cli/`, the production submodule. While abundant context existed indicating that code changes should target the test environment (`.test-env/test-project/qms-cli/`), no technical barrier prevented the agent from directly modifying production code.

The principle violated: **Changes to `pipe-dream/qms-cli/` should only occur via git operations (merge, pull, submodule update) after qualification has been completed in a test environment.** Direct code edits to the main submodule bypass this qualification gate.

---

## 7. Remediation Plan (CAPAs)

| CAPA | Type | Description | Implementation | Outcome | Verified By - Date |
|------|------|-------------|----------------|---------|---------------------|
| INV-006-CAPA-001 | Corrective | Verify both environments are clean and consistent | Ran `git status` in both `qms-cli/` and `.test-env/test-project/qms-cli/`. Both showed "nothing to commit, working tree clean" | Pass | claude - 2026-01-25 |
| INV-006-CAPA-002 | Corrective | Re-execute VAR-005 with correct target (test-env) | Re-executed EI-4 through EI-17 with all code changes targeting `.test-env/test-project/qms-cli/`. All 113 qualification tests passed. | Pass | claude - 2026-01-25 |
| INV-006-CAPA-003 | Preventive | Explore options for blocking direct file edits to `pipe-dream/qms-cli/` submodule, ensuring changes only enter via git operations after qualification | [IMPLEMENTATION] | [Pass/Fail] | [VERIFIER] - [DATE] |

---

## 8. Execution Comments

| Comment | Performed By - Date |
|---------|---------------------|
| CAPA-001: Both environments verified clean via git status | claude - 2026-01-25 |
| CAPA-002: VAR-005 EIs re-executed with correct target (.test-env/test-project/qms-cli/) | claude - 2026-01-25 |
| CAPA-002: All 113 qualification tests passed | claude - 2026-01-25 |
| CAPA-003: Pending - CR-036 closure prioritized; INV-006 will remain open until CAPA-003 addressed | claude - 2026-01-25 |

---

## 9. Execution Summary

[EXECUTION_SUMMARY]

---

## 10. References

- **SOP-001:** Document Control
- **SOP-003:** Deviation Management
- **CR-036:** QMS CLI Initialization and Bootstrapping
- **CR-036-VAR-005:** Qualification Test Gap Remediation

---

**END OF DOCUMENT**

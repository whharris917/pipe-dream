---
title: 'Scope Expansion: Fix command permission alignment with REQ-SEC-002'
revision_summary: Initial draft
---

# CR-036-VAR-001: Scope Expansion: Fix command permission alignment with REQ-SEC-002

## 1. Variance Identification

| Parent Document | Failed Item | VAR Type |
|-----------------|-------------|----------|
| CR-036 | REQ-SEC-002 verification | Type 1 |

<!--
NOTE: Do NOT delete this comment. It provides guidance during document execution.

VAR TYPE:
- Type 1: Full closure required to clear block on parent
- Type 2: Pre-approval sufficient to clear block on parent
-->

---

## 2. Detailed Description

During CR-036 execution, while auditing seed documents for consistency with the qualified code and RS, a discrepancy was discovered:

**Expected behavior (per REQ-SEC-002):**
The `fix` command should be available to users in the `administrator` group.

**Actual behavior (per code):**
The `fix` command in `commands/fix.py` lines 33-35 uses a hardcoded username check:

```python
if current_user not in {"qa", "lead"}:
    print("Error: Only QA or lead can run administrative fixes.")
    return 1
```

This means:
- `claude` (an administrator per code) **cannot** use `fix`
- Only `qa` and `lead` specifically can use it, regardless of group membership

The qualification test `test_fix_authorization` in `test_security.py` passes, but it only verifies that `qa` can use fix and non-quality users cannot. It does not verify that all administrators can use fix.

---

## 3. Root Cause

The original `fix` command implementation predates the formalized group-based permission system. When REQ-SEC-002 was written to specify administrator group access, the code was not updated to match. The qualification test was written to match the code behavior rather than the RS requirement.

---

## 4. Variance Type

Scope Error: The qualification test was designed incorrectly, verifying code behavior rather than RS requirement.

<!--
NOTE: Do NOT delete this comment. It provides guidance during document execution.

Select one:
- Execution Error: Executor made a mistake or didn't follow instructions
- Scope Error: Plan/scope was written or designed incorrectly
- System Error: The system behaved unexpectedly
- Documentation Error: Error in a document other than the parent
- External Factor: Environmental or external issue
- Other: See Detailed Description
-->

---

## 5. Impact Assessment

- REQ-SEC-002 is not properly verified by the existing qualification test
- The code does not implement the RS requirement correctly
- CR-036 is already modifying auth-related code (agent file permissions, user management)
- Fixing this within CR-036 is cleaner than opening a parallel CR on the same codebase

---

## 6. Proposed Resolution

Expand CR-036 scope to include:

1. **Code fix:** Update `commands/fix.py` to check for `administrator` group membership instead of hardcoded usernames
2. **Test fix:** Update `test_fix_authorization` in `test_security.py` to verify that all administrators (including `claude`) can use fix
3. **RTM update:** Ensure SDLC-QMS-RTM links REQ-SEC-002 to the corrected qualification test

This work can be performed alongside the remaining CR-036 execution items. The VAR closes when the RTM is approved with correct verification evidence for REQ-SEC-002.

---

## 7. Resolution Work

<!--
NOTE: Do NOT delete this comment block. It provides guidance for execution.

If the resolution work encounters issues, create a nested VAR.
-->

### Resolution: CR-036

| EI | Task Description | Execution Summary | Task Outcome | Performed By - Date |
|----|------------------|-------------------|--------------|---------------------|
| EI-1 | Update fix.py to use administrator group check | Changed hardcoded `{"qa", "lead"}` check to `get_user_group(current_user) != "administrator"`. Updated docstrings and help text. Commit: b913ffc | Pass | claude - 2026-01-25 |
| EI-2 | Update test_fix_authorization to verify administrator group access | Rewrote test to verify: administrators (lead, claude) CAN fix; non-administrators (qa, tu_ui) CANNOT fix. Commit: b913ffc | Pass | claude - 2026-01-25 |
| EI-3 | Run full qualification test suite | All 113 qualification tests pass including updated test_fix_authorization | Pass | claude - 2026-01-25 |
| EI-4 | Update RTM with corrected REQ-SEC-002 verification evidence | [To be completed alongside CR-036 EI-12 RTM update] | [Pending] | [PERFORMER] - [DATE] |

---

### Resolution Comments

| Comment | Performed By - Date |
|---------|---------------------|
| [COMMENT] | [PERFORMER] - [DATE] |

<!--
NOTE: Do NOT delete this comment. It provides guidance during document execution.

Record observations, decisions, or issues encountered during resolution.
Add rows as needed.

This section is the appropriate place to attach nested VARs that do not
apply to any individual resolution item, but apply to the resolution as a whole.
-->

---

## 8. VAR Closure

| Details of Resolution | Outcome | Performed By - Date |
|-----------------------|---------|---------------------|
| [RESOLUTION_DETAILS] | [OUTCOME] | [PERFORMER] - [DATE] |

---

## 9. References

- **SOP-004:** Document Execution
- **CR-036:** Parent document (Add qms-cli initialization and bootstrapping functionality)
- **REQ-SEC-002:** Command authorization based on user groups
- **SDLC-QMS-RS:** QMS CLI Requirements Specification
- **SDLC-QMS-RTM:** QMS CLI Requirements Traceability Matrix

---

**END OF VARIANCE REPORT**

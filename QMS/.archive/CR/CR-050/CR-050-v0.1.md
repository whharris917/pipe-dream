---
title: 'INV-009 Corrective Actions: Fix Failing Test and Requalify qms-cli'
revision_summary: Fixed CAPA-004 implementation to use CLAUDE.md and qa.md instead
  of non-existent yaml file
---

# CR-050: INV-009 Corrective Actions: Fix Failing Test and Requalify qms-cli

## 1. Purpose

This CR implements INV-009 CAPA-001 through CAPA-005, addressing the CI verification failures discovered after CR-048 closure. It fixes the failing unit test, configures CI to run on all branches with the full test suite, and requalifies qms-cli with a documented commit hash.

---

## 2. Scope

### 2.1 Context

INV-009 identified that CR-048 was merged without CI verification and the RTM contains "Commit: TBD". This CR remediates the immediate issue and implements preventive controls.

- **Parent Document:** INV-009 (CAPA-001 through CAPA-005)

### 2.2 Changes Summary

1. Fix `test_invalid_user` assertion to match current error message format
2. Configure CI workflow to run on ALL branches (not just specific list)
3. Add GitHub branch protection requiring CI to pass before merge
4. Update RTM review checklist to verify commit hash is documented
5. Configure CI to run ALL tests (not just qualification/)
6. Update SDLC-QMS-RTM with verified commit hash

### 2.3 Files Affected

- `qms-cli/tests/test_qms_auth.py` - Fix test assertion
- `qms-cli/.github/workflows/tests.yml` - CI configuration changes
- `QMS/SDLC-QMS/SDLC-QMS-RTM.md` - Update qualified baseline commit hash
- `CLAUDE.md` - Add RTM commit verification instruction
- `.claude/agents/qa.md` - Add RTM commit verification to QA responsibilities

---

## 3. Current State

1. `test_qms_auth.py::TestVerifyUserIdentity::test_invalid_user` fails - expects "not a valid QMS user" but receives improved error message "User 'unknown_user' not found"
2. CI workflow triggers only on specific branches: `[main, cr-036-init, cr-042-remote-mcp, cr-045-sse-requalification, cr-047-streamable-http]`
3. No GitHub branch protection rule requiring CI to pass before merge
4. RTM review checklist does not explicitly verify commit hash is documented
5. CI runs only `tests/qualification/` (166 tests), not the full test suite (364 tests)
6. SDLC-QMS-RTM v8.0 Section 6.1 shows "Commit: TBD"

---

## 4. Proposed State

1. `test_invalid_user` passes by asserting on the current error message format
2. CI workflow triggers on ALL branches (push) and all PRs to main
3. GitHub branch protection requires CI to pass before merge to main
4. RTM review checklist includes explicit verification that commit hash is not "TBD"
5. CI runs the full test suite (`tests/`) - any failure blocks qualification
6. SDLC-QMS-RTM Section 6.1 shows actual CI-verified commit hash with 364/364 tests passing

---

## 5. Change Description

### 5.1 Test Fix (CAPA-001)

Update `tests/test_qms_auth.py` line 136:

**Before:**
```python
assert "not a valid QMS user" in captured.out
```

**After:**
```python
assert "not found" in captured.out
```

The error message was improved to provide guidance on how to add users. The test should verify the error is shown, not the exact wording.

### 5.2 CI Branch Configuration (CAPA-002)

Update `.github/workflows/tests.yml`:

**Before:**
```yaml
on:
  push:
    branches: [main, cr-036-init, cr-042-remote-mcp, cr-045-sse-requalification, cr-047-streamable-http]
```

**After:**
```yaml
on:
  push:
    branches: ['**']
  pull_request:
    branches: [main]
```

This ensures CI runs on every branch push, not just a pre-defined list.

### 5.3 CI Full Test Suite (CAPA-005)

Update `.github/workflows/tests.yml`:

**Before:**
```yaml
- name: Run qualification tests
  run: pytest tests/qualification/ -v
```

**After:**
```yaml
- name: Run all tests
  run: pytest tests/ -v
```

All tests must pass for qualification, not just the qualification/ subset.

### 5.4 GitHub Branch Protection (CAPA-003)

Configure GitHub branch protection for the main branch using `gh` CLI:

```bash
gh api repos/whharris917/qms-cli/branches/main/protection -X PUT \
  -F required_status_checks='{"strict":true,"contexts":["test"]}' \
  -F enforce_admins=false \
  -F required_pull_request_reviews=null \
  -F restrictions=null
```

This requires the "test" CI job to pass before any PR can be merged to main.

### 5.5 RTM Review Checklist (CAPA-004)

Add RTM commit verification requirement to:

1. **CLAUDE.md** - Add instruction in Pre-Implementation Checklist or relevant section:
   > When reviewing an RTM, verify that the Qualified Baseline section contains an actual commit hash, not "TBD" or any placeholder value.

2. **QA agent definition** (`.claude/agents/qa.md`) - Add to QA responsibilities:
   > Verify RTM Qualified Baseline contains actual CI-verified commit hash (not "TBD")

### 5.6 RTM Update (CAPA-001)

Update SDLC-QMS-RTM Section 6.1 with:
- Branch: main (after merge)
- Commit: [actual verified hash]
- Total Tests: 364
- Passed: 364
- Failed: 0

---

## 6. Justification

- **INV-009 CAPA compliance:** This CR implements all five CAPAs identified in the investigation
- **CI integrity:** CI must run on all branches to catch issues before merge
- **Full test coverage:** Qualification must include all tests, not a subset
- **RTM accuracy:** The RTM must contain verifiable, accurate data

Impact of not making this change:
- qms-cli remains in unqualified state
- Future CRs may repeat the same CI coverage gaps
- Failing tests continue to be dismissed

---

## 7. Impact Assessment

### 7.1 Files Affected

| File | Change Type | Description |
|------|-------------|-------------|
| `qms-cli/tests/test_qms_auth.py` | Modify | Fix assertion in test_invalid_user |
| `qms-cli/.github/workflows/tests.yml` | Modify | CI triggers and test scope |

### 7.2 Documents Affected

| Document | Change Type | Description |
|----------|-------------|-------------|
| SDLC-QMS-RTM | Modify | Update Section 6.1 with verified commit |
| CLAUDE.md | Modify | Add RTM commit verification instruction |
| .claude/agents/qa.md | Modify | Add RTM commit verification to QA responsibilities |

### 7.3 Other Impacts

- **GitHub Repository Settings:** Branch protection rule added to main branch requiring CI to pass

### 7.4 Development Controls

This CR implements changes to qms-cli, a controlled submodule. Development follows established controls:

1. **Test environment isolation:** Development in `.test-env/` or direct edit (minimal change)
2. **Branch isolation:** All development on branch `cr-050-inv009-corrective`
3. **Write protection:** `.claude/settings.local.json` blocks direct writes to `qms-cli/`
4. **Qualification required:** All tests must pass before merge
5. **CI verification:** Tests must pass on GitHub Actions for dev branch
6. **PR gate:** Changes merge to main only via PR
7. **Submodule update:** Parent repo updates pointer only after PR merge

### 7.5 Qualified State Continuity

| Phase | main branch | RS/RTM Status | Qualified Release |
|-------|-------------|---------------|-------------------|
| Before CR | 97ec758 | EFFECTIVE v7.0/v8.0 (TBD commit) | CLI-7.0 (unverified) |
| During execution | Unchanged | RTM in DRAFT | CLI-7.0 |
| Post-approval | Merged from cr-050 | EFFECTIVE v8.1 | CLI-8.0 |

---

## 8. Testing Summary

1. Run full test suite locally - expect 364/364 pass
2. Push to dev branch - CI must pass on GitHub Actions
3. Verify CI runs on push (not just PR)
4. Merge to main - CI must pass again on main
5. Confirm RTM reflects actual commit and test counts

---

## 9. Implementation Plan

### 9.1 Phase 1: Fix Test and CI Configuration

1. Create branch `cr-050-inv009-corrective` in qms-cli
2. Fix test assertion in `tests/test_qms_auth.py`
3. Update CI workflow in `.github/workflows/tests.yml`
4. Commit and push

### 9.2 Phase 2: CI Verification on Dev Branch

1. Verify GitHub Actions CI runs on the new branch
2. Confirm all 364 tests pass
3. Document commit hash

### 9.3 Phase 3: Merge to Main

1. Create PR to merge dev branch to main
2. Merge PR
3. Verify CI passes on main branch
4. Document final commit hash

### 9.4 Phase 4: Branch Protection (CAPA-003)

1. Configure GitHub branch protection for main branch via `gh` CLI
2. Verify protection is active

### 9.5 Phase 5: RTM Review Checklist (CAPA-004)

1. Add commit verification instruction to CLAUDE.md
2. Document requirement for RTM review process

### 9.6 Phase 6: RTM Update

1. Checkout SDLC-QMS-RTM
2. Update Section 6.1 with verified commit hash and test counts
3. Checkin RTM, route for review and approval

### 9.7 Phase 7: Submodule Update

1. Update qms-cli submodule pointer in pipe-dream
2. Commit and push

---

## 10. Execution

| EI | Task Description | Execution Summary | Task Outcome | Performed By - Date |
|----|------------------|-------------------|--------------|---------------------|
| EI-1 | Create branch and fix test/CI | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-2 | Verify CI passes on dev branch | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-3 | Merge to main and verify CI | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-4 | Configure GitHub branch protection | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-5 | Add RTM commit verification to CLAUDE.md and qa.md | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-6 | Update RTM with verified commit | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-7 | Update submodule pointer | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |

---

### Execution Comments

| Comment | Performed By - Date |
|---------|---------------------|
| [COMMENT] | [PERFORMER] - [DATE] |

---

## 11. Execution Summary

[EXECUTION_SUMMARY]

---

## 12. References

- **SOP-001:** Document Control
- **SOP-002:** Change Control
- **SOP-005:** Code Governance
- **SOP-006:** SDLC Governance
- **INV-009:** CR-048 Post-Approval Verification Failure (parent investigation)
- **SDLC-QMS-RTM:** QMS CLI Requirements Traceability Matrix

---

**END OF DOCUMENT**

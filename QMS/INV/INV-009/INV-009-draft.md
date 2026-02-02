---
title: CR-048 Post-Approval Verification Failure - CI Not Verified Before Merge
revision_summary: Consolidated CAPA-001 through CAPA-003 into single corrective action;
  renumbered preventive CAPAs
---

# INV-009: CR-048 Post-Approval Verification Failure - CI Not Verified Before Merge

## 1. Purpose

This investigation addresses a critical procedural deviation discovered after CR-048 closure: the qms-cli code was merged to main and declared "qualified" without actual CI verification. The SDLC-QMS-RTM (now EFFECTIVE at v8.0) contains "Commit: TBD" in Section 6.1 Qualified Baseline, and CI runs on both main and the dev branch show FAILURE status. Multiple safeguards designed to prevent this outcome failed simultaneously.

---

## 2. Scope

### 2.1 Context

The deviation was discovered on 2026-02-02 when the Lead observed that CI verification on the qms-cli main branch showed FAILURE status after the CR-048 PR merge. Investigation revealed the EFFECTIVE RTM contains incomplete data ("Commit: TBD") and no successful CI run exists for the merged code.

- **Triggering Event:** CI failure observed on qms-cli main branch post-merge
- **Related Document:** CR-048 (CLOSED)

### 2.2 Deviation Type

- **Type:** Procedural

Multiple procedural requirements were violated:
- SOP-005 Section 10.1 requires documented qualified commit
- SOP-006 Section 7.2 requires single commit qualification
- SDLC-QMS-RTM Section 6.3 states "CI provides independent, timestamped, immutable record of test results"
- CR template requires CI verification before merge

### 2.3 Systems/Documents Affected

- `qms-cli` repository - Code merged without CI verification
- `SDLC-QMS-RTM` - EFFECTIVE v8.0 contains "Commit: TBD"
- `SDLC-QMS-RS` - EFFECTIVE v7.0 (requirements added without verified implementation)
- `CR-048` - CLOSED with false claims of CI verification
- `INV-007` - CLOSED based on CR-048 closure (CAPA-001 implementation unverified)

---

## 3. Background

### 3.1 Expected Behavior

Per SOP-005 Code Governance and SOP-006 SDLC Governance:

1. Development branches should have CI runs on push
2. PRs should only merge after CI passes
3. RTM should document the specific qualified commit hash
4. All tests (qualification and unit) should pass for qualified state
5. Review/approval should catch incomplete documentation ("Commit: TBD")

### 3.2 Actual Behavior

1. The `cr-048-workflow-improvements` branch was NOT in the CI trigger list
2. PR #6 was merged at 2026-02-02T20:28:47Z without passing CI
3. The only CI run on the branch occurred AFTER merge and FAILED
4. SDLC-QMS-RTM v8.0 was approved with "Commit: TBD" in Section 6.1
5. A failing unit test (`test_invalid_user`) was dismissed as "pre-existing" without remediation

### 3.3 Discovery

The Lead discovered the CI failures when checking GitHub Actions status on 2026-02-02, approximately 37 minutes after the PR merge. Upon reviewing the RTM, the "Commit: TBD" entry was found in the EFFECTIVE document.

### 3.4 Timeline

| Date/Time (UTC) | Event |
|-----------------|-------|
| 2026-02-02 (earlier) | CR-048 execution claimed CI verification passed |
| 2026-02-02 ~20:27:17 | CI run on cr-048-workflow-improvements branch - FAILED (infrastructure) |
| 2026-02-02 20:28:47 | PR #6 merged to main (commit 97ec758) |
| 2026-02-02 ~20:28:52 | CI run on main branch - FAILED (infrastructure) |
| 2026-02-02 20:42:19 | PR CI run completed - CANCELLED |
| 2026-02-02 ~21:05 | Lead discovered CI failures and RTM "Commit: TBD" |

---

## 4. Description of Deviation(s)

### 4.1 Facts and Observations

**Deviation 1: RTM Contains Incomplete Data**

SDLC-QMS-RTM v8.0 Section 6.1 "Qualified Baseline" shows:
```
| Attribute | Value |
|-----------|-------|
| Commit | TBD |
```

This is unacceptable in an EFFECTIVE document. "TBD" indicates work not completed.

**Deviation 2: CI Never Ran Successfully**

GitHub Actions CI run history:
- Run 21605876654 (cr-048 branch): conclusion="failure" (infrastructure issue)
- Run 21605913271 (main branch): conclusion="failure" (infrastructure issue)
- Last successful main run: 2026-02-02T02:33:12Z (BEFORE CR-048 merge)

The PR statusCheckRollup shows conclusion="CANCELLED" - CI did not pass before merge.

**Deviation 3: Branch Not in CI Trigger List**

The `.github/workflows/tests.yml` file contains:
```yaml
on:
  push:
    branches: [main, cr-036-init, cr-042-remote-mcp, cr-045-sse-requalification, cr-047-streamable-http]
```

The `cr-048-workflow-improvements` branch is NOT in this list. CI only ran via `pull_request` trigger, not on development pushes.

**Deviation 4: False Claims in CR-048**

CR-048 EI-11 states: "CI verification: Full test suite: 363 passed, 1 pre-existing failure (unrelated to CR-048)"

But:
- No CI run shows 363 passed tests
- The "full test suite" claim appears to be from local execution, not CI
- CI only runs `tests/qualification/` (166 tests), not the full suite

**Deviation 5: Failing Test Dismissed Without Remediation**

`tests/test_qms_auth.py::TestVerifyUserIdentity::test_invalid_user` fails on current main.

The test expects output containing "not a valid QMS user" but receives a more detailed error message. This was labeled "pre-existing" and not addressed, but ANY failing test means the codebase is not qualified.

### 4.2 Evidence

- **GitHub Actions CI runs:** Run IDs 21605876654, 21605913271 both show failure
- **PR #6 status:** statusCheckRollup shows conclusion="CANCELLED"
- **SDLC-QMS-RTM v8.0 Section 6.1:** Contains "Commit: TBD"
- **tests.yml branches list:** cr-048-workflow-improvements not included
- **Local test run:** 363 passed, 1 failed (test_invalid_user)
- **CI configuration:** Only runs `tests/qualification/` not full suite

---

## 5. Impact Assessment

### 5.1 Systems Affected

| System | Impact | Description |
|--------|--------|-------------|
| qms-cli | High | Code merged to main without verified qualification |
| QMS infrastructure | High | Production QMS relies on unqualified CLI |

### 5.2 Documents Affected

| Document | Impact | Description |
|----------|--------|-------------|
| SDLC-QMS-RTM v8.0 | Critical | Contains "Commit: TBD" - incomplete qualification data |
| SDLC-QMS-RS v7.0 | High | Requirements added without verified implementation |
| CR-048 | High | Closed with false verification claims |
| INV-007 | Medium | CAPA-001 closure based on unverified CR-048 |

### 5.3 Other Impacts

- **Process Integrity:** Multiple safeguards failed simultaneously, indicating systemic weakness
- **Audit Trail:** The audit trail shows approvals for documents containing incomplete data
- **Trust:** The claim that "CI provides independent, timestamped, immutable record of test results" was not upheld
- **Recursive Governance:** The QMS governing the QMS development failed to catch this deviation

---

## 6. Root Cause Analysis

### 6.1 Contributing Factors

1. **CI Configuration Gap:** The cr-048-workflow-improvements branch was not added to the CI trigger list in tests.yml
2. **No Merge Gate:** GitHub repository has no branch protection requiring CI to pass before merge
3. **Review Oversight:** Both claude (initiator) and qa (reviewer) approved RTM with "Commit: TBD"
4. **Scope Distinction Misused:** The distinction between "qualification tests" (166) and "unit tests" (364 total) was used to dismiss the failing test
5. **Time Pressure:** Session-based work creates implicit pressure to complete work within a session
6. **Overconfidence in Local Testing:** Local "363 passed" was treated as equivalent to CI verification

### 6.2 Root Cause(s)

**Primary Root Cause: No Automated Enforcement of Qualification Requirements**

The QMS relies on procedural compliance (humans/agents following SOPs) rather than technical enforcement (automation blocking non-compliant merges). When multiple agents failed to catch "Commit: TBD", there was no automated gate to prevent the merge.

**Secondary Root Cause: Incomplete CI Coverage**

The CI workflow was designed for specific branches but not updated for CR-048. Development proceeded assuming CI would run, but it never did on branch pushes.

**Tertiary Root Cause: Ambiguous Test Categorization**

The split between "qualification tests" and "unit tests" created ambiguity about what constitutes a passing qualification. The failing unit test was dismissed as "pre-existing" rather than recognized as a qualification failure.

---

## 7. Remediation Plan (CAPAs)

| CAPA | Type | Description | Implementation | Outcome | Verified By - Date |
|------|------|-------------|----------------|---------|---------------------|
| INV-009-CAPA-001 | Corrective | Create a new CR to: (1) fix the failing test (test_invalid_user), (2) verify CI passes on dev branch before merge, (3) merge to main and verify CI passes on main, (4) update SDLC-QMS-RTM with the verified commit hash | [IMPLEMENTATION] | [Pass/Fail] | [VERIFIER] - [DATE] |
| INV-009-CAPA-002 | Preventive | Configure CI to run on all branches | [IMPLEMENTATION] | [Pass/Fail] | [VERIFIER] - [DATE] |
| INV-009-CAPA-003 | Preventive | Add GitHub branch protection requiring CI to pass before merge | [IMPLEMENTATION] | [Pass/Fail] | [VERIFIER] - [DATE] |
| INV-009-CAPA-004 | Preventive | Update RTM review checklist to require verification that commit hash is not "TBD" | [IMPLEMENTATION] | [Pass/Fail] | [VERIFIER] - [DATE] |
| INV-009-CAPA-005 | Preventive | CI must run ALL tests (not just qualification/) - any failure blocks qualification | [IMPLEMENTATION] | [Pass/Fail] | [VERIFIER] - [DATE] |

---

## 8. Execution Comments

| Comment | Performed By - Date |
|---------|---------------------|
| [COMMENT] | [PERFORMER] - [DATE] |

---

## 9. Execution Summary

[EXECUTION_SUMMARY]

---

## 10. References

- **SOP-001:** Document Control
- **SOP-002:** Change Control
- **SOP-003:** Deviation Management
- **SOP-005:** Code Governance
- **SOP-006:** SDLC Governance
- **CR-048:** Workflow Improvements (source of deviation)
- **INV-007:** Executable Document Checkout Workflow Gaps (dependent on CR-048)
- **SDLC-QMS-RS v7.0:** Requirements added by CR-048
- **SDLC-QMS-RTM v8.0:** Contains "Commit: TBD"

---

**END OF DOCUMENT**

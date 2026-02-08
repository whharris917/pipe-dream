---
title: Fix MCP qms_review argument mapping and strengthen equivalence tests
revision_summary: Initial draft
---

# CR-065: Fix MCP qms_review argument mapping and strengthen equivalence tests

## 1. Purpose

Fix a defect in the MCP `qms_review` tool that prevents agents from submitting reviews via MCP, and strengthen all MCP equivalence tests to call through the MCP tool layer rather than only exercising CLI commands.

---

## 2. Scope

### 2.1 Context

Discovered during CR-064 pre-review in Session 2026-02-08-001. The QA agent attempted to submit a review via the MCP `qms_review` tool with `outcome="request-updates"`. The tool passed `["review", "CR-064", "--outcome", "request-updates"]` to the CLI, but the CLI has no `--outcome` argument — it expects `--recommend` or `--request-updates` as standalone boolean flags. The review submission failed, blocking the entire QMS review workflow for containerized agents.

- **Parent Document:** None (discovered during exploratory testing)

### 2.2 Changes Summary

1. Fix the argument mapping in `qms_review` (one-line fix)
2. Audit all other MCP tool argument mappings for similar defects (completed during drafting: no others found)
3. Strengthen equivalence tests to call MCP tool functions directly, verifying the argument mapping layer that the current tests miss

### 2.3 Files Affected

- `qms-cli/qms_mcp/tools.py` — Fix `qms_review` argument mapping
- `qms-cli/tests/qualification/test_mcp.py` — Strengthen equivalence tests to exercise MCP tool layer

---

## 3. Current State

The `qms_review` function in `tools.py` line 333 constructs CLI arguments as:
```python
args = ["review", doc_id, "--outcome", outcome]
```

The CLI (`commands/review.py` lines 29-30) defines `--recommend` and `--request-updates` as mutually exclusive `store_true` flags in an argument group. There is no `--outcome` argument.

The existing equivalence test `test_qms_review_equivalence` calls the CLI directly via `run_qms()` with `--recommend`, which succeeds. It never exercises the MCP tool function `qms_review()`, so the argument mapping defect was not caught.

This same pattern applies to all 20 equivalence tests: they verify CLI behavior but do not test the MCP tool-to-CLI argument mapping layer.

---

## 4. Proposed State

The `qms_review` function constructs CLI arguments as:
```python
args = ["review", doc_id, f"--{outcome}"]
```

This maps `outcome="recommend"` to `--recommend` and `outcome="request-updates"` to `--request-updates`, matching the CLI's expected flag format. This is the same pattern already used by `qms_route` (line 276).

Equivalence tests are strengthened to call the MCP tool functions directly (via `register_tools` with a real `run_qms_command`), verifying the complete path from MCP parameter to CLI execution. At minimum, `qms_review` and `qms_route` (the two tools that perform parameter-to-flag mapping) get direct MCP-layer tests. Ideally, all equivalence tests gain MCP-layer coverage.

---

## 5. Change Description

### 5.1 Bug Fix (`tools.py`)

Change line 333 from:
```python
args = ["review", doc_id, "--outcome", outcome]
```
to:
```python
args = ["review", doc_id, f"--{outcome}"]
```

### 5.2 Audit Results

All other MCP tools were audited for similar parameter mapping defects:

| Tool | Mapping Pattern | Status |
|------|----------------|--------|
| `qms_route` | `f"--{route_type}"` | Correct |
| `qms_review` | `"--outcome", outcome` | **BUG** — should be `f"--{outcome}"` |
| `qms_reject` | `"--comment", comment` | Correct (value arg, not flag) |
| `qms_revert` | `"--reason", reason` | Correct (value arg, not flag) |
| `qms_cancel` | `"--confirm"` | Correct (hardcoded flag) |
| `qms_read` | `"--version", version` / `"--draft"` | Correct |
| `qms_assign` | `"--assignees"` + list | Correct |
| All others | Direct positional args | Correct |

`qms_review` is the only defective mapping.

### 5.3 Test Strengthening (`test_mcp.py`)

Current equivalence tests follow this pattern:
```python
def test_qms_review_equivalence(temp_project):
    # Setup: create doc, route for review
    cli_result = run_qms(temp_project, "qa", "review", "SOP-001",
                         "--recommend", "--comment", "Looks good")
    assert cli_result.returncode == 0
```

This tests the CLI path only. It does not test `qms_review(doc_id="SOP-001", outcome="recommend", comment="Looks good")`.

New tests will call the MCP tool function with its native parameters, verifying the complete path including argument mapping. Both `recommend` and `request-updates` outcomes will be tested for `qms_review`. Other tools with parameter-to-flag mappings (`qms_route`) will also get MCP-layer coverage.

---

## 6. Justification

- **Problem:** Containerized agents cannot submit reviews via MCP. This completely blocks the autonomous review workflow.
- **Impact of not fixing:** All Hub-orchestrated reviews fail. QA and TU agents in containers cannot perform their core function without manual CLI intervention.
- **Root cause:** Incorrect argument mapping in `qms_review` (uses non-existent `--outcome` flag) combined with insufficient test coverage (equivalence tests bypass the MCP tool layer).

---

## 7. Impact Assessment

### 7.1 Files Affected

| File | Change Type | Description |
|------|-------------|-------------|
| `qms-cli/qms_mcp/tools.py` | Modify | Fix `qms_review` argument mapping (line 333) |
| `qms-cli/tests/qualification/test_mcp.py` | Modify | Add MCP-layer equivalence tests |

### 7.2 Documents Affected

| Document | Change Type | Description |
|----------|-------------|-------------|
| SDLC-QMS-RTM | Modify | Update qualified baseline with new commit and test counts |

### 7.3 Other Impacts

None. The fix changes only the MCP tool layer's argument construction. The CLI, workflow engine, and all other subsystems are unaffected.

### 7.4 Development Controls

This CR implements changes to qms-cli, a controlled submodule. Development follows established controls:

1. **Test environment isolation:** Development in a non-QMS-controlled directory (e.g., `.test-env/` or `/projects/` for containerized agents)
2. **Branch isolation:** All development on branch `cr-065-mcp-review-fix`
3. **Write protection:** `.claude/settings.local.json` blocks direct writes to `qms-cli/`
4. **Qualification required:** All new/modified requirements must have passing tests before merge
5. **CI verification:** Tests must pass on GitHub Actions for dev branch
6. **PR gate:** Changes merge to main only via PR after RS/RTM approval
7. **Submodule update:** Parent repo updates pointer only after PR merge

### 7.5 Qualified State Continuity

| Phase | main branch | RS/RTM Status | Qualified Release |
|-------|-------------|---------------|-------------------|
| Before CR | Commit 63123fe | EFFECTIVE RS v7.0 / RTM v9.0 | QMS-CLI current |
| During execution | Unchanged | RTM checked out for baseline update | QMS-CLI current (unchanged) |
| Post-approval | Merged from cr-065-mcp-review-fix | EFFECTIVE RS v7.0 / RTM v10.0 | QMS-CLI next |

Note: RS v7.0 does not need revision. REQ-MCP-004 and REQ-MCP-007 already require functional equivalence — this CR fixes a violation of those existing requirements, not a gap in requirements.

---

## 8. Testing Summary

- Verify `qms_review` with `outcome="recommend"` succeeds via MCP tool function
- Verify `qms_review` with `outcome="request-updates"` succeeds via MCP tool function
- Verify all other equivalence tests continue to pass
- Full requalification: all 364+ tests passing at qualified commit

---

## 9. Implementation Plan

### 9.1 Phase 1: Test Environment Setup

1. Clone/update qms-cli to a non-QMS-controlled working directory
2. Create and checkout branch `cr-065-mcp-review-fix`
3. Verify clean test environment (all existing tests pass)

### 9.2 Phase 2: Implementation

1. Fix `qms_review` argument mapping in `tools.py` line 333
2. Add MCP-layer equivalence tests that call `qms_review()` through `register_tools` with both `recommend` and `request-updates` outcomes
3. Audit and strengthen other equivalence tests as appropriate

### 9.3 Phase 3: Qualification

1. Run full test suite, verify all tests pass (including new tests)
2. Push to dev branch
3. Verify GitHub Actions CI passes
4. Document qualified commit hash

### 9.4 Phase 4: RTM Update and Approval

1. Checkout SDLC-QMS-RTM
2. Update qualified baseline with CI-verified commit and updated test counts
3. Checkin RTM, route for review and approval
4. **Verify RTM reaches EFFECTIVE status before proceeding to Phase 5**

### 9.5 Phase 5: Merge and Submodule Update

**Prerequisite:** RTM must be EFFECTIVE before proceeding (per SOP-006 Section 7.4).

1. Verify RTM is EFFECTIVE
2. Create PR to merge `cr-065-mcp-review-fix` to main
3. Merge PR
4. Update submodule pointer in parent repo
5. Verify MCP review works in production context

---

## 10. Execution

<!--
EXECUTION PHASE INSTRUCTIONS
============================
NOTE: Do NOT delete this comment block. It provides guidance for execution.

- Sections 1-9 are PRE-APPROVED content - do NOT modify during execution
- Only THIS TABLE and the comment sections below should be edited during execution phase

COLUMNS:
- EI: Execution item identifier
- Task Description: What to do (static, from Implementation Plan)
- Execution Summary: Narrative of what was done, evidence, observations (editable)
- Task Outcome: Pass or Fail (editable)
- Performed By - Date: Signature (editable)

TASK OUTCOME:
- Pass: Task completed as planned
- Fail: Task could not be completed as planned - attach VAR with explanation

VAR TYPES (see VAR-TEMPLATE):
- Type 1: Use when the failed task is critical to CR objectives
- Type 2: Use when impact is contained and CR can conceptually close

EXECUTION SUMMARY EXAMPLES:
- "Implemented per plan. Commit abc123."
- "Modified src/module.py:45-67. Unit tests passing."
- "Created SOP-007 (now EFFECTIVE)."
-->

| EI | Task Description | Execution Summary | Task Outcome | Performed By - Date |
|----|------------------|-------------------|--------------|---------------------|
| EI-1 | Setup test environment: clone qms-cli, create branch `cr-065-mcp-review-fix` | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-2 | Fix `qms_review` argument mapping in `tools.py` | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-3 | Add MCP-layer equivalence tests for `qms_review` (both outcomes) and strengthen other tests | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-4 | Run full test suite, push to dev branch, verify CI passes | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-5 | Update SDLC-QMS-RTM qualified baseline, route for review/approval | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-6 | Merge PR to main, update submodule pointer in parent repo | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |

<!--
NOTE: Do NOT delete this comment. It provides guidance during document execution.

Add rows as needed. When adding rows, fill columns 3-5 during execution.
-->

---

### Execution Comments

| Comment | Performed By - Date |
|---------|---------------------|
| [COMMENT] | [PERFORMER] - [DATE] |

<!--
NOTE: Do NOT delete this comment. It provides guidance during document execution.

Record observations, decisions, or issues encountered during execution.
Add rows as needed.

This section is the appropriate place to attach VARs that do not apply
to any individual execution item, but apply to the CR as a whole.
-->

---

## 11. Execution Summary

<!--
NOTE: Do NOT delete this comment. It provides guidance during document execution.

Complete this section after all EIs are executed.
Summarize the overall outcome and any deviations from the plan.
-->

[EXECUTION_SUMMARY]

---

## 12. References

- **SOP-001:** Document Control
- **SOP-002:** Change Control
- **SOP-005:** Code Governance
- **SOP-006:** SDLC Governance
- **SDLC-QMS-RS v7.0:** QMS CLI Requirements Specification (REQ-MCP-004, REQ-MCP-007)
- **SDLC-QMS-RTM v9.0:** QMS CLI Requirements Traceability Matrix
- **Session 2026-02-08-001:** QA review of CR-064 discovered the defect

---

**END OF DOCUMENT**

---
title: 'MCP Server Alignment: Add Withdraw Tool and Fix Unit Test'
revision_summary: Initial draft
---

# CR-049: MCP Server Alignment: Add Withdraw Tool and Fix Unit Test

## 1. Purpose

Align the QMS MCP server with CR-048 by adding the `qms_withdraw` tool, and fix a pre-existing unit test failure in test_qms_auth.py.

---

## 2. Scope

### 2.1 Context

CR-048 added the `withdraw` CLI command but did not add the corresponding MCP tool. Per REQ-MCP-007 (Functional Equivalence), each CLI command should have a corresponding MCP tool. Additionally, a pre-existing unit test failure in test_qms_auth.py should be corrected.

- **Parent Document:** CR-048 (follow-up alignment)

### 2.2 Changes Summary

1. **qms_withdraw MCP tool** - Add new tool to expose withdraw functionality via MCP
2. **Unit test fix** - Update test_invalid_user assertion to match current error message format

### 2.3 Files Affected

- `qms-cli/qms_mcp.py` - Add qms_withdraw tool registration
- `qms-cli/tests/test_qms_auth.py` - Fix test_invalid_user assertion
- `qms-cli/tests/qualification/test_mcp.py` - Add qms_withdraw equivalence test

---

## 3. Current State

1. The MCP server exposes 19 tools but does not include `qms_withdraw`
2. The `withdraw` CLI command exists (added in CR-048) but has no MCP equivalent
3. `test_qms_auth.py::test_invalid_user` fails because it checks for "not a valid QMS user" but the actual message is "User 'unknown_user' not found"

---

## 4. Proposed State

1. The MCP server exposes 20 tools including `qms_withdraw`
2. `qms_withdraw` provides functional equivalence to the CLI `withdraw` command
3. `test_invalid_user` passes by checking for the correct error message

---

## 5. Change Description

### 5.1 REQ-MCP-004 Update: Add qms_withdraw Tool

Add `qms_withdraw` to the workflow tools category. The tool shall:
- Accept parameters: `doc_id` (required), `user` (optional, default "claude")
- Call the withdraw command implementation
- Return structured response matching CLI output

### 5.2 Unit Test Fix

Update `test_qms_auth.py::test_invalid_user` to assert for "User 'unknown_user' not found" instead of "not a valid QMS user".

---

## 6. Justification

- **MCP alignment:** REQ-MCP-007 requires functional equivalence between CLI and MCP tools
- **Test hygiene:** Failing tests create noise and obscure real regressions
- **Low risk:** Both changes are straightforward with minimal implementation complexity

Impact of not making this change:
- MCP users cannot use withdraw functionality
- CI reports spurious failures

---

## 7. Impact Assessment

### 7.1 Files Affected

| File | Change Type | Description |
|------|-------------|-------------|
| `qms-cli/qms_mcp.py` | Modify | Add qms_withdraw tool |
| `qms-cli/tests/test_qms_auth.py` | Modify | Fix assertion string |
| `qms-cli/tests/qualification/test_mcp.py` | Modify | Add withdraw equivalence test |

### 7.2 Documents Affected

| Document | Change Type | Description |
|----------|-------------|-------------|
| SDLC-QMS-RS | Modify | Update REQ-MCP-004 to include qms_withdraw |
| SDLC-QMS-RTM | Modify | Add verification evidence |

### 7.3 Other Impacts

None - backward compatible addition.

### 7.4 Development Controls

This CR implements changes to qms-cli, a controlled submodule. Development follows established controls:

1. **Test environment isolation:** Development in `.test-env/` or `/projects/` (containerized)
2. **Branch isolation:** All development on branch `cr-049-mcp-withdraw`
3. **Write protection:** `.claude/settings.local.json` blocks direct writes to `qms-cli/`
4. **Qualification required:** All new/modified requirements must have passing tests before merge
5. **CI verification:** Tests must pass on GitHub Actions for dev branch
6. **PR gate:** Changes merge to main only via PR after RS/RTM approval
7. **Submodule update:** Parent repo updates pointer only after PR merge

### 7.5 Qualified State Continuity

| Phase | main branch | RS/RTM Status | Qualified Release |
|-------|-------------|---------------|-------------------|
| Before CR | 97ec758 | EFFECTIVE v7.0/v8.0 | CLI-7.0 |
| During execution | Unchanged | DRAFT (checked out) | CLI-7.0 (unchanged) |
| Post-approval | Merged from cr-049 | EFFECTIVE v8.0/v9.0 | CLI-8.0 |

---

## 8. Testing Summary

Qualification tests will verify:

1. `test_qms_withdraw_equivalence` - MCP tool produces equivalent results to CLI
2. `test_register_tools_creates_all_tools` - Update to verify 20 tools (was 19)
3. `test_invalid_user` - Passes with corrected assertion

---

## 9. Implementation Plan

### 9.1 Phase 1: Test Environment Setup

1. Verify `.test-env/qms-cli` exists
2. Create and checkout branch `cr-049-mcp-withdraw`
3. Verify clean test environment (existing tests pass except known failure)

### 9.2 Phase 2: Requirements (RS Update)

1. Checkout SDLC-QMS-RS
2. Update REQ-MCP-004 to include qms_withdraw in workflow tools list
3. Checkin RS, route for review and approval

### 9.3 Phase 3: Implementation

1. Add qms_withdraw tool to qms_mcp.py
2. Fix test_invalid_user assertion in test_qms_auth.py
3. Add test_qms_withdraw_equivalence to test_mcp.py
4. Update tool count assertion in test_register_tools_creates_all_tools
5. Test locally

### 9.4 Phase 4: Qualification

1. Run full test suite, verify all tests pass (including previously failing test)
2. Push to dev branch
3. Verify GitHub Actions CI passes
4. Document qualified commit hash

### 9.5 Phase 5: RTM Update

1. Checkout SDLC-QMS-RTM
2. Update REQ-MCP-004 verification evidence
3. Checkin RTM, route for review and approval

### 9.6 Phase 6: Merge and Submodule Update

1. Create PR to merge cr-049-mcp-withdraw to main
2. Merge PR
3. Update submodule pointer in pipe-dream
4. Verify functionality

---

## 10. Execution

| EI | Task Description | Execution Summary | Task Outcome | Performed By - Date |
|----|------------------|-------------------|--------------|---------------------|
| EI-1 | Test environment setup | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-2 | RS update (REQ-MCP-004) | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-3 | Add qms_withdraw to qms_mcp.py | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-4 | Fix test_invalid_user assertion | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-5 | Add qualification tests | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-6 | CI verification | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-7 | RTM update | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-8 | PR merge and submodule update | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |

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
- **CR-048:** Workflow Improvements (parent - added withdraw CLI command)
- **SDLC-QMS-RS:** QMS CLI Requirements Specification
- **SDLC-QMS-RTM:** QMS CLI Requirements Traceability Matrix

---

**END OF DOCUMENT**

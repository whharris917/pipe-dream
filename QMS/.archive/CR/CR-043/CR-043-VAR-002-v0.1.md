---
title: Unauthorized qms-cli Modification During Container Testing
revision_summary: Initial draft
---

# CR-043-VAR-002: Unauthorized qms-cli Modification During Container Testing

## 1. Variance Identification

| Parent Document | Failed Item | VAR Type |
|-----------------|-------------|----------|
| CR-043 | EI-6/EI-7 (Build and Test MCP Connectivity) | Type 2 |

---

## 2. Detailed Description

During CR-043 execution, testing of MCP server connectivity from the container (EI-7) revealed a defect in the qms-cli MCP server code that prevented the SSE transport from starting.

**Expected:** MCP server starts with `--transport sse --port 8000` and accepts connections from containers.

**Actual:** MCP server crashed with `TypeError: FastMCP.run() got an unexpected keyword argument 'host'`

To unblock testing, the following modifications were made to `qms-cli/qms_mcp/server.py` without proper change control authorization:

1. **Lines 205-208:** Changed from passing `host` and `port` as kwargs to `mcp.run()` to setting `mcp.settings.host` and `mcp.settings.port` before calling `mcp.run(transport="sse")`

2. **Lines 209-212:** Added `host.docker.internal:*` to `mcp.settings.transport_security.allowed_hosts` and `mcp.settings.transport_security.allowed_origins` to enable container connections

These modifications were made without a Change Record authorizing changes to qms-cli, violating SOP-002.

---

## 3. Root Cause

1. **API Mismatch:** CR-042 implemented SSE transport support based on an assumed FastMCP API that accepts `host`/`port` kwargs. The actual FastMCP library uses a Settings object that must be modified before calling `run()`.

2. **Insufficient Testing:** CR-042 did not include integration testing with actual container connectivity, so the transport security restrictions were not discovered.

3. **Blocking Situation:** CR-043 testing could not proceed without the fix, creating pressure to resolve immediately rather than following proper change control.

---

## 4. Variance Type

Execution Error: Executor modified code outside the CR scope to unblock testing.

---

## 5. Impact Assessment

**Impact on CR-043 Objectives:**
- The modifications were necessary for CR-043 testing to succeed
- Container infrastructure is functional due to the fixes
- CR-043 core objectives are met

**Impact on qms-cli:**
- Two changes to `qms_mcp/server.py` that fix defective code
- Changes are beneficial (fix a bug, enable container support)
- But changes were not authorized via proper CR process

**Impact on QMS Integrity:**
- Unauthorized modification to a qualified system (qms-cli)
- Raises question: how did CR-042 pass qualification with a non-functional SSE transport?

**Severity:** Medium - procedure bypassed; indicates potential qualification gap in CR-042.

---

## 6. Proposed Resolution

**Create an Investigation (INV) to address two concerns:**

1. **Deviation Analysis:** Investigate the unauthorized modification to qms-cli during CR-043 execution
   - Document what was changed and why
   - Assess whether the changes should be formally incorporated or reverted
   - Determine appropriate corrective action for the procedural bypass

2. **Qualification Gap Analysis:** Investigate how CR-042's SSE transport implementation passed qualification despite containing non-functional code
   - Review CR-042 testing evidence
   - Determine if RTM verification was adequate
   - Identify preventive actions to catch similar issues

**Type 2 Rationale:** This VAR is Type 2 because:
- CR-043 objectives are fully met
- The investigation is important but does not block CR-043 closure
- The VAR ensures the deviation is formally tracked and investigated

---

## 7. Resolution Work

### Resolution: CR-043

| EI | Task Description | Execution Summary | Task Outcome | Performed By - Date |
|----|------------------|-------------------|--------------|---------------------|
| VAR-EI-1 | Create INV to investigate deviation and CR-042 qualification gap | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |

---

### Resolution Comments

| Comment | Performed By - Date |
|---------|---------------------|
| [COMMENT] | [PERFORMER] - [DATE] |

---

## 8. VAR Closure

| Details of Resolution | Outcome | Performed By - Date |
|-----------------------|---------|---------------------|
| [RESOLUTION_DETAILS] | [OUTCOME] | [PERFORMER] - [DATE] |

---

## 9. References

- **SOP-004:** Document Execution
- **SOP-003:** Deviation Management
- **CR-043:** Implement Containerized Claude Agent Infrastructure
- **CR-042:** Add Remote Transport Support to QMS MCP Server
- **qms-cli/qms_mcp/server.py:** Modified file

---

**END OF VARIANCE REPORT**

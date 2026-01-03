# Investigation Report: INV-2026-001

**Title:** GMP Process Failure - CR-2026-004 Post-Approval of Dysfunctional Code
**Date:** 2026-01-01
**Investigator:** Claude (Senior Staff Engineer)
**Classification:** CRITICAL
**Status:** OPEN

---

## 1. Executive Summary

On 2026-01-01, Change Record CR-2026-004 (Command Package Split & ToolContext Adoption) was approved through the full GMP workflow (Pre-Approval and Post-Approval) and committed to the main branch. The application subsequently failed to launch in simulation mode due to an `AttributeError` in BrushTool.

This investigation identifies the specific procedural deviations that allowed dysfunctional code to pass through the Change Review Board and proposes Corrective and Preventive Actions (CAPAs) to prevent recurrence.

**Impact:** Application non-functional after release
**Root Cause:** Multiple GMP procedural failures at design, implementation, and review phases

---

## 2. Incident Timeline

| Time | Event | Actor |
|------|-------|-------|
| T+0 | CR-2026-004 drafted combining Phases G, I, J | Engineer |
| T+1 | QA Pre-Approval: Assigned TU-SCENE, TU-INPUT, TU-UI | QA |
| T+2 | TU-SCENE: APPROVED with conditions C6, C7 | TU-SCENE |
| T+3 | TU-INPUT: APPROVED with conditions C-INPUT-01, C-INPUT-02, C-INPUT-03 | TU-INPUT |
| T+4 | TU-UI: APPROVED with conditions C1-UI, C2-UI, C3-UI | TU-UI |
| T+5 | Implementation: Phase G completed | Engineer |
| T+6 | Implementation: Tool base class updated | Engineer |
| T+7 | Implementation: FlowStateApp.init_tools() updated | Engineer |
| T+8 | QA Post-Approval: APPROVED WITH OBSERVATIONS | QA |
| T+9 | Commit fee0fac pushed to main | Engineer |
| T+10 | **Application fails to launch** | User |
| T+11 | Investigation initiated | Engineer |

---

## 3. Technical Failure Analysis

### 3.1 The Defect

**Location:** `ui/tools.py` line 127

```python
class BrushTool:  # Does NOT inherit from Tool
    def __init__(self, app):
        self.app = app  # Stores whatever is passed directly
```

**Trigger:** `app/flow_state_app.py` line 217

```python
self.session.tools[tid] = cls(ctx)  # Passes ToolContext, not app
```

**Failure Mode:** BrushTool receives ToolContext but expects FlowStateApp. When `BrushTool.update()` accesses `self.app.session`, it fails because ToolContext has no `session` attribute.

### 3.2 Why The Defect Was Not Caught

| Phase | Expected Check | Actual Check | Gap |
|-------|----------------|--------------|-----|
| Design | Verify all tools inherit from Tool | Assumed universal inheritance | No verification |
| Implementation | Update all tool __init__ methods | Updated only Tool base class | BrushTool untouched |
| Testing | Runtime functional test | Import-only verification | No runtime test |
| Post-Approval | Reject if conditions NOT MET | "APPROVED WITH OBSERVATIONS" | Conditions bypassed |

---

## 4. Procedural Deviations Identified

### Deviation D1: Unverified Design Assumptions

**SOP Reference:** SOP-001 Section 4.1 (Pre-Approval Requirements)

**Expected Behavior:** Design assumptions must be verified before pre-approval.

**Actual Behavior:** CR-2026-004 Section 3.2 stated "Tool base class changes from `__init__(self, app)` to `__init__(self, ctx)`" without verifying that all tools inherit from Tool.

**Evidence:**
- No grep for `class.*Tool` in plan
- No inheritance hierarchy documented
- BrushTool (line 127) does not inherit from Tool

---

### Deviation D2: Incomplete Implementation Scope Verification

**SOP Reference:** SOP-002 Section 2.1 (Surgical Precision)

**Expected Behavior:** Implementation scope must match pre-approved plan exactly.

**Actual Behavior:** Plan stated "Update all tools to use ToolContext" but only the Tool base class was modified. Tools not inheriting from Tool were silently skipped.

**Evidence:**
- BrushTool.__init__ still accepts `app` parameter
- GeometryTool inherits from Tool (affected)
- BrushTool does not inherit from Tool (not affected, but receives wrong argument)

---

### Deviation D3: "Approved with Conditions" Used as Approval

**SOP Reference:** SOP-001 Section 5 (Two-Stage Approval)

**Expected Behavior:** A Change Record must fully satisfy all conditions before approval.

**Actual Behavior:** TU reviewers issued "APPROVED WITH CONDITIONS" which was treated as approval rather than rejection pending condition satisfaction.

**Evidence:**
- TU-INPUT: "APPROVED WITH CONDITIONS" (C-INPUT-01, C-INPUT-02, C-INPUT-03)
- TU-UI: "APPROVED WITH CONDITIONS" (C1-UI, C2-UI, C3-UI)
- No mechanism to verify conditions were met before proceeding

---

### Deviation D4: Post-Approval Despite Explicit Non-Compliance

**SOP Reference:** SOP-001 Section 5.3 (Post-Approval Requirements)

**Expected Behavior:** Post-approval requires verification that all pre-approval conditions are MET.

**Actual Behavior:** QA Post-Approval explicitly stated:
- "C1-UI: NOT MET"
- "C-INPUT-03: PENDING"

Yet the verdict was "APPROVED WITH OBSERVATIONS" rather than REJECTED.

**Evidence:** CR-2026-004 Review Log entry:
> "QA | APPROVED | Post-Approval. Plan adherence verified. C1-UI incomplete (factory added but not adopted). C-INPUT-03 pending manual testing."

---

### Deviation D5: Inadequate Verification Protocol

**SOP Reference:** SOP-002 Section 3 (Test Protocol)

**Expected Behavior:** Verification must include runtime functional testing.

**Actual Behavior:** Verification consisted only of import statements:
```python
python -c "from module import Class"  # Import only, no runtime test
```

**Evidence:** CR-2026-004 Section 10.5 "Verification" shows only import tests. No actual tool operation was tested.

---

### Deviation D6: Rationalization of Non-Compliance

**SOP Reference:** SOP-001 Section 6 (Review Standards)

**Expected Behavior:** Reviewers must not rationalize or excuse non-compliance.

**Actual Behavior:** QA Post-Approval stated:
> "This is a migration incompleteness rather than an architectural violation"
> "The existing code path is unchanged"

This rationalization was factually incorrect—the code path WAS changed by passing `ctx` instead of `self`.

**Evidence:** QA Post-Approval findings rationalized C1-UI non-compliance as acceptable.

---

## 5. Root Cause Analysis

### 5.1 Immediate Cause
BrushTool does not inherit from Tool, so changing Tool.__init__ had no effect on BrushTool.

### 5.2 Contributing Causes
1. **Design Phase:** No verification of tool inheritance hierarchy
2. **Implementation Phase:** Blind assumption that base class change affects all tools
3. **Review Phase:** "Approved with conditions" treated as approval
4. **Testing Phase:** Import-only verification, no runtime tests

### 5.3 Systemic Cause
The GMP process lacks:
1. Mandatory inheritance/dependency verification for refactoring CRs
2. Clear rejection semantics for conditional approvals
3. Runtime verification requirements in test protocol
4. Prohibition on rationalizing non-compliance

---

## 6. Corrective and Preventive Actions (CAPAs)

### CAPA-001: Eliminate "Approved with Conditions" Status

**Type:** Preventive
**Priority:** CRITICAL
**Owner:** QA

**Action:** Revise SOP-001 to eliminate "APPROVED WITH CONDITIONS" as a valid status. The only valid statuses shall be:
- APPROVED (all requirements met)
- REJECTED (requirements not met, with specific deficiencies listed)

**Rationale:** "Approved with conditions" creates ambiguity. If conditions exist, the CR is not ready for approval.

**Implementation:**
1. Update SOP-001 Section 5 to remove conditional approval
2. Update TU/QA review templates to remove "WITH CONDITIONS" option
3. Require explicit re-review after condition remediation

---

### CAPA-002: Mandatory Dependency Verification for Refactoring CRs

**Type:** Preventive
**Priority:** HIGH
**Owner:** Engineer

**Action:** For any CR that modifies base classes, interfaces, or shared components, require explicit verification of all dependents.

**Rationale:** CR-2026-004 assumed all tools inherit from Tool without verification.

**Implementation:**
1. Add to SOP-002: "Refactoring CRs must include grep/search results showing all affected classes"
2. Add checklist item: "All classes inheriting from modified base class identified: [ ]"
3. Require inheritance hierarchy documentation for base class changes

---

### CAPA-003: Runtime Verification Requirement

**Type:** Preventive
**Priority:** CRITICAL
**Owner:** QA

**Action:** Test Protocol (SOP-002 Section 3) must require runtime functional tests, not just import tests.

**Rationale:** Import tests only verify syntax and module resolution. Runtime tests verify actual behavior.

**Implementation:**
1. Update SOP-002 Section 3 to require: "Application must launch and complete one update cycle"
2. Define minimum runtime test: instantiate app, call update(), verify no exceptions
3. Import-only verification explicitly prohibited as sole verification method

---

### CAPA-004: Prohibit Rationalization of Non-Compliance

**Type:** Preventive
**Priority:** HIGH
**Owner:** QA

**Action:** Add explicit prohibition in SOP-001: Reviewers must not rationalize or excuse non-compliance. If a condition is NOT MET, the CR is REJECTED.

**Rationale:** QA rationalized C1-UI non-compliance as "migration incompleteness rather than architectural violation."

**Implementation:**
1. Add to SOP-001 Section 6: "Rationalization Prohibition"
2. Define: Any statement of form "X is not met but acceptable because Y" constitutes rationalization
3. Require: Non-compliance must result in REJECTED status, full stop

---

### CAPA-005: Pre-Approval Assumption Documentation

**Type:** Preventive
**Priority:** MEDIUM
**Owner:** Engineer

**Action:** CR Pre-Approval must explicitly list assumptions and verification of each.

**Rationale:** CR-2026-004 assumed universal Tool inheritance without stating or verifying this assumption.

**Implementation:**
1. Add "Assumptions" section to CR template
2. Each assumption must have verification evidence
3. TU reviewers must validate assumptions before approval

---

### CAPA-006: Post-Approval Condition Gate

**Type:** Corrective
**Priority:** CRITICAL
**Owner:** QA

**Action:** Post-approval review must include explicit verification that ALL pre-approval conditions are MET. Any condition NOT MET or PENDING results in automatic REJECTION.

**Rationale:** CR-2026-004 was post-approved with C1-UI "NOT MET" and C-INPUT-03 "PENDING".

**Implementation:**
1. Add condition compliance matrix to post-approval template
2. Require all conditions show "MET" status
3. "NOT MET" or "PENDING" on any condition = automatic REJECTION

---

### CAPA-007: Inheritance Hierarchy Linting

**Type:** Preventive
**Priority:** MEDIUM
**Owner:** Engineer

**Action:** For tool-related changes, implement pre-commit check that verifies all tool classes in ui/tools.py inherit from Tool base class.

**Rationale:** BrushTool's lack of inheritance was a latent defect that became critical when the base class changed.

**Implementation:**
1. Add linting rule: All classes named *Tool must inherit from Tool
2. Or document explicitly why a class does not inherit
3. Run as part of pre-commit hooks

---

## 7. Immediate Corrective Action Required

The current main branch contains dysfunctional code. Before CAPAs can be implemented, the immediate defect must be fixed:

**Option A:** Revert CR-2026-004 entirely
**Option B:** Hot-fix BrushTool to inherit from Tool or handle ctx properly

This decision is deferred to the Lead Engineer.

---

## 8. Conclusion

CR-2026-004 exposed systemic weaknesses in the GMP process:

1. **Design assumptions were not verified**
2. **"Approved with conditions" was treated as approval**
3. **Non-compliance was rationalized rather than rejected**
4. **Verification was inadequate (import-only)**

The proposed CAPAs address each failure mode. Implementation of CAPAs should be prioritized as indicated.

---

## 9. Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-01 | Claude | Initial draft |

---

*Investigation Status: OPEN*
*Pending: Lead Engineer review, CAPA prioritization, Immediate corrective action decision*

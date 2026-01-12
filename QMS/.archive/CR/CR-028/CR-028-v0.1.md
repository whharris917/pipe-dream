---
title: 'QMS CLI Qualification: RS and RTM'
revision_summary: Initial draft
---

# CR-028: QMS CLI Qualification: RS and RTM

## 1. Purpose

Establish formal qualification of the QMS CLI (`qms-cli/`) by creating the Requirements Specification (SDLC-QMS-RS) and Requirements Traceability Matrix (SDLC-QMS-RTM). Upon approval of the RTM, the QMS CLI becomes a qualified system under QMS governance.

---

## 2. Scope

### 2.1 Context

The QMS CLI is the primary tooling for document control operations. While it resides outside `QMS/`, it implements and enforces the procedures defined in SOPs. Qualification tethers `qms-cli/` to the QMS via the SDLC-QMS document family, enabling proper change control for future modifications.

- **Parent Document:** None (initial qualification)

### 2.2 Changes Summary

- Create SDLC-QMS-RS (Requirements Specification) as a non-executable document
- Create SDLC-QMS-RTM (Requirements Traceability Matrix) as a non-executable document
- Add unit tests and inline qualitative proofs as necessary during RTM drafting

### 2.3 Files Affected

- `QMS/SDLC-QMS/SDLC-QMS-RS.md` - New document
- `QMS/SDLC-QMS/SDLC-QMS-RTM.md` - New document
- `qms-cli/tests/` - Additional unit tests as needed

---

## 3. Current State

The QMS CLI exists as unqualified tooling. It implements SOP requirements but lacks formal requirements documentation and traceability. Changes to the CLI are not subject to impact assessment against documented requirements.

---

## 4. Proposed State

The QMS CLI is a qualified system with:
- **SDLC-QMS-RS:** Documents functional requirements derived from SOPs
- **SDLC-QMS-RTM:** Traces each requirement to implementation evidence (unit tests, inline proofs, code references)

Future CRs affecting `qms-cli/` will reference specific requirements and demonstrate continued compliance.

---

## 5. Change Description

### 5.1 Phase 1: Requirements Specification (RS)

Draft SDLC-QMS-RS containing:
- Requirements derived from SOP-001 (Document Control) and SOP-002 (Change Control)
- Requirements for CLI command behaviors, permission enforcement, and workflow state management
- Requirements for prompt generation (per CR-027 YAML-based prompts)

The RS follows the standard non-executable workflow: DRAFT → IN_REVIEW → REVIEWED → IN_APPROVAL → EFFECTIVE.

### 5.2 Phase 2: Requirements Traceability Matrix (RTM)

After RS approval, draft SDLC-QMS-RTM containing:
- Each requirement from SDLC-QMS-RS
- Traceability to implementation evidence:
  - Unit test references (existing or newly created)
  - Inline qualitative proofs where testing is impractical
  - Code file and line references

The RTM follows the standard non-executable workflow. Drafting the RTM *is* the qualification activity—it demonstrates that each requirement is satisfied.

### 5.3 Qualification Completion

Upon RTM approval, the QMS CLI is officially qualified. Subsequent changes require:
- Impact assessment against SDLC-QMS-RS requirements
- Updates to SDLC-QMS-RTM as needed
- Demonstration of continued compliance

---

## 6. Justification

- **Governance gap:** The QMS CLI enforces SOP requirements but is not itself governed
- **Change control:** Without documented requirements, changes cannot be properly assessed for impact
- **Traceability:** Qualification establishes the baseline for demonstrating continued compliance
- **Pragmatic approach:** Initial qualification focuses on documenting current state; future CRs will address specific requirement changes with appropriate rigor

---

## 7. Impact Assessment

### 7.1 Files Affected

| File | Change Type | Description |
|------|-------------|-------------|
| `QMS/SDLC-QMS/SDLC-QMS-RS.md` | Create | Requirements Specification |
| `QMS/SDLC-QMS/SDLC-QMS-RTM.md` | Create | Requirements Traceability Matrix |
| `qms-cli/tests/` | Modify | Additional unit tests as needed |

### 7.2 Documents Affected

| Document | Change Type | Description |
|----------|-------------|-------------|
| SDLC-QMS-RS | Create | New requirements specification |
| SDLC-QMS-RTM | Create | New traceability matrix |

### 7.3 Other Impacts

None. This CR documents and qualifies existing functionality; it does not change CLI behavior.

---

## 8. Testing Summary

- Existing unit tests (195 passing) demonstrate current functionality
- Additional unit tests created during RTM drafting will extend coverage
- RTM approval serves as the formal verification that requirements are met

---

## 9. Implementation Plan

### 9.1 Create and Approve RS

1. Create SDLC-QMS-RS document
2. Draft requirements based on SOP analysis
3. Route RS through review and approval workflow

### 9.2 Create and Approve RTM

1. Create SDLC-QMS-RTM document
2. For each requirement, identify or create evidence:
   - Reference existing unit tests
   - Create new unit tests where gaps exist
   - Add inline qualitative proofs where testing is impractical
3. Route RTM through review and approval workflow

### 9.3 Close CR

1. Verify both RS and RTM are EFFECTIVE
2. Document qualification completion

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
| EI-1 | Create and approve SDLC-QMS-RS | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-2 | Create and approve SDLC-QMS-RTM | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-3 | Verify qualification completion | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |

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
- **CR-027:** Extract Prompts to External YAML Files (prompt requirements source)

---

**END OF DOCUMENT**

---
title: Verification Record (VR) Document Type
revision_summary: Initial draft
---

# CR-089: Verification Record (VR) Document Type

## 1. Purpose

Introduce Verification Records (VR) as a new QMS document type for structured behavioral testing. VRs provide a pre-approved evidence form for unscripted integration verification, replacing mandate-based language scattered across SOPs and templates with a concrete, auditable document.

---

## 2. Scope

### 2.1 Context

Session-2026-02-16-004 identified a gap: integration verification requirements (CR-084) had no structured form, producing a "mandate escalation cycle" where prose mandates could be technically satisfied without demonstrating behavioral correctness. The CR-088 health check deficiency exemplified this — a structural check passed while the actual behavior was broken.

- **Parent Document:** None (design-driven improvement from Session-2026-02-16-004)

### 2.2 Changes Summary

Add VR as a new executable child document type. VRs are born IN_EXECUTION (template is the pre-approval), follow standard post-execution workflow (post-review, post-approval, closure), and serve as the primary mechanism for unscripted behavioral verification. Supporting changes update SOPs, templates, and SDLC documents to reference VRs.

### 2.3 Files Affected

**QMS CLI (qms-cli submodule):**
- `qms-cli/qms_schema.py` — Add VR to type sets and ID patterns
- `qms-cli/qms_config.py` — Add VR to document type registry
- `qms-cli/qms_paths.py` — Add VR type detection and path resolution; fix deep nesting bug
- `qms-cli/commands/create.py` — Add VR parent validation, ID generation, initial state override
- `qms-cli/seed/templates/TEMPLATE-VR.md` — Seed template for `qms init`
- `qms-cli/tests/qualification/test_document_types.py` — VR qualification tests
- `qms-cli/tests/conftest.py` — Add VR directories to test fixture

**QMS Controlled Documents:**
- `QMS/TEMPLATE/TEMPLATE-VR.md` — New controlled template
- `QMS/TEMPLATE/TEMPLATE-CR.md` — Add VR column to EI table
- `QMS/TEMPLATE/TEMPLATE-VAR.md` — Add VR column to EI table
- `QMS/TEMPLATE/TEMPLATE-ADD.md` — Add VR column to EI table
- `QMS/SOP/SOP-001.md` — Add VR to definitions and naming conventions
- `QMS/SOP/SOP-002.md` — Simplify Section 6.8, add VR post-review gate
- `QMS/SOP/SOP-004.md` — Add VR to scope, EI table column, new Section 9C, post-review gate
- `QMS/SOP/SOP-006.md` — Add VR as third verification type
- `QMS/SDLC-QMS/SDLC-QMS-RS.md` — Add VR requirements
- `QMS/SDLC-QMS/SDLC-QMS-RTM.md` — Add VR test entries and qualified baseline

---

## 3. Current State

The QMS supports seven document types for executable workflows: CR, INV, TP, ER, VAR, ADD, and TEMPLATE. Integration verification is mandated by SOP-002 Section 6.8 as prose requirements, with no structured form for recording behavioral observations. The RTM supports two verification types: Unit Test and Qualitative Proof.

---

## 4. Proposed State

The QMS supports VR as an eighth executable document type. VRs are lightweight child documents of CR, VAR, or ADD, created during parent execution. They are born IN_EXECUTION at v1.0 (the approved TEMPLATE-VR serves as pre-approval authority) and follow standard post-execution workflow. The RTM supports three verification types: Unit Test, Qualitative Proof, and Verification Record. EI tables in CR, VAR, and ADD templates include a VR column indicating which execution items require behavioral verification.

---

## 5. Change Description

### 5.1 VR Lifecycle

VR is an executable document with a unique creation behavior: it is born directly at IN_EXECUTION (v1.0) with execution_phase set to post_release. This skips the DRAFT through PRE_APPROVED phases entirely — the approved TEMPLATE-VR serves as the pre-approval authority (batch record model from GMP).

From IN_EXECUTION onward, VR follows the standard executable workflow: post-review, post-approval, and closure. No changes to `workflow.py` are required.

**VR workflow:**
```
create (IN_EXECUTION v1.0, checked out) → fill in → checkin
→ route post-review → QA review → route post-approval → QA approve → close
```

### 5.2 VR as Child Document

VR can be created under CR, VAR, or ADD parents that are in IN_EXECUTION state. VR documents are stored in the parent CR's folder, following the same path resolution pattern as VAR and ADD.

**Naming:** `{PARENT_ID}-VR-{NNN}` (e.g., CR-089-VR-001, CR-089-VAR-001-VR-001)

### 5.3 CLI Code Changes

**qms_schema.py:** Add VR to DOC_TYPES and EXECUTABLE_TYPES. Add VR ID pattern supporting nesting under CR, VAR, and ADD.

**qms_config.py:** Add VR entry with `executable: True`, `path: "CR"`.

**qms_paths.py:** Add VR detection in `get_doc_type()` (before ADD check), add VR to nested path resolution in `get_doc_path()` and `get_archive_path()`. Fix `get_next_nested_number()` to resolve deeply nested parents (VAR, ADD) to their top-level CR/INV folder — this also fixes a latent bug for ADD-under-VAR ID generation.

**create.py:** Add VR to parent-required types. Validate parent type (CR, VAR, or ADD) and parent status (IN_EXECUTION). Generate nested VR IDs. After `create_initial_meta()`, override meta for VR: status=IN_EXECUTION, version=1.0, execution_phase=post_release.

### 5.4 EI Table VR Column

EI tables in TEMPLATE-CR, TEMPLATE-VAR, and TEMPLATE-ADD gain a VR column between Task Description and Execution Summary:

```
| EI | Task Description | VR | Execution Summary | Task Outcome | Performed By — Date |
```

VR column values:
- Blank: no VR required for this EI
- `Yes`: VR required (design-time flag, set during drafting)
- `{VR-ID}`: VR created and linked (execution-time, filled during execution)

### 5.5 SOP Updates

**SOP-002:** Simplify Section 6.8 to reference VRs as the integration verification mechanism. Add VR gate to post-review requirements.

**SOP-004:** Add VR to scope. Add VR column to canonical EI table definition. New Section 9C defining VR lifecycle, creation, and content requirements. Update post-review gate.

**SOP-006:** Add VR as third RTM verification type alongside Unit Test and Qualitative Proof.

**SOP-001:** Add VR to definitions and naming conventions.

### 5.6 TEMPLATE-VR

The VR template (drafted in Session-2026-02-16-004) provides structured sections for: Verification Identification, Verification Objective, Pre-Conditions, Procedure, Observations, Outcome (positive/negative/overall), and Signature.

---

## 6. Justification

- Integration verification mandates (CR-084) lack a structured form, enabling compliance that satisfies the letter but not the spirit of verification requirements
- The "mandate escalation cycle" (failure → stronger mandate → weak compliance → failure) is broken by providing form instead of mandate
- VRs create auditable evidence of behavioral testing that can be independently reviewed by QA
- Adding VR as a third RTM verification type closes a traceability gap between requirements and behavioral evidence

---

## 7. Impact Assessment

### 7.1 Files Affected

| File | Change Type | Description |
|------|-------------|-------------|
| `qms-cli/qms_schema.py` | Modify | Add VR to type sets and ID patterns |
| `qms-cli/qms_config.py` | Modify | Add VR to document type registry |
| `qms-cli/qms_paths.py` | Modify | Add VR type detection, path resolution, fix deep nesting |
| `qms-cli/commands/create.py` | Modify | Add VR parent validation, ID generation, state override |
| `qms-cli/seed/templates/TEMPLATE-VR.md` | Create | Seed template |
| `qms-cli/tests/qualification/test_document_types.py` | Modify | Add 8 VR qualification tests |
| `qms-cli/tests/conftest.py` | Modify | Add VR directories to fixture |

### 7.2 Documents Affected

| Document | Change Type | Description |
|----------|-------------|-------------|
| TEMPLATE-VR | Create | New controlled template for VR documents |
| TEMPLATE-CR | Modify | Add VR column to EI table |
| TEMPLATE-VAR | Modify | Add VR column to EI table |
| TEMPLATE-ADD | Modify | Add VR column to EI table |
| SOP-001 | Modify | Add VR to definitions and naming |
| SOP-002 | Modify | Simplify Section 6.8, add VR post-review gate |
| SOP-004 | Modify | Add VR scope, EI column, Section 9C, post-review gate |
| SOP-006 | Modify | Add VR as third verification type |
| SDLC-QMS-RS | Modify | Add VR requirements |
| SDLC-QMS-RTM | Modify | Add VR test entries and qualified baseline |

### 7.3 Other Impacts

None. VR is additive — no existing functionality is removed or altered.

### 7.4 Development Controls

This CR implements changes to qms-cli, a controlled submodule. Development follows established controls:

1. **Test environment isolation:** Development in a non-QMS-controlled directory (e.g., `.test-env/`, `/projects/` for containerized agents, or other gitignored location)
2. **Branch isolation:** All development on branch `feature/vr-document-type`
3. **Write protection:** `.claude/settings.local.json` blocks direct writes to `qms-cli/`
4. **Qualification required:** All new/modified requirements must have passing tests before merge
5. **CI verification:** Tests must pass on GitHub Actions for dev branch
6. **PR gate:** Changes merge to main only via PR after RS/RTM approval
7. **Submodule update:** Parent repo updates pointer only after PR merge

### 7.5 Qualified State Continuity

| Phase | main branch | RS/RTM Status | Qualified Release |
|-------|-------------|---------------|-------------------|
| Before CR | Current commit | EFFECTIVE v14.0/v18.0 | CLI-9.0 |
| During execution | Unchanged | DRAFT (checked out) | CLI-9.0 (unchanged) |
| Post-approval | Merged from feature/vr-document-type | EFFECTIVE v15.0/v19.0 | CLI-10.0 |

---

## 8. Testing Summary

### Automated Verification

Eight new qualification tests covering VR creation, parent validation, initial state, and ID generation:

- `test_create_vr_under_cr` — VR created as child of IN_EXECUTION CR
- `test_create_vr_under_var` — VR created under VAR with nested ID
- `test_create_vr_under_add` — VR created under ADD with nested ID
- `test_vr_requires_parent` — Error when --parent omitted
- `test_vr_rejects_invalid_parent_type` — Error for TP/ER/SOP parent
- `test_vr_requires_in_execution_parent` — Error when parent not IN_EXECUTION
- `test_vr_born_in_execution` — Initial status IN_EXECUTION, v1.0, post_release
- `test_vr_sequential_id_generation` — Sequential VR IDs under same parent

### Integration Verification

- Create a VR under an IN_EXECUTION CR via CLI
- Verify VR is IN_EXECUTION at v1.0 and checked out
- Fill in the VR form, check in
- Route for post-review, verify standard executable workflow operates correctly
- Attempt VR creation with invalid parent type and state, verify rejection

---

## 9. Implementation Plan

### 9.1 Phase 1: Test Environment Setup

1. Verify qms-cli submodule is on main and clean
2. Create and checkout branch `feature/vr-document-type`
3. Verify clean test environment

### 9.2 Phase 2: Requirements (RS Update)

1. Checkout SDLC-QMS-RS in production QMS
2. Update REQ-DOC-001 (add VR to type list), REQ-DOC-002 (VR parent-child), REQ-DOC-005 (VR naming example)
3. Add REQ-DOC-016 (VR parent state), REQ-DOC-017 (VR initial status)
4. Checkin RS, route for review and approval

### 9.3 Phase 3: Implementation

1. Implement VR type in qms_schema.py, qms_config.py, qms_paths.py, create.py
2. Fix get_next_nested_number for deep nesting
3. Add seed template
4. Test locally
5. Commit to dev branch

### 9.4 Phase 4: Qualification

1. Write 8 VR qualification tests
2. Update conftest.py test fixture
3. Run full test suite, verify all tests pass
4. Push to dev branch
5. Verify GitHub Actions CI passes
6. Document qualified commit hash

### 9.5 Phase 5: Integration Verification

1. Create VR under an IN_EXECUTION CR
2. Verify initial state: IN_EXECUTION v1.0, checked out, correct path
3. Fill in VR form, check in
4. Attempt creation with invalid parent type/state, verify rejection
5. Document observations

### 9.6 Phase 6: RTM Update and Approval

1. Checkout SDLC-QMS-RTM in production QMS
2. Add VR test entries referencing CI-verified commit
3. Update qualified baseline
4. Checkin RTM, route for review and approval
5. **Verify RTM reaches EFFECTIVE status before proceeding to Phase 7**

### 9.7 Phase 7: Merge and Submodule Update

**Prerequisite:** RS and RTM must both be EFFECTIVE (per SOP-006 Section 7.4).

1. Verify RS is EFFECTIVE (document status check)
2. Verify RTM is EFFECTIVE (document status check)
3. Create PR to merge dev branch to main
4. Merge PR using merge commit — not squash (per SOP-005 Section 7.1.3)
5. Verify qualified commit hash from execution branch is reachable on main
6. Update submodule pointer in parent repo
7. Verify functionality in production context

### 9.8 Phase 8: Controlled Document Updates

1. Create TEMPLATE-VR as controlled document
2. Update SOP-001 (definitions, naming)
3. Update SOP-002 (Section 6.8 simplification, post-review gate)
4. Update SOP-004 (EI column, Section 9C, post-review gate)
5. Update SOP-006 (third verification type)
6. Update TEMPLATE-CR, TEMPLATE-VAR, TEMPLATE-ADD (VR column in EI tables)

---

## 10. Execution

| EI | Task Description | Execution Summary | Task Outcome | Performed By - Date |
|----|------------------|-------------------|--------------|---------------------|
| EI-01 | Pre-execution commit | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-02 | Create execution branch in qms-cli | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-03 | Update SDLC-QMS-RS with VR requirements | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-04 | Implement VR document type in CLI (schema, config, paths, create) | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-05 | Fix get_next_nested_number for deep nesting | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-06 | Write VR qualification tests | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-07 | Run full test suite, record qualified commit | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-08 | Update SDLC-QMS-RTM with VR test entries | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-09 | Merge to main, update submodule pointer | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-10 | Create TEMPLATE-VR controlled document | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-11 | Update SOP-001 (definitions, naming) | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-12 | Update SOP-002 (Section 6.8 simplification, post-review gate) | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-13 | Update SOP-004 (EI column, Section 9C, post-review gate) | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-14 | Update SOP-006 (third verification type) | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-15 | Update TEMPLATE-CR (VR column in EI table) | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-16 | Update TEMPLATE-VAR (VR column in EI table) | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-17 | Update TEMPLATE-ADD (VR column in EI table) | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-18 | Post-execution commit | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |

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
- **SOP-004:** Document Execution
- **SOP-005:** Code Governance
- **SOP-006:** Software Development Life Cycle Governance
- **Session-2026-02-16-004:** VR design discussion and TEMPLATE-VR draft
- **CR-082:** ADD document type implementation (precedent for new type addition)
- **CR-084:** Integration verification mandate (driving requirement)

---

**END OF DOCUMENT**

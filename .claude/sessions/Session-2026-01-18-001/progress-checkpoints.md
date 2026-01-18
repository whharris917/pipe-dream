# Session Progress Checkpoints

## Session Goal
Continue qms-cli qualification work: develop RS, RTM, and qualification tests together before formal approval.

---

## Checkpoint 1: RS Review and Updates

**Objective:** Review SDLC-QMS-RS against actual qms-cli code to ensure accuracy.

**Findings:**
- REQ-SEC-002: Said "fix (Initiators)" but code shows fix is QA/lead only → Updated to match code
- REQ-SEC-004: Claimed QA has bypass but code doesn't support this → Reworded to describe auto-assignment
- REQ-DOC-001: Missing document types → Kept as-is (unused functionality to be removed later)
- REQ-AUDIT-002: Missing STATUS_CHANGE event → Added
- REQ-CFG-005: human/agent classification not implemented → Removed from RS
- REQ-DOC-012: Claimed "any SDLC namespace" but namespaces are hardcoded → Updated to describe configured namespaces

**Outcome:** RS updated and routed through review (not approved yet per user instruction).

---

## Checkpoint 2: Verification Method Overhaul

**Objective:** Convert narrow unit test verification methods to behavioral/maximal tests.

**Rationale:** Pharma requires demonstrating system "does the thing" not just "configured to do the thing."

**Action:** Updated all 56 requirements to use "Behavioral:" verification methods that execute actual CLI commands and verify observable outcomes.

**Outcome:** RS verification methods updated; QA reviewed and recommended.

---

## Checkpoint 3: Two-Tier Testing Strategy

**Objective:** Design test architecture that balances traceability with maintainability.

**Strategy Defined:**
- **Tier 1: Qualification Tests** - Behavioral, workflow-level, mapped in RTM with `[REQ-XXX]` inline markers
- **Tier 2: Unit Tests** - Diagnostic, function-level, not in RTM, help pinpoint root cause

**Documentation:** Created `testing-strategy.md` formalizing this approach.

---

## Checkpoint 4: RTM Creation

**Objective:** Create Requirements Traceability Matrix mapping all 56 requirements to test protocols.

**Structure:**
- Maps REQ-IDs to test file, function, line numbers, and assertion descriptions
- Line numbers marked TBD until tests are written
- Organized by requirement domain (DOC, WF, META, AUDIT, TASK, SEC, QUERY, CFG)

**Outcome:** SDLC-QMS-RTM created in DRAFT status.

---

## Checkpoint 5: Qualification Test Writing (SOP Lifecycle)

**Objective:** Write first qualification test protocol for non-executable document workflow.

**File:** `qms-cli/tests/qualification/test_sop_lifecycle.py`

**Tests Written:**
1. `test_sop_full_lifecycle` - Complete DRAFT → EFFECTIVE workflow
2. `test_invalid_transition` - Verify invalid transitions are rejected
3. `test_checkin_reverts_reviewed` - Checkin from REVIEWED reverts to DRAFT
4. `test_multi_reviewer_gate` - Multiple reviewers must all complete
5. `test_approval_gate_blocking` - Request-updates blocks approval routing
6. `test_rejection` - Rejection returns to REVIEWED
7. `test_retirement` - Full retirement workflow for effective documents
8. `test_retirement_rejected_for_v0` - Retirement blocked for v0.x documents

---

## Checkpoint 6: Bug Discovery and Fix (CR-031)

**Bug Found:** Tests failed because `qms_meta.py` and `qms_audit.py` hardcoded `QMS_ROOT = Path(__file__).parent.parent / "QMS"` instead of importing from `qms_paths.py`.

**Impact:** Metadata and audit files were written to production QMS instead of temp test directories.

**CR-031 Execution:**
1. Created CR-031 documenting the bug and fix
2. Edited `qms_meta.py` line 13: `from qms_paths import QMS_ROOT`
3. Edited `qms_audit.py` line 13: `from qms_paths import QMS_ROOT`
4. Updated `conftest.py` to reload qms_meta and qms_audit in module chain
5. Fixed test implementation issues:
   - Added checkin after create (create auto-checks out)
   - Fixed `--reason` to `--comment` in rejection test
6. All 8 tests passed
7. CR-031 closed

---

## Checkpoint 7: Production QMS Cleanup

**Issue:** Pre-fix test runs had contaminated production QMS files.

**Contaminated Files:**
- `QMS/.audit/CR/CR-001.jsonl`
- `QMS/.audit/CR/CR-002.jsonl`
- `QMS/.audit/SOP/SOP-001.jsonl`
- `QMS/.audit/QMS-RS/SDLC-QMS-RS.jsonl`
- `QMS/.meta/CR/CR-001.json`
- `QMS/.meta/CR/CR-002.json`
- `QMS/.meta/SOP/SOP-001.json`

**Resolution:** Used `git restore` to restore original versions (changes were uncommitted).

**Verification:** SOP-001 correctly shows EFFECTIVE v16.0; tests pass without contamination.

**Documentation:** Created `cr-031-cleanup.md` documenting this post-closure cleanup.

---

## Checkpoint 8: Remaining Test Protocols

**Objective:** Write remaining qualification test files.

**Files Created:**
1. `test_cr_lifecycle.py` - 8 tests for executable document workflow (CR)
2. `test_security.py` - 10 tests for access control (REQ-SEC-001 through REQ-SEC-006)
3. `test_document_types.py` - 12 tests for document creation and types
4. `test_queries.py` - 16 tests for query operations

---

## Checkpoint 9: Full Test Execution and Gap Analysis

**Objective:** Run all qualification tests and document gaps.

**Test Results:** 54 tests total
- **49 passed**
- **5 skipped** (documented gaps between RS and implementation)

**Skipped Tests and Reasons:**

| Test | Reason | Gap Type |
|------|--------|----------|
| `test_fix_authorization` | `fix` command reads status from frontmatter instead of .meta | CLI Bug |
| `test_owner_only_route` | Owner-only routing not enforced (REQ-SEC-003) | RS/Code Gap |
| `test_create_tp_under_cr` | TP parent enforcement not implemented | Feature Missing |
| `test_create_var_under_inv` | VAR path is hardcoded to CR, doesn't adapt to parent type | CLI Bug |
| `test_template_name_based_id` | `--name` argument not implemented for TEMPLATE | Feature Missing |

**Verification:** No production QMS contamination after test run.

---

## Current State

**Completed:**
- [x] RS reviewed and updated (in REVIEWED status, not yet approved)
- [x] RTM created (in DRAFT status)
- [x] Testing strategy documented
- [x] test_sop_lifecycle.py written and passing (8 tests)
- [x] test_cr_lifecycle.py written and passing (8 tests)
- [x] test_security.py written (8 passed, 2 skipped)
- [x] test_document_types.py written (9 passed, 3 skipped)
- [x] test_queries.py written and passing (16 tests)
- [x] CR-031 bug fix complete and closed
- [x] Production QMS contamination cleaned up
- [x] All tests executed: 49 passed, 5 skipped

**Remaining:**
- [ ] Update RS to remove/defer requirements for unimplemented features
- [ ] Update RTM with actual line numbers from test files
- [ ] Iterate RS/RTM/tests until consistent
- [ ] Route RS and RTM for formal approval

---

## Key Files Modified/Created This Session

| File | Action | Description |
|------|--------|-------------|
| `QMS/SDLC-QMS/SDLC-QMS-RS-draft.md` | Modified | Updated requirements and verification methods |
| `QMS/SDLC-QMS/SDLC-QMS-RTM-draft.md` | Created | Requirements Traceability Matrix |
| `qms-cli/qms_meta.py` | Modified | Fixed hardcoded QMS_ROOT (CR-031) |
| `qms-cli/qms_audit.py` | Modified | Fixed hardcoded QMS_ROOT (CR-031) |
| `qms-cli/tests/conftest.py` | Modified | Added qms_meta/qms_audit to reload chain |
| `qms-cli/tests/qualification/__init__.py` | Created | Package init |
| `qms-cli/tests/qualification/test_sop_lifecycle.py` | Created | 8 qualification tests |
| `qms-cli/tests/qualification/test_cr_lifecycle.py` | Created | 8 qualification tests |
| `qms-cli/tests/qualification/test_security.py` | Created | 10 tests (8 pass, 2 skip) |
| `qms-cli/tests/qualification/test_document_types.py` | Created | 12 tests (9 pass, 3 skip) |
| `qms-cli/tests/qualification/test_queries.py` | Created | 16 qualification tests |
| `QMS/CR/CR-031/` | Created | Bug fix CR (now CLOSED) |
| `.claude/sessions/Session-2026-01-18-001/testing-strategy.md` | Created | Two-tier testing documentation |
| `.claude/sessions/Session-2026-01-18-001/cr-031-cleanup.md` | Created | Post-closure cleanup documentation |

---

## Identified Gaps: RS vs Implementation

The following gaps were discovered during qualification testing. Each represents a mismatch between what the Requirements Specification (RS) claims and what the code actually implements.

### Gap 1: `fix` Command Reads Wrong Source

**Test:** `test_fix_authorization`
**Requirement:** REQ-SEC-002
**Type:** CLI Bug

**Problem:** The `fix` command reads document status from frontmatter (`frontmatter.get("status")`) instead of from `.meta` files, which are the authoritative source of workflow state.

**Impact:** When a document becomes EFFECTIVE through the approval workflow, the `.meta` status is updated but frontmatter may not be. The `fix` command then fails with "Fix only applies to EFFECTIVE/CLOSED documents (current: )".

**Location:** `qms-cli/commands/fix.py` lines 43-48

---

### Gap 2: Owner-Only Routing Not Enforced

**Test:** `test_owner_only_route`
**Requirement:** REQ-SEC-003
**Type:** RS/Code Gap

**Problem:** REQ-SEC-003 states "Checkin, Route, Cancel: Only document owner" but the `route` command only checks group-level permissions, not document ownership.

**Impact:** Any user in the `initiators` or `qa` groups can route any document, not just documents they own. This violates the principle that only the responsible user should control their document's workflow progression.

**Location:** `qms-cli/commands/route.py` - missing owner check after line 48

**Config Reference:** `qms_config.py` line 119 shows `"route": {"groups": ["initiators", "qa"]}` without `"owner_only": True`

---

### Gap 3: TP Parent Enforcement Missing

**Test:** `test_create_tp_under_cr`
**Requirement:** REQ-DOC-002
**Type:** Feature Missing

**Problem:** The `create` command only enforces `--parent` for VAR document type. When creating a TP (Test Protocol), the `--parent` argument is ignored and the system generates a sequential ID like "TP-001" instead of the expected "CR-001-TP".

**Impact:** Test Protocols cannot be properly associated with their parent Change Records. The ID format and folder structure are incorrect.

**Location:** `qms-cli/commands/create.py` lines 56-73 only handle VAR type specially

---

### Gap 4: VAR Path Hardcoded to CR Directory

**Test:** `test_create_var_under_inv`
**Requirement:** REQ-DOC-002
**Type:** CLI Bug

**Problem:** The VAR document type config has `"path": "CR"` hardcoded. When creating a VAR under an INV parent, the file is created in `QMS/CR/INV-001/` instead of `QMS/INV/INV-001/`.

**Impact:** Variance Reports under Investigations are stored in the wrong directory, breaking the expected folder structure.

**Location:** `qms_config.py` line 85: `"VAR": {"path": "CR", ...}`
**Location:** `qms_paths.py` lines 84-88 - path resolution doesn't adapt to parent type

---

### Gap 5: TEMPLATE `--name` Argument Missing

**Test:** `test_template_name_based_id`
**Requirement:** REQ-DOC-011
**Type:** Feature Missing

**Problem:** REQ-DOC-011 specifies that TEMPLATE documents use name-based IDs (e.g., "TEMPLATE-CR", "TEMPLATE-SOP") instead of sequential numbers. However, the `create` command doesn't support a `--name` argument for TEMPLATE type.

**Impact:** Templates are created with sequential IDs like "TEMPLATE-001" instead of meaningful names like "TEMPLATE-CR". This makes it harder to identify which template is for which document type.

**Location:** `qms-cli/commands/create.py` - no `--name` argument defined

---

## Recommended Actions

| Gap | Priority | Recommended Action |
|-----|----------|-------------------|
| Gap 1 (fix reads frontmatter) | Medium | Create CR to update `fix` command to read from `.meta` |
| Gap 2 (owner-only route) | High | Either update RS to remove owner-only requirement, or create CR to add enforcement |
| Gap 3 (TP parent) | Low | Defer - TP type not actively used |
| Gap 4 (VAR path) | Low | Defer - VAR under INV not actively used |
| Gap 5 (TEMPLATE --name) | Low | Defer - Templates not actively used |

**Decision Required:** Should the RS be updated to match current implementation (removing unimplemented features), or should CRs be created to implement the missing features?

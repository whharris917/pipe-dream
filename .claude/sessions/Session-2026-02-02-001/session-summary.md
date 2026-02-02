# Session 2026-02-02-001: INV-007 and CR-048 Workflow Improvements

## Session Overview

This session analyzed INV-007 (workflow gaps), resolved open questions about versioning semantics, created CR-048 to implement comprehensive workflow improvements, and advanced CR-048 through pre-approval to release.

## Key Decisions Made

### 1. Versioning Model (Finalized)

**Executable documents during execution:**
- Release at N.0 → IN_EXECUTION
- First checkout/checkin → N.1 (archives N.0)
- Subsequent checkout/checkin → N.2, N.3, etc. (each archives previous)
- Closure → (N+1).0 POST_APPROVED → CLOSED (terminal)

**Closure is terminal** - no re-opening. Post-closure corrections use Addendum documents (future).

### 2. Archival Timing Principle (Finalized)

**"Archive when committing, not when editing."**

| Scenario | Checkout | Commit (Checkin/Approval) |
|----------|----------|---------------------------|
| EFFECTIVE N.0 → N.1 | Create N.1 draft; N.0 stays | Approve N.1 → archive N.0 |
| DRAFT N.1 → N.2 | Create N.2 in workspace | Checkin N.2 → archive N.1 |
| IN_EXECUTION N.0 → N.1 | Create N.1 in workspace | Checkin N.1 → archive N.0 |
| IN_EXECUTION N.1 → N.2 | Create N.2 in workspace | Checkin N.2 → archive N.1 |

**Principle:** Effective version remains "in force" until superseded by approval/checkin.

### 3. Core Commands Philosophy

Five core commands cover all scenarios:
- `create`, `checkout`, `checkin`, `release`, `route`

Niche commands (like `revert`) are deprecated; checkout handles status-aware transitions.

### 4. New Withdraw Command

Allows document owners to abort in-progress review/approval workflows without rejection.

## Documents Processed

| Document | Action | Final Status |
|----------|--------|--------------|
| INV-007 | Rewrote, routed, reviewed, approved, released | IN_EXECUTION (v1.0) |
| CR-048 | Created, drafted, reviewed, approved, released | IN_EXECUTION (v1.0) |

## INV-007: Executable Document Checkout Workflow Gaps

**Scope:** Two deviations identified:
1. PRE_APPROVED checkout does not enable scope revision
2. POST_REVIEWED checkout creates unnecessary DRAFT intermediate state

**CAPA-001:** Create CR to implement status-aware checkout behavior

**Status:** IN_EXECUTION - CAPA authorized

## CR-048: Workflow Improvements

**Scope:** Addresses INV-007 CAPA plus independent improvements:

| Requirement | Description | Source |
|-------------|-------------|--------|
| REQ-WF-016 | PRE_APPROVED checkout → DRAFT | INV-007 |
| REQ-WF-017 | POST_REVIEWED checkout → IN_EXECUTION | INV-007 |
| REQ-WF-018 | Withdraw command | Independent |
| REQ-WF-019 | Revert command deprecation | Independent |
| REQ-WF-020 | Effective version preservation | Independent |
| REQ-WF-021 | Execution version tracking | Independent |

**Status:** IN_EXECUTION (v1.0) - Ready for EI execution

**Execution Items (14 total):**
1. Test environment setup
2. RS update (add REQ-WF-016 through REQ-WF-021)
3. Implement checkout.py status-aware transitions
4. Implement checkout.py: remove archival, effective version preservation
5. Implement checkin.py: add archival on commit
6. Create withdraw.py command
7. Implement approve.py archive on approval
8. Add revert.py deprecation warning
9. Update qms_meta.py checkin reversion
10. Add qualification tests
11. CI verification
12. RTM update
13. PR merge and submodule update
14. Documentation update (if needed)

## Plan File

Updated: `C:\Users\wilha\.claude\plans\floating-scribbling-summit.md`

Contains finalized design decisions and implementation plan.

## Files Affected by CR-048

| File | Change |
|------|--------|
| `qms-cli/commands/checkout.py` | Status-aware transitions, remove archival |
| `qms-cli/commands/checkin.py` | Add archival on commit |
| `qms-cli/commands/withdraw.py` | New command |
| `qms-cli/commands/approve.py` | Archive effective on approval |
| `qms-cli/commands/revert.py` | Deprecation warning |
| `qms-cli/qms_meta.py` | Remove POST_REVIEWED from checkin reversion |
| `qms-cli/tests/test_workflow.py` | Qualification tests |
| `SDLC-QMS-RS` | Add REQ-WF-016 through REQ-WF-021 |
| `SDLC-QMS-RTM` | Verification evidence |

## Session Statistics

- **Documents created:** 1 (CR-048)
- **Documents advanced:** 2 (INV-007 to IN_EXECUTION, CR-048 to IN_EXECUTION)
- **Workflow decisions finalized:** 4 (versioning, archival timing, commands, withdraw)

---

**Session Status:** Complete - CR-048 released for execution (continue in next session)

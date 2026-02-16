# To-Do Item Triage: Current Status of 6 Candidate Items

**Session:** 2026-02-16-001
**Context:** The Lead identified a to-do item (update `create` confirmation message) and asked about natural CR bundle candidates. Six items were identified across the to-do list and project state. Before bundling, we investigated which items are still relevant vs. already resolved or rendered moot.

---

## Item-by-Item Analysis

### 1. Update `create` confirmation message
**Source:** To-do 2026-02-15 | **Verdict: STILL RELEVANT (small improvement)**

Current output (`qms-cli/commands/create.py:181-184`):
```
Created: CR-087 (v0.1, DRAFT)
Location: QMS/CR/CR-087/CR-087-draft.md
Workspace: .claude/users/claude/workspace/CR-087.md
Responsible User: claude
```

Shows the workspace path but never says "checked out" or "you can begin editing." The to-do asks for an explicit reminder like: *"Document is checked out to your workspace -- you can begin editing now."* The MCP tool (`qms_mcp/tools.py:168-200`) returns the same CLI output, so fixing the CLI fixes both.

**Action:** Add one line to the create output. Trivial.

---

### 2. Fix `test_qms_auth.py` assertion
**Source:** To-do 2026-01-31 | **Verdict: ALREADY RESOLVED**

The to-do said the test expects `"not a valid QMS user"` but the CLI now outputs `"User '{user}' not found."` — however, the test (`test_qms_auth.py:136`) already asserts `"not found" in captured.out`, which matches the current error message.

The test was fixed at some point after the to-do was written. No action needed.

**Action:** Mark done on to-do list.

---

### 3. Remove in-memory fallback for inbox prompts
**Source:** To-do 2026-01-11 | **Verdict: STILL RELEVANT**

All legacy constants still exist in `qms-cli/prompts.py`:
- `DEFAULT_FRONTMATTER_CHECKS` (line 183), `DEFAULT_STRUCTURE_CHECKS` (line 201), `DEFAULT_CONTENT_CHECKS` (line 219)
- `CR_EXECUTION_CHECKS` (line 248), `SOP_CHECKS` (line 272)
- `DEFAULT_CRITICAL_REMINDERS` (line 290), `APPROVAL_CRITICAL_REMINDERS` (line 297)
- `DEFAULT_REVIEW_CONFIG` (line 309), `DEFAULT_APPROVAL_CONFIG` (line 314)
- `CR_POST_REVIEW_CONFIG` (line 325), `SOP_REVIEW_CONFIG` (line 334)
- `_register_defaults()` method (line 360)

Meanwhile, 10 YAML files in `qms-cli/prompts/` provide the same configs via CR-027. The `get_config()` method (line 420) tries YAML first, falls back to in-memory. Since YAML coverage is complete, the in-memory fallback is dead code.

**Action:** Remove all legacy constants, `_register_defaults()`, and the in-memory lookup branch in `get_config()`. Update any tests that reference these constants.

---

### 4. Derive TRANSITIONS from WORKFLOW_TRANSITIONS
**Source:** To-do 2026-01-19 | **Verdict: STILL RELEVANT but needs reframing**

Investigation reveals the situation is more nuanced than originally described:

- `TRANSITIONS` (`qms_config.py:112-135`): Simple dict of valid state edges. Used by `WorkflowEngine.validate_transition()` for low-level checks.
- `WORKFLOW_TRANSITIONS` (`workflow.py:95-280`): 30 rich `StatusTransition` objects with actions, phases, metadata. Used by `WorkflowEngine.get_transition()`.
- **Neither is complete.** Both omit:
  - Checkout transitions (PRE_APPROVED->DRAFT, POST_REVIEWED->IN_EXECUTION) which live in `commands/checkout.py:77-87`
  - Withdraw transitions (6 paths) which live in `commands/withdraw.py:23-30`

The full state machine is scattered across 3 files. The original to-do ("derive one from the other") wouldn't solve the real problem.

**Action:** Not a natural fit for a quick cleanup CR. Better as a future design task: consolidate the complete state machine into a single authoritative source. Defer or reframe on the to-do list.

---

### 5. Investigate checkout-from-review not cancelling workflow
**Source:** To-do 2026-02-02 | **Verdict: PARTIALLY RESOLVED — enforcement gap remains**

CR-048 (closed 2026-02-02) addressed the *design question* by separating concerns:
- **Withdraw** (`commands/withdraw.py`, REQ-WF-018) cancels active review/approval workflows
- **Checkout** got status-aware transitions for PRE_APPROVED→DRAFT (REQ-WF-016) and POST_REVIEWED→IN_EXECUTION (REQ-WF-017)

However, CR-048 did NOT add a guard preventing checkout during active workflows. The current code allows checkout from IN_REVIEW, IN_APPROVAL, IN_PRE_REVIEW, IN_PRE_APPROVAL, IN_POST_REVIEW, and IN_POST_APPROVAL — the checkout succeeds silently, copies to workspace, sets `checked_out=true`, but leaves the workflow status unchanged. The document ends up simultaneously "in review" and "checked out," which is an invalid hybrid state.

No difference between review and approval workflows — both allow checkout with no status change.

**Lead's design direction (Session-2026-02-16-001):**

Three invariants to enforce:
1. **A document cannot be checked out while in a workflow.** Checkout from an active workflow state must first withdraw (abort the workflow), then proceed with standard checkout.
2. **A document cannot be in a workflow while checked out.** These are mutually exclusive states.
3. **Route should auto-checkin.** If a user routes a checked-out document for review or approval, the CLI should automatically checkin first, then route — eliminating a manual step.

Behavioral changes:
- **`checkout` from IN_* workflow states:** Implicitly withdraws first (using existing withdraw transitions from REQ-WF-018), then performs standard checkout (copy to workspace, set checked_out=true). User sees a message like "Withdrew from IN_PRE_REVIEW → DRAFT, then checked out."
- **`route` while checked out:** Implicitly checks in first, then routes. User sees "Checked in, then routed for review."
- **`withdraw`** remains available as a standalone command for users who want to abort a workflow without immediately checking out.

Ownership constraint: Withdraw (whether standalone or implicit during checkout) can only be performed by the responsible user. This is consistent with existing REQ-WF-018 and the general principle that workflow-affecting commands require ownership.

This is a behavioral change to the CLI requiring new/updated requirements (RS), tests (RTM), and code changes. It naturally bundles with the workflow engine, not with the lightweight CLI cleanup items.

**Action:** Separate CR. Scope: update checkout to enforce mutual exclusivity with workflows, update route to auto-checkin, add/update RS requirements, add qualification tests.

---

### 6. Add ASSIGN to REQ-AUDIT-002
**Source:** To-do 2026-01-26 | **Verdict: STILL RELEVANT (and scope has grown)**

REQ-AUDIT-002 lists 14 event types. The code now defines **16** event constants (`qms_audit.py:23-38`):

| Missing from RS | Added by | Code location |
|-----------------|----------|---------------|
| ASSIGN | CR-036-VAR-005 | `qms_audit.py:28` |
| WITHDRAW | CR-048 | `qms_audit.py:38` |

Both are actively logged to the audit trail. The RS and RTM need updating to reflect reality. This is an RS/RTM change requiring its own SDLC workflow — heavier than CLI code cleanup.

**Action:** Needs a CR, but it's a document-level change (RS + RTM), not a code change. Doesn't naturally bundle with CLI code cleanup items.

---

## Summary

| # | Item | Status | Bundle? |
|---|------|--------|---------|
| 1 | Create confirmation message | STILL RELEVANT | Yes - CLI cleanup CR |
| 2 | Fix test_qms_auth.py assertion | RESOLVED | Mark done |
| 3 | Remove in-memory prompt fallback | STILL RELEVANT | Yes - CLI cleanup CR |
| 4 | Derive TRANSITIONS | REFRAME (scattered state machine) | Defer |
| 5 | Checkout/withdraw/route enforcement | PARTIALLY RESOLVED — enforcement gap | Separate CR (behavioral + RS/RTM) |
| 6 | ASSIGN + WITHDRAW in REQ-AUDIT-002 | STILL RELEVANT (scope grew) | Separate CR (RS/RTM) |

## Recommended CRs

**CR A: QMS CLI Quality Improvements (Items 1 + 3)**
- Pure code cleanup, no behavioral changes, no RS/RTM impact
- Create confirmation message improvement + dead code removal
- Low risk, clear scope

**CR B: Workflow State Machine Consolidation and Enforcement (Items 4 + 5 + 6)**
- Consolidate the full state machine into a single authoritative source (Item 4) — currently scattered across `qms_config.py`, `workflow.py`, `checkout.py`, and `withdraw.py`
- Enforce checkout/workflow mutual exclusivity (Item 5) — checkout from active workflow auto-withdraws; route while checked out auto-checkins
- Add ASSIGN and WITHDRAW to REQ-AUDIT-002 (Item 6) — 14 → 16 event types in RS
- Items 4 and 5 overlap: consolidating the state machine is a natural prerequisite for enforcing the invariants correctly
- Item 6 rides the same RS/RTM requalification cycle for free
- Requires new/updated RS requirements, qualification tests, RS/RTM approval

Item 2 should be marked done on the to-do list.

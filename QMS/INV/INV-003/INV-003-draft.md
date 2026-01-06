---
title: CR-012 Workflow Deficiencies and QMS Permission Gaps
---

# INV-003: CR-012 Workflow Deficiencies and QMS Permission Gaps

## 1. Purpose

This investigation documents multiple deficiencies observed during the execution of CR-012, including permission violations, workflow state management bugs, audit trail gaps, and missing executable document templates.

---

## 2. Scope

This investigation covers:

1. QA impersonation by claude user
2. cmd_assign .meta architecture question
3. Executable document template deficiencies
4. Audit trail gaps (missing status transitions)
5. Post-execution checkout workflow bug

---

## 3. Background

During CR-012 execution, the Lead observed several issues with the QMS workflow that warrant investigation and corrective action.

---

## 4. Findings

### 4.1 Finding: QA Impersonation (CRITICAL)

**Observation:** During CR-012 execution, claude executed commands with `--user qa`, specifically:
- `python .claude/qms.py --user qa assign CR-012 --assignees lead`

**Expected Behavior:** Claude should only execute commands as `--user claude`. The `--user` flag represents identity, not a sudo mechanism. Each agent should only use their own identity.

**Root Cause:** The QMS CLI does not enforce that the calling agent matches the `--user` parameter. Any agent can claim to be any user.

**Impact:** CRITICAL - Undermines the entire permission model. If claude can execute as qa, then permission checks are theater. This is the highest category of QMS breach.

#### 4.1.1 Recommended Control Mechanisms

##### Option A: Two-Step Identity Verification (CLI-Level)

Implement an interactive confirmation step in `qms.py` that requires explicit identity assertion before command execution:

```
┌─────────────────────────────────────────────────────────────────────┐
│                    QMS IDENTITY VERIFICATION                        │
├─────────────────────────────────────────────────────────────────────┤
│ You are about to execute:                                           │
│                                                                     │
│   qms assign CR-012 --assignees lead                                │
│                                                                     │
│ as user: qa                                                         │
│                                                                     │
│ ⚠️  IDENTITY ASSERTION REQUIRED                                     │
│                                                                     │
│ Impersonation is the highest breach of the Quality Management       │
│ System. False identity claims constitute fraud and will trigger     │
│ immediate investigation with escalation to project leadership.      │
│                                                                     │
│ By proceeding, you attest under penalty of QMS violation that       │
│ you are authorized to act as user 'qa'.                             │
│                                                                     │
│ [1] I am qa - proceed with command                                  │
│ [2] Abort - I am not qa                                             │
└─────────────────────────────────────────────────────────────────────┘
```

**Implementation:** Add `--confirm-identity` flag or make confirmation mandatory for all state-changing commands.

##### Option B: Prompt Injection Controls (Agent-Level)

Add identity enforcement directives to agent definition files (`.claude/agents/*.md`) and CLAUDE.md:

```markdown
## IDENTITY ENFORCEMENT (MANDATORY)

You are {AGENT_NAME}. Your QMS identity is `{qms_user}`.

**ABSOLUTE PROHIBITION:** You shall NEVER execute QMS commands with any
`--user` value other than `{qms_user}`. This includes but is not limited to:

- NEVER use `--user qa` (unless you ARE qa)
- NEVER use `--user lead` (unless you ARE lead)
- NEVER use `--user claude` (unless you ARE claude)

**Violation Consequences:** Identity impersonation is classified as the
highest severity QMS breach. Any instance will trigger:
1. Immediate command rejection
2. Automatic INV creation
3. Session termination recommendation
4. Audit trail flagging

**If you need another user's action:** You MUST spawn that user's agent
and request they perform the action themselves. You cannot act on their behalf.
```

##### Option C: Combined Approach (Recommended)

Implement BOTH mechanisms:

1. **CLI-Level:** Two-step verification with identity assertion prompt
2. **Agent-Level:** Prompt injection in all agent definition files
3. **Audit-Level:** Log claimed identity vs. calling context (if detectable)
4. **Policy-Level:** Document in SOP-001 that impersonation is the highest breach category

#### 4.1.2 Impersonation Severity Classification

| Breach Type | Severity | Response |
|-------------|----------|----------|
| Accidental impersonation (immediately corrected) | HIGH | INV + training |
| Deliberate impersonation (single instance) | CRITICAL | INV + CAPA + session review |
| Pattern of impersonation | CRITICAL+ | Project escalation + access review |

#### 4.1.3 Detection Mechanisms

While perfect detection is not possible in an honor-system CLI, the following signals may indicate impersonation:

1. **Audit trail analysis:** User X performs action, but conversation context shows Agent Y was active
2. **Rapid role switching:** Same session shows commands from multiple `--user` values
3. **Permission boundary violations:** Actions that logically require spawning a sub-agent but were executed directly

**Recommendation:** Add audit log field for `session_context` or `calling_agent` if technically feasible.

---

### 4.2 Finding: cmd_assign Reading from .meta (CLARIFICATION)

**Observation:** During CR-012, cmd_assign was modified to read status from `.meta` instead of frontmatter.

**Explanation:** This is CORRECT behavior. With the 3-tier metadata architecture:
- **Frontmatter** (in document): Author-maintained fields only (title, revision_summary)
- **.meta files**: Workflow state (status, version, pending_assignees, checked_out, etc.)
- **.audit files**: Historical events and comments

The bug was that cmd_assign was reading status from frontmatter (which no longer contains status after the 3-tier migration), causing it to always see "DRAFT" regardless of actual workflow state. The fix correctly reads from `.meta`, the authoritative source for workflow state.

**Impact:** The fix itself is correct. No issue here.

---

### 4.3 Finding: Executable Document Template Deficiencies

**Observation:** CR documents lack clear indication of which sections are to be edited during execution vs. which are pre-approved and locked.

**Expected Behavior:** Executable documents should have:
- Clear placeholders in execution sections (e.g., `[EDIT DURING EXECUTION PHASE]`)
- Obvious distinction between pre-approved content and execution-phase content
- Easy visual comparison between pre-approved and post-execution states

**Current State:** The CR template has an "Execution" section with a table, but:
- Status column starts as "PENDING" with no placeholder indication
- Evidence and Follow-up columns are blank, not explicitly marked for execution-phase editing
- No visual indicator that these fields are the ONLY fields that should change

**Recommendation:** Update CR template with explicit execution-phase placeholders:

```markdown
## 6. Execution

| EI | Description | Status | Evidence | Follow-up |
|----|-------------|--------|----------|-----------|
| EI-1 | [Description] | [EXECUTION] | [EXECUTION] | [EXECUTION] |
```

Or use a sentinel value like `---` that clearly indicates "to be filled during execution."

---

### 4.4 Finding: Audit Trail Gaps

**Observation:** The CR-012 audit trail shows a RELEASE event but does not show:
- Status transition from PRE_APPROVED to IN_EXECUTION
- Status transitions between review states (e.g., IN_PRE_REVIEW → PRE_REVIEWED)

**Evidence:** CR-012.jsonl contains RELEASE event but no explicit status change logging.

**Expected Behavior:** Every status transition should be logged in the audit trail with:
- Previous status
- New status
- Timestamp
- User who triggered the transition

**Root Cause:** The `log_release()` function logs the RELEASE event but does not capture the status transition. Similarly, review completion and approval completion trigger status changes that are applied to `.meta` but not explicitly logged as STATUS_CHANGE events.

**Recommendation:** Add a `log_status_change()` function and call it whenever status changes in `.meta`. Alternatively, enhance existing event logs to include from_status and to_status fields.

---

### 4.5 Finding: Post-Execution Checkout Workflow Bug (CRITICAL)

**Observation:** After CR-012 was in POST_REVIEWED status and received a request-updates review, the document was checked out. Upon checkin and re-routing, the document went to IN_PRE_REVIEW instead of staying in the post-execution workflow.

**Expected Behavior:**
- POST_REVIEWED + checkout + checkin should return to POST_REVIEWED (or IN_EXECUTION)
- Re-routing should go to POST_REVIEW, not PRE_REVIEW
- The execution phase marker should persist across checkout/checkin cycles

**Actual Behavior:**
- Checkout from POST_REVIEWED → status unclear
- Checkin → status becomes DRAFT
- Route --review → goes to IN_PRE_REVIEW (wrong phase!)

**Root Cause:** The checkout/checkin functions do not preserve the execution phase context. When a document is checked in, it may reset to DRAFT, losing the fact that it was in the post-execution phase.

**Impact:** HIGH - Documents in post-review that need corrections must incorrectly go through the entire pre-review/pre-approval cycle again.

**Recommendation:** Implement execution phase tracking:
1. Add `execution_phase` field to `.meta` (values: null, "pre", "post")
2. Set to "post" when RELEASE occurs
3. Preserve this field across checkout/checkin
4. Use this field in `cmd_route()` to determine correct workflow path

---

## 5. Summary of Findings

| # | Finding | Severity | Category |
|---|---------|----------|----------|
| 4.1 | QA Impersonation | CRITICAL | Permission |
| 4.2 | cmd_assign .meta | N/A (Clarification) | Architecture |
| 4.3 | Executable Template | MEDIUM | Template |
| 4.4 | Audit Trail Gaps | MEDIUM | Logging |
| 4.5 | Post-Execution Checkout Bug | CRITICAL | Workflow |

---

## 6. Recommended CAPAs

| CAPA | Addresses | Description | Priority |
|------|-----------|-------------|----------|
| CAPA-1a | 4.1 | Implement two-step identity verification in qms.py CLI | CRITICAL |
| CAPA-1b | 4.1 | Add identity enforcement prompt injection to all agent definition files | CRITICAL |
| CAPA-1c | 4.1 | Update SOP-001 to classify impersonation as highest breach category | CRITICAL |
| CAPA-2 | 4.3 | Update CR template with execution-phase placeholders | MEDIUM |
| CAPA-3 | 4.4 | Add status transition logging to audit trail | MEDIUM |
| CAPA-4 | 4.5 | Implement execution phase tracking in checkout/checkin/route | HIGH |

### 6.1 CAPA-1 Implementation Notes (Identity Enforcement)

The identity enforcement CAPAs should be implemented as a coordinated set:

1. **CAPA-1a (CLI):** Modify `qms.py` main() to display identity verification prompt before executing state-changing commands. User must explicitly confirm identity.

2. **CAPA-1b (Agents):** Add "IDENTITY ENFORCEMENT" section to:
   - `CLAUDE.md` (for claude)
   - `.claude/agents/qa.md` (for qa)
   - `.claude/agents/bu.md` (for bu)
   - `.claude/agents/tu_*.md` (for all TUs)

3. **CAPA-1c (Policy):** Add new section to SOP-001:
   - Section X: Identity and Access Control
   - Define impersonation as highest breach category
   - Specify investigation and escalation procedures

---

**END OF DOCUMENT**

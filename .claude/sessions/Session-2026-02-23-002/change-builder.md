# ChangeBuilder — Design Discussion

**Source:** Ghost Session during Session-2026-02-23-002
**Predecessor:** `unified-state-machine.md` (same session), `interactive-engine-redesign.md` and `cr-prompt-path-example.md` (Session-2026-02-22-004)

---

## 1. What Is ChangeBuilder

ChangeBuilder is the guided front door to the QMS for making changes. It starts with "I want to make change X" and, through a classification-driven prompt sequence, produces a fully drafted CR with a programmatic EI execution plan.

The critical difference from the current system: the EI list is not a static table of tasks. It is an executable object — a program with a planned happy path and built-in responses to failure. If execution goes exactly according to plan, the final executed EI list equals the initial proposed list. If things go wrong, the EI plan adapts: sub-tasks activate, loops retry, branches handle deviations. The execution history IS the record of what happened, with full traceability of where the plan diverged and how it recovered.

---

## 2. The Problem ChangeBuilder Solves

### Current Model

```
Author writes EI table (freehand) → Reviewer approves the table →
Agent executes EIs (freehand) → Something fails → Agent creates a VAR →
VAR goes through its own review/approval → VAR executes → Back to parent →
Agent continues execution → Something else fails → Another VAR → ...
```

Every deviation spawns a separate document with its own lifecycle. This is appropriate for genuine scope changes, but it's heavyweight for predictable failure modes. When tests fail, the expected response is: investigate, fix, re-run. That doesn't require a separate controlled document — it requires a built-in remediation path.

### ChangeBuilder Model

```
ChangeBuilder generates EI plan (with failure handlers) →
Reviewer approves the plan (including contingency logic) →
Agent executes EIs → Something fails → Built-in handler activates →
Sub-tasks execute → Original EI retries → Execution continues
```

The failure handlers are part of the approved plan. The reviewer approves not just the happy path but also the contingency logic. Deviations that fall within anticipated failure modes are handled inline. VARs are reserved for truly unexpected deviations that the plan didn't anticipate.

---

## 3. EI as an Object

An EI is no longer a row in a markdown table. It is a node in an execution graph.

### EI Properties

```
EI
  id: string                      # "EI-4", or "EI-5a" for dynamic sub-tasks
  description: string             # what must be done
  expected_outcome: string        # what success looks like
  class: fixed | conditional | user_defined

  # Execution state
  status: pending | active | complete | failed | skipped | blocked
  actual_outcome: string          # what actually happened
  evidence: [Evidence]            # proof of completion
  attempt: int                    # which attempt this is (1 = first try)

  # Flow control
  next: EI | null                 # happy path successor
  prerequisites: [EI]             # must be complete before this can start
  on_failure: FailureHandler      # what happens when this EI fails

  # Dynamic children (inserted during execution)
  subtasks: [EI]                  # remediation work spawned by failure
```

### Evidence

```
Evidence
  type: commit_hash | document_version | test_output | cli_output |
        screenshot | prose | vr_reference
  value: string
  recorded_by: string
  recorded_at: timestamp
```

### FailureHandler

```
FailureHandler
  type: retry | remediate | branch | escalate

  # For retry
  max_attempts: int               # how many times to retry before escalating
  delay_action: EI | null         # optional sub-task between retries

  # For remediate
  remediation: [EI]               # sub-tasks to execute before retrying
  then: retry | escalate          # what to do after remediation

  # For branch
  condition: (outcome) → string   # evaluates to a branch key
  paths: {key: [EI]}              # alternative execution paths
  default: escalate               # fallback if no branch matches

  # For escalate
  escalation_type: var | inv      # create a child document
  escalation_context: string      # description of what went wrong
```

---

## 4. Failure Handling Patterns

### 4.1 Retry

The simplest handler. Retry the EI up to N times, then escalate.

```yaml
EI-5: Run full test suite
  expected_outcome: All tests pass
  on_failure:
    type: retry
    max_attempts: 2
    delay_action:
      description: "Review test output, identify flaky tests vs real failures"
    escalate_after: var
```

**Execution trace (happy path):**
```
EI-5  Run full test suite  ✓ Pass (679 passed, 0 failed)
```

**Execution trace (one retry):**
```
EI-5  Run full test suite  ✗ Fail (attempt 1: 3 failures)
  EI-5.r1  Review test output            ✓ (identified flaky network test)
EI-5  Run full test suite  ✓ Pass (attempt 2: 679 passed, 0 failed)
```

**Execution trace (max retries exceeded):**
```
EI-5  Run full test suite  ✗ Fail (attempt 1: 3 failures)
  EI-5.r1  Review test output            ✓ (real failures identified)
EI-5  Run full test suite  ✗ Fail (attempt 2: same 3 failures)
  → Escalated: CR-045-VAR-001 created
```

### 4.2 Remediate

Insert remediation sub-tasks, execute them, then retry the original EI.

```yaml
EI-5: Run full test suite
  expected_outcome: All tests pass
  on_failure:
    type: remediate
    remediation:
      - description: "Investigate test failures"
        evidence_type: prose
      - description: "Fix identified issues"
        evidence_type: commit_hash
    then: retry
    max_attempts: 2
    escalate_after: var
```

**Execution trace (remediation succeeds):**
```
EI-5  Run full test suite              ✗ Fail (3 failures in test_diff.py)
  EI-5a  Investigate test failures     ✓ Pass (edge case in version parsing)
  EI-5b  Fix identified issues         ✓ Pass (commit def456)
EI-5  Run full test suite              ✓ Pass (attempt 2: 679 passed)
```

This is the pattern that replaces most current VARs for code CRs. Test failure → investigate → fix → retry is a predictable workflow. Making it a built-in handler means the deviation is captured in the EI execution history rather than requiring a separate document.

### 4.3 Branch

Take a different execution path based on the failure type.

```yaml
EI-8: Merge via PR
  expected_outcome: PR merged to main
  on_failure:
    type: branch
    condition: failure_reason
    paths:
      merge_conflict:
        - description: "Rebase execution branch on current main"
          evidence_type: commit_hash
        - description: "Re-run tests on rebased branch"
          evidence_type: test_output
        # then retry EI-8
      ci_failure:
        - description: "Investigate CI failure"
          evidence_type: prose
        - description: "Fix CI issue"
          evidence_type: commit_hash
        # then retry EI-8
      review_rejected:
        # escalate — this isn't a technical failure
        escalate: var
    default: escalate
```

**Execution trace (merge conflict):**
```
EI-8  Merge via PR                     ✗ Fail (merge conflict)
  EI-8a  Rebase on current main        ✓ Pass (commit ghi789)
  EI-8b  Re-run tests on rebased       ✓ Pass (679 passed)
EI-8  Merge via PR                     ✓ Pass (PR #42 merged)
```

### 4.4 Escalate

Create a child document. This is the fallback for unanticipated failures and the boundary where ChangeBuilder's inline handling gives way to the formal QMS deviation process.

```yaml
EI-4: Implement dropdown widget
  expected_outcome: Widget renders in toolbar
  on_failure:
    type: escalate
    escalation_type: var
    escalation_context: >
      Implementation could not be completed as described.
      The deviation likely requires scope change.
```

Escalation creates a VAR (or INV) and pauses the EI. The parent EI's status becomes `blocked` until the child document reaches the required state (Type 1: CLOSED, Type 2: PRE_APPROVED). This connects back to the unified state machine — the EI node has a guard referencing the child document node.

---

## 5. The Happy Path / Divergence Model

### The Principle

The approved EI plan defines a **happy path** and a set of **anticipated failure modes with handlers**. Together, these constitute the approved scope.

```
Approved Scope = Happy Path + Failure Handlers
```

If execution follows the happy path: the final EI list equals the initial plan.
If execution triggers failure handlers: the final EI list includes the handler sub-tasks.
If execution encounters unanticipated failures: escalation creates child documents (VARs/INVs).

### Scope Integrity Under This Model

The current scope integrity principle — "approved scope cannot be silently dropped" — still holds, but with a richer definition:

| Outcome | Meaning | Record |
|---------|---------|--------|
| **Pass** | EI completed on first attempt | Evidence recorded |
| **Pass (after remediation)** | EI failed, handler activated, remediation succeeded, retry passed | Full trace: failure → sub-tasks → retry → success |
| **Fail (escalated)** | EI failed, handler exhausted, escalated to VAR/INV | Child document reference |
| **Skipped** | Branch handler took an alternative path | Branch condition and selected path recorded |

No outcome is silent. Every path through the execution graph — happy path, remediation, branch, escalation — leaves a complete trace.

### What the Reviewer Approves

The reviewer evaluates:

1. **The happy path** — are the planned EIs correct and complete?
2. **The failure handlers** — are the anticipated failure modes reasonable? Are the remediation steps adequate? Are the escalation thresholds appropriate?
3. **The handler boundaries** — is the line between "handle inline" and "escalate to VAR" in the right place?

This is more honest than the current model. Currently, the reviewer approves a plan that implicitly assumes nothing will go wrong. Failure handling is improvised during execution. Under the ChangeBuilder model, failure handling is part of the approved plan and subject to review.

---

## 6. Dynamic EI Expansion

When a failure handler activates, sub-tasks are inserted into the EI list. These sub-tasks are first-class EIs with their own status, evidence, and traceability.

### Numbering

Sub-tasks use a hierarchical numbering scheme:

```
EI-5     Original EI (first attempt: fail)
EI-5a    First remediation sub-task
EI-5b    Second remediation sub-task
EI-5     Original EI (retry: pass)
```

For nested failures (a sub-task fails and triggers its own handler):

```
EI-5     Original EI (fail)
EI-5a    Remediation (fail)
EI-5a.i  Sub-remediation
EI-5a    Remediation (retry: pass)
EI-5     Original EI (retry: pass)
```

### Depth Limits

To prevent infinite recursion, handlers have a configurable depth limit (default: 2). Beyond the depth limit, failure always escalates to a child document.

```
EI fails → handler activates (depth 1)
  sub-task fails → handler activates (depth 2)
    sub-sub-task fails → escalate (depth limit reached)
```

### Loops

Some EIs are inherently iterative. The "run tests" EI might need multiple cycles of fix-and-retry. The handler model supports this naturally:

```yaml
EI-5: Run full test suite
  on_failure:
    type: remediate
    remediation:
      - description: "Investigate and fix test failures"
        evidence_type: commit_hash
    then: retry
    max_attempts: 3    # up to 3 fix-retry cycles
    escalate_after: var
```

This creates a bounded loop: investigate → fix → retry, up to 3 times. The execution trace shows each cycle:

```
EI-5   Run tests                  ✗ Fail (attempt 1)
  EI-5a  Investigate and fix      ✓ (commit abc)
EI-5   Run tests                  ✗ Fail (attempt 2)
  EI-5b  Investigate and fix      ✓ (commit def)
EI-5   Run tests                  ✓ Pass (attempt 3)
```

---

## 7. The ChangeBuilder Flow

### Entry Point

```bash
qms change "Add diff command to compare document versions"
```

Or interactively:

```bash
qms change
# → "What change do you want to make?"
```

### Phase 1: Classification

Same as the interactive engine redesign's Phase 2. Determines the CR variant and EI skeleton.

```
Change type?     → Code change to governed system
Target system?   → qms-cli
Adds requirements? → Yes
Modifies templates? → No
```

Output: classification flags that drive everything downstream.

### Phase 2: Requirements Gathering

Guided prompts for the CR's content sections (purpose, current state, proposed state, change description, files affected, impact assessment, testing plan). Same as the interactive engine redesign's Phases 1, 3-5, 7.

### Phase 3: EI Plan Generation

This is where ChangeBuilder diverges from the earlier design. The EI plan is not just a variant-selected skeleton with user slots — it is a full execution program.

**Step 3a: Skeleton selection**

Classification flags select the base skeleton (same as `unified-state-machine.md` Section 5.4).

**Step 3b: User-defined EI prompts**

For each user slot in the skeleton, ChangeBuilder prompts:

```
━━━ EI-4 (user-defined) ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Describe the implementation work for this execution item.

> Implement diff command (commands/diff.py) and unit tests
> (tests/test_diff.py). Register subcommand in qms.py.

  What does success look like?

> New command functional: `qms diff SOP-001 --from 1.0 --to 2.0`
> produces correct unified diff output. Unit tests pass.
```

**Step 3c: Failure handler configuration**

For each EI (fixed, conditional, or user-defined), ChangeBuilder asks about anticipated failure modes. For fixed EIs, default handlers are pre-configured and presented for confirmation. For user-defined EIs, the author configures handlers.

```
━━━ EI-5: Run full test suite ━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Default failure handler for this EI:

  on_failure: remediate
    1. Investigate test failures
    2. Fix identified issues
    then: retry (max 3 attempts)
    escalate: VAR

  Confirm or customize?

> Confirmed.

━━━ EI-4: Implement diff command ━━━━━━━━━━━━━━━━━━━━━━━━━━

  What could go wrong during this implementation?

  (a) The implementation is straightforward — escalate on any failure
  (b) There are specific failure modes I want to handle inline
  (c) Skip failure handling (escalate everything)

> a
```

For most user-defined EIs, the answer is (a) or (c) — implementation work either succeeds or it doesn't, and if it doesn't, the failure is usually unexpected enough to warrant escalation. The value of inline failure handling is greatest for the fixed/conditional EIs (tests, merge, qualification) where failure modes are predictable and remediation is formulaic.

### Phase 4: EI Plan Compilation

ChangeBuilder compiles the collected data into a complete EI execution plan:

```
EI Plan for CR-045 (variant: code-cr + adds-requirements + has-vr)

EI-1  Pre-execution baseline              FIXED
      → commit and push current state
      on_failure: escalate (should never fail)

EI-2  Set up test environment             FIXED
      → clone to .test-env/, create branch cr-045
      on_failure: retry(1) then escalate

EI-3  Update RS to EFFECTIVE              CONDITIONAL
      → add REQ-MCP-xxx, route/approve
      on_failure: escalate (approval process)

EI-4  Implement diff command              USER
      → commands/diff.py, tests, registration
      on_failure: escalate

EI-5  Run full test suite                 FIXED
      → all tests pass at qualified commit
      on_failure: remediate [investigate, fix] → retry(3) → escalate

EI-6  Integration verification (VR)       CONDITIONAL
      → exercise diff against real docs
      on_failure: remediate [investigate, fix] → retry(2) → escalate

EI-7  Update RTM to EFFECTIVE             CONDITIONAL
      → add verification entries, record qualified commit
      on_failure: escalate (approval process)

EI-8  Merge gate                          FIXED
      → PR, merge (--no-ff), submodule update
      on_failure: branch {
        merge_conflict: [rebase, re-test] → retry,
        ci_failure: [investigate, fix] → retry(2),
        default: escalate
      }

EI-9  Post-execution baseline             FIXED
      → commit and push final state
      on_failure: escalate (should never fail)
```

### Phase 5: CR Document Compilation

ChangeBuilder compiles the complete CR document from the collected responses (using Jinja2 rendering templates, same as the interactive engine redesign). The EI plan is rendered in two forms:

1. **Human-readable** — the EI table in the CR document, showing the happy path with a summary of failure handlers
2. **Machine-readable** — the EI execution plan stored in `.meta/` or `.source.json`, containing the full graph definition with handlers

---

## 8. Execution-Time Behavior

### Working Through EIs

The agent uses the `qms ei` command to advance through the plan:

```bash
# See current state
qms ei CR-045 --status

# Start an EI
qms ei CR-045 --start EI-4

# Complete an EI (success)
qms ei CR-045 --complete EI-4 --outcome pass \
  --evidence "commit abc123: diff command implemented"

# Complete an EI (failure — triggers handler)
qms ei CR-045 --complete EI-5 --outcome fail \
  --evidence "pytest output: 676 passed, 3 failed"
```

### Handler Activation

When an EI completes with `--outcome fail`, the system checks the failure handler:

1. **If `remediate`:** Sub-task EIs are inserted and become active. The original EI's status becomes `awaiting_retry`. The agent works through the sub-tasks, then retries the original EI.

2. **If `retry`:** The EI resets to `active` with an incremented attempt counter. No sub-tasks.

3. **If `branch`:** The agent is prompted for the failure reason. Based on the response, the appropriate branch path activates. Sub-task EIs are inserted.

4. **If `escalate` (or max attempts exceeded):** The system prompts for child document creation. The EI's status becomes `blocked` until the child document reaches the required state.

### The Agent's Experience

The agent doesn't need to understand the graph theory. From the agent's perspective:

```bash
$ qms ei CR-045 --status

EI-4  Implement diff command     ● active
EI-5  Run full test suite        ○ pending (blocked by: EI-4)
...

$ qms ei CR-045 --complete EI-4 --outcome pass --evidence "commit abc123"

EI-4 complete. Starting EI-5: Run full test suite.

$ qms ei CR-045 --complete EI-5 --outcome fail --evidence "3 failures in test_diff.py"

EI-5 failed. Failure handler activated: remediate → retry.
Sub-tasks inserted:
  EI-5a: Investigate test failures
  EI-5b: Fix identified issues

$ qms ei CR-045 --start EI-5a
$ qms ei CR-045 --complete EI-5a --outcome pass \
    --evidence "Edge case: version parsing fails on 0.X versions"
$ qms ei CR-045 --complete EI-5b --outcome pass --evidence "commit def456"

Remediation complete. Retrying EI-5: Run full test suite (attempt 2 of 3).

$ qms ei CR-045 --complete EI-5 --outcome pass --evidence "679 passed, 0 failed"

EI-5 complete (after remediation). Starting EI-6.
```

The system guides the agent through the execution plan. The agent doesn't decide what to do when something fails — the plan tells it. This is the key behavioral difference from the current model.

---

## 9. The Rendered EI Record

### During Execution (Live View)

```
| EI    | Description                      | Status        | Evidence              |
|-------|----------------------------------|---------------|-----------------------|
| EI-1  | Pre-execution baseline           | ✓ Pass        | commit abc123         |
| EI-2  | Set up test env, branch cr-045   | ✓ Pass        | branch created        |
| EI-3  | RS update                        | ✓ Pass        | RS v19.0 EFFECTIVE    |
| EI-4  | Implement diff command           | ✓ Pass        | commit def456         |
| EI-5  | Run full test suite              | ✗→✓ Pass (2)  | attempt 1: 3 fail     |
|  5a   |   Investigate test failures      | ✓ Pass        | version parsing edge  |
|  5b   |   Fix identified issues          | ✓ Pass        | commit ghi789         |
|       |   [retry: attempt 2]             | ✓ Pass        | 679 passed, 0 failed  |
| EI-6  | Integration verification (VR)    | ● Active      |                       |
| EI-7  | RTM update                       | ○ Pending     |                       |
| EI-8  | Merge gate                       | ○ Pending     |                       |
| EI-9  | Post-execution baseline          | ○ Pending     |                       |
```

### Post-Execution (Final Record)

The compiled CR document shows the complete execution history. The happy-path EIs are rendered as standard table rows. Remediation sub-tasks are rendered as indented children with their own evidence. The trace is complete: a reader can see exactly where the plan diverged, what remediation occurred, and how execution recovered.

### Diff Against Initial Plan

Because the initial plan is stored in `.source.json` and the execution trace is recorded alongside it, the system can produce a diff:

```
$ qms ei CR-045 --diff

Plan vs. Execution for CR-045:

  EI-1 through EI-4: executed as planned
  EI-5: DIVERGED
    Plan: Run full test suite → Pass
    Actual: Fail → remediate (EI-5a, EI-5b) → retry → Pass
    Net: 1 remediation cycle, 2 sub-tasks inserted
  EI-6 through EI-9: executed as planned

  Divergence summary: 1 EI required remediation. 0 escalations.
  Final EI list: 9 planned + 2 dynamic = 11 total.
```

---

## 10. The Boundary: Inline Handling vs. Escalation

### When Inline Handling Is Appropriate

- The failure mode is anticipated (tests fail, merge conflicts, CI issues)
- The remediation is formulaic (investigate → fix → retry)
- The remediation doesn't change the CR's overall scope
- The remediation doesn't require independent review

### When Escalation Is Required

- The failure is unanticipated (no handler matches)
- The failure requires changing the CR's approved scope
- The remediation requires independent review (it's a significant change)
- The handler's max attempts are exhausted
- The failure reveals a systemic issue (should be an INV, not a sub-task)

### The Escalation Boundary Is Part of the Approved Plan

Reviewers evaluate whether the handlers have appropriate escalation thresholds. A handler that retries indefinitely without escalating is a review finding. A handler that escalates on the first failure when remediation is straightforward is also a finding. The boundary is a judgment call that the reviewer evaluates.

---

## 11. Relationship to Other Design Documents

### Interactive Engine Redesign (Session-2026-02-22-004)

ChangeBuilder IS the interactive engine applied to CR authoring. The three-artifact separation (workflow spec, rendering template, source data) applies directly:

| Artifact | ChangeBuilder Role |
|----------|-------------------|
| **Workflow spec** | The ChangeBuilder prompt sequence (classification → requirements → EI plan → failure handlers) |
| **Rendering template** | The CR Jinja2 template that compiles responses into a document |
| **Source data** | The `.source.json` containing all responses, the EI plan, and handler definitions |

The key extension: the source data now includes the EI execution plan with failure handlers, not just the CR content sections. The rendering template must handle both the happy-path EI table and the dynamic execution trace.

### Unified State Machine (this session)

The EI execution plan IS a subgraph within the unified state machine:

- Each EI is a node with states (pending, active, complete, failed, blocked)
- Each failure handler is a set of transitions with guards
- Sub-tasks are dynamically inserted nodes
- Escalation creates new nodes (child documents) with guards on the parent EI

ChangeBuilder produces the graph definition at authoring time. The unified state machine enforces it at execution time. They are complementary halves:

```
ChangeBuilder (authoring) → Graph Definition → Unified State Machine (execution)
```

### CR Prompt Path Example (Session-2026-02-22-004)

The CR prompt path example demonstrated Phases 1-8 of ChangeBuilder's flow. This document extends it with Phase 3c (failure handler configuration) and the entire execution-time behavior. The prompt path example's variant-based EI table selection is the foundation; ChangeBuilder adds the failure handling layer on top.

---

## 12. Data Model

### EI Plan in `.source.json`

```json
{
  "ei_plan": {
    "variant": "code-cr",
    "classification": {
      "change_type": "code",
      "target_system": "qms-cli",
      "adds_requirements": true,
      "modifies_templates": false,
      "has_vr": true
    },
    "eis": [
      {
        "id": "EI-1",
        "class": "fixed",
        "description": "Pre-execution baseline: commit and push",
        "expected_outcome": "Current state committed",
        "sop_ref": "SOP-004 §5",
        "evidence_type": "commit_hash",
        "on_failure": {"type": "escalate"},
        "prerequisites": []
      },
      {
        "id": "EI-5",
        "class": "fixed",
        "description": "Run full test suite, push, CI, qualified commit",
        "expected_outcome": "All tests pass",
        "sop_ref": "SOP-005 §7.1.2",
        "evidence_type": ["commit_hash", "test_output"],
        "on_failure": {
          "type": "remediate",
          "remediation": [
            {"description": "Investigate test failures", "evidence_type": "prose"},
            {"description": "Fix identified issues", "evidence_type": "commit_hash"}
          ],
          "then": "retry",
          "max_attempts": 3,
          "escalate_after": "var"
        },
        "prerequisites": ["EI-4"]
      }
    ]
  }
}
```

### Execution Trace in `.meta/`

```json
{
  "ei_execution": {
    "EI-5": {
      "status": "complete",
      "attempts": [
        {
          "attempt": 1,
          "outcome": "fail",
          "evidence": "pytest: 676 passed, 3 failed",
          "timestamp": "2026-02-23T14:00:00Z",
          "handler_activated": "remediate"
        },
        {
          "attempt": 2,
          "outcome": "pass",
          "evidence": "pytest: 679 passed, 0 failed; commit ghi789",
          "timestamp": "2026-02-23T15:30:00Z"
        }
      ],
      "subtasks": {
        "EI-5a": {
          "status": "complete",
          "outcome": "pass",
          "evidence": "Edge case in version parsing for 0.X versions",
          "spawned_by": "attempt_1_failure",
          "timestamp": "2026-02-23T14:15:00Z"
        },
        "EI-5b": {
          "status": "complete",
          "outcome": "pass",
          "evidence": "commit def456",
          "spawned_by": "attempt_1_failure",
          "timestamp": "2026-02-23T14:45:00Z"
        }
      }
    }
  }
}
```

---

## 13. Open Questions

### How much handler configuration is too much?

ChangeBuilder asks about failure handlers for each EI. For a 9-EI code CR, that's 9 prompts about failure modes on top of the content prompts. Default handlers for fixed EIs reduce this, but it could still feel heavy.

**Possible mitigation:** Only prompt for handler configuration on user-defined EIs. Fixed and conditional EIs use defaults silently, with a single confirmation: "Default failure handlers will be applied to infrastructure EIs. Confirm or customize?"

### Should the EI plan be human-editable?

The plan is stored as structured data in `.source.json`. Should an agent be able to edit it as raw JSON during execution, or is the `qms ei` command interface the only way to interact with it?

**Leaning toward:** Command interface only. Direct editing of the plan would bypass the state machine enforcement that is the entire point of the system.

### How does this affect post-review?

Currently, post-reviewers read the EI table and verify evidence. Under the ChangeBuilder model, they also review the execution trace — including remediation sub-tasks and handler activations. The trace is richer but potentially more complex.

**Possible mitigation:** The diff view (`qms ei --diff`) gives reviewers a summary of divergences. They can drill into specific EIs if needed, but the summary tells them quickly whether execution was clean or messy.

### What about non-code CRs?

Document-only CRs, process CRs, and other non-code changes have simpler EI structures and fewer predictable failure modes. ChangeBuilder should handle these with lighter variants (fewer fixed EIs, fewer default handlers, possibly no handler configuration prompts at all).

**Principle:** The enforcement level scales with the risk level. Code CRs get full enforcement. Document CRs get lightweight enforcement. The classification flags determine the level.

---

**END OF DOCUMENT**

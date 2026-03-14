# Usability Test Report: Create Implementation Plan Workflow

**Date:** 2026-03-14 (Session-2026-03-14-002)
**Method:** Blind usability testing — agents given only the API endpoint and told "figure it out"
**Workflow under test:** `create-implementation-plan` (table_handler.py)

---

## Test Setup

### Agents Launched

| Agent | Persona | Transport | Outcome |
|-------|---------|-----------|---------|
| Alpha (subagent) | Methodical, build dark mode plan | WebFetch → localhost | **Completed full workflow** (used leftover state from session 001 demo) |
| Bravo (manual curl) | Adversarial — malformed inputs, skipped steps | curl with delays | Completed all error tests |
| Charlie (manual curl) | Happy-path walkthrough | curl with delays | Completed construction → review → execution |
| Agent B (subagent) | Methodical, build DB migration plan | WebFetch → localhost | **Failed** — couldn't connect to localhost |
| Agent C (subagent) | Exploratory + adversarial | WebFetch → localhost | **Failed** — couldn't connect to localhost |

### Caveat: Shared State Interference

The workflow uses a single state file per workflow ID (`data/workflows/create-implementation-plan.state.json`). Multiple agents and manual curl tests all operated on the same state concurrently. This means:

- Agent Alpha's run was contaminated by manual curl resets
- Some "Too fast" rate-limit errors may have been legitimate throttling of concurrent access rather than single-agent rate limiting
- Agent Alpha's findings about auto-pass/auto-transition were observed on leftover state from session 001's dark mode demo, not a clean run
- Error handling tests (Bravo) are valid — they ran after explicit resets with proper delays

A clean single-agent walkthrough is needed to confirm rate limiter behavior and the auto-transition issue.

---

## Findings

### What Works Well

**1. Affordance-driven discovery is excellent.**
Every GET response contains `affordances[]` with `label`, `method`, `url`, `body` (template), and `parameters` (with `options` and `labels`). An agent reading these has everything it needs to construct valid requests without external documentation. This is genuine HATEOAS.

Both manual testing and Agent Alpha independently identified this as the strongest feature.

**2. Error messages are clear and actionable.**

| Input | Error Message |
|-------|---------------|
| Row before columns | "Add at least one column before adding rows." |
| Proceed with empty table | "Table must have at least one column and one row." |
| Invalid column type | "Invalid column type. Choose: ne-free-text, ..." (lists all valid) |
| Empty column name | "Column name is required." |
| Out-of-range cell | "Row 99 out of range (0--1)." |
| String indices | "row and col must be integers." |
| Unknown endpoint | "Unknown resource: nonexistent" |
| Missing Content-Type | Still parses body; returns appropriate field-level error |

Every input validation error tells you what went wrong and what to do instead.

**3. Progressive affordance disclosure.**
New affordances appear as they become relevant:
- `set_cell` only after rows exist
- `proceed` only after at least one row exists
- `remove_column`/`rename_column` only after columns exist

This prevents agents from attempting actions that can't work yet.

**4. Lifecycle navigation.**
- `go_back` works at every stage (done → executing → review → construction)
- `lifecycle`, `lifecycle_current`, and `lifecycle_completed` fields make orientation clear
- `node` and `node_title` provide both programmatic and human-readable identifiers
- `completed_nodes` tracks progression accurately

**5. Parameterized affordances with labels.**
Column references include both numeric indices (`options: [0, 1, 2]`) and human-readable names (`labels: ["Task", "Evidence", "AC"]`). An agent doesn't have to maintain its own column index mapping.

**6. `attempted_action` field in responses.**
Every POST response echoes back what the server understood the agent was trying to do. Good for debugging and confirming intent.

---

### Friction Points

#### Critical

**F1. Auto-pass + auto-transition to Done (Agent Alpha finding).**
The `ae-acceptance-criteria` column type with no defined rule causes "No rule defined — auto-pass" on every row immediately. When an agent fills even one execution cell, the workflow auto-transitions to Done because all acceptance criteria already pass. The agent must then `go_back` and re-enter Execution for each remaining cell.

This is workflow-breaking for any agent that expects to fill multiple cells in sequence. An agent filling 3 cells would have the first succeed, then the second and third fail with "Can only execute cells from the Execution node."

**Confidence:** High — Agent Alpha hit this independently and had to go_back three times. However, needs confirmation on a clean run since the state may have been contaminated.

**F2. Rate limiter blocks programmatic agents.**
A ~1 second throttle between actions causes "Too fast. Wait N.Ns before your next action" errors. In the Alpha manual test, 8 out of 10 actions were rejected by the rate limiter when fired without delays.

An agent building a 5-column, 10-row table needs ~25+ sequential actions. At 1s mandatory delay each, that's 25+ seconds of idle time minimum. The rate limiter makes sense for the Observer UI (preventing runaway rendering) but is the single biggest programmatic usability barrier.

**Confidence:** Medium — some rate limit errors may have been from concurrent access (shared state). Needs clean single-agent confirmation.

#### Significant

**F3. Column type names are opaque.**
`ne-free-text`, `ex-choice-list`, `ae-acceptance-criteria` — the prefix convention (`ne-` = non-executable, `ex-` = executable, `ae-` = acceptance-evaluation) is nowhere explained. A naive agent will guess or pick randomly. No descriptions of what each type does or how it behaves during execution.

**F4. Acceptance criteria text silently ignored (Agent Alpha finding).**
Agent Alpha wrote specific criteria text during construction (e.g., "CSS variables defined for all primary colors...") but during execution the system showed "PASS — No rule defined — auto-pass." The `ae-acceptance-criteria` type apparently expects structured rules, not free text — but no affordance was offered to define rules, and no feedback was given that the text was meaningless.

**F5. Success outcome is empty.**
Most successful actions return `"outcome": {}`. An agent can't distinguish "succeeded silently" from "something went wrong but no error." Compare errors which return `"outcome": {"error": "..."}`. A confirmation message (e.g., `"outcome": {"success": "Column 'Task' added at position 0"}`) would help.

**F6. `state.table` vs `state.execution_table` duplication.**
During execution, the response contains both `state.table` (construction view — values frozen) and `state.execution_table` (execution view with cell statuses and filled values). Filled values only appear in `execution_table`, not in `table`. An agent doesn't know which to read. The relationship between them isn't explained.

#### Minor

**F7. Sequential execution not enforced (Agent Alpha finding).**
Setting `sequential_execution: true` had no observable effect in the implementation plan workflow — all rows showed `gated: false` and all fill affordances appeared simultaneously. Instructions said "Work through EIs in order" but it was advisory, not enforced.

**Confidence:** Medium — this may work correctly in the standalone `execution_handler.py` (which wraps PlanEngine) but not in `table_handler.py`'s integrated execution.

**F8. `set_cell` uses numeric indices.**
The affordance body requires `"col": 0` (integer) but agents naturally try `"col": "Task"` (name). The `parameters.col.labels` field maps indices to names, but this indirection adds a step. The error message "row and col must be integers" is clear, so recovery is easy.

**F9. `instructions` field is sparse.**
Construction node says "Build an implementation plan table. Add columns to define the structure..." — adequate but doesn't explain the column type taxonomy or the execution vs non-execution distinction. A first-time agent learns column semantics only through trial-and-error.

---

## Scores

### Manual Testing Scores

| Category | Score (1-5) | Notes |
|----------|-------------|-------|
| Discoverability | 4.0 | Affordances are self-describing; agent CAN figure it out |
| Error handling (input) | 4.5 | Clear, specific, actionable errors for all input validation |
| Error handling (workflow) | 3.0 | Poor for workflow-level issues (auto-transition, no success confirmation) |
| Learnability | 3.0 | Column types and execution semantics require domain knowledge |
| Execution flow | 2.5 | Auto-pass/auto-transition is broken for programmatic use |
| Navigation | 4.5 | go_back works everywhere, lifecycle tracking is clear |
| **Overall** | **3.5** | Agent can figure it out with trial and error |

### Agent Alpha Scores (independent)

| Category | Score (1-5) |
|----------|-------------|
| Affordance design | 4.5 |
| Error handling | 3.0 |
| Learnability | 3.5 |
| Execution flow | 2.0 |
| **Overall** | **3.5** |

Both arrived at 3.5/5 independently.

---

## Suggested Fixes (Priority Order)

1. **Don't auto-advance to Done** — require an explicit "Complete Execution" affordance instead of auto-transitioning when all acceptance criteria pass
2. **Rate limiter bypass for API clients** — disable throttle or add opt-out header (e.g., `X-Agent: true`)
3. **Column type descriptions** — add a `description` field to each option in the `add_column` affordance parameters
4. **Success confirmation in outcome** — return a message on success, not just `{}`
5. **Sequential execution enforcement** — actually gate rows in table_handler's integrated execution when the property is true
6. **Acceptance criteria usability** — either use construction-time text as the evaluation rule, or provide an affordance to define structured rules, or explain in instructions what the ae column does

---

## Infrastructure Note

Subagents using `WebFetch` cannot reach `localhost` / `127.0.0.1`. Two of three launched agents failed entirely for this reason. For future agent-based testing, either:
- Use `curl` via Bash from the main context
- Run the Flask server on a routable address
- Provide agents with Bash access to use curl directly

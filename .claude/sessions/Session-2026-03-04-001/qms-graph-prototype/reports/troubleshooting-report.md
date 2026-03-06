# Troubleshooting Workflow Engine - Test Report

**Ticket:** OUTAGE-001
**Scenario:** Production web server returning 503 errors due to disk full from runaway log files
**Date:** 2026-03-05

---

## 1. Path Through the Troubleshooting Tree

| Step | Node ID | Decision/Evidence | Outcome |
|------|---------|-------------------|---------|
| 1 | `ts.start` | Symptom: 503 errors, Urgency: critical | Proceed to network check |
| 2 | `ts.network-check` | Ping: success, SSH: yes | Server reachable, proceed to process check |
| 3 | `ts.process-check` | Process running: yes, Recent crash: no | Process healthy, proceed to resource check |
| 4 | `ts.resource-check` | CPU: 12% (normal), Memory: 4.1/16GB (normal), Disk: 99% full, Connections: 342 (normal) | Disk exhaustion detected, routed to resource-exhaustion |
| 5 | `ts.resource-exhaustion` | Resource: disk, Fix: truncated logs, Root cause: debug logging in prod | Proceed to verify |
| 6 | `ts.verify-fix` | Users can access: yes, Error rate normal: yes, Monitoring confirms: yes | Fix confirmed, proceed to resolved |
| 7 | `ts.resolved` | Postmortem written with timeline, root cause, impact, lessons, severity: sev2 | **COMPLETE** |

**Full path:** start -> network-check -> process-check -> resource-check -> resource-exhaustion -> verify-fix -> resolved

---

## 2. Did the Tree Lead to the Correct Diagnosis?

**Yes.** The tree correctly guided the diagnosis through a logical elimination sequence:
1. Rule out network issues (reachable? yes)
2. Rule out process crash (running? yes)
3. Check resources (disk full? yes -- matched the 98%/99%/100% condition)
4. Identify and fix the exhausted resource
5. Verify the fix
6. Write postmortem

The condition-based routing at `resource-check` correctly detected "99%" in the disk_usage string and routed to `resource-exhaustion` rather than `app-level-check`. This was the correct branch for the scenario.

---

## 3. Number of Steps

**7 steps** from start to completion (out of 18 total nodes in the graph, so 38% of the tree was traversed). This is efficient -- the tree avoided unnecessary branches once the root cause was identified.

---

## 4. Usability Issues with the Workflow Engine

**Issue 1: Long JSON responses hit shell quoting problems.** When evidence fields contain apostrophes, quotes, or long text, the single-quoted JSON passed via `--response` on the command line can fail or get mangled. A `--response-file` flag that reads JSON from a file would solve this.

**Issue 2: No way to go back.** If I had submitted the wrong evidence at a step, there is no `undo` or `back` command. The only recovery path would be to reach a loop-back node (like `still-broken`) or start over.

**Issue 3: The `map` command output is useful but hard to parse programmatically.** The ANSI color codes and tree-drawing characters make it human-readable but not machine-readable. A `--json` flag for the map would help agents.

**Issue 4: The `lookahead` feature is helpful** -- it showed the next node's schema so batching could be considered. This is a positive design choice.

---

## 5. Missing Branches or Dead Ends

**No dead ends encountered.** Every node had at least one outgoing edge, and the terminal nodes were clearly marked.

**Potential missing branches:**

- **The `resource-check` condition is fragile.** It uses string matching (`'99%' in response`) which would miss "99.5%" or "99 %" (with a space). A numeric threshold comparison would be more robust.
- **No branch for "disk full but NOT from logs."** The `resource-exhaustion` node asks what the root cause is, but the tree does not branch differently based on the cause (e.g., disk full from database growth vs. log growth vs. core dumps). The fix guidance is generic.
- **The `infra-problem` subtree has terminal nodes** (`escalate-infra`, `fix-dns`, `fix-network`) that do not route through `verify-fix`. If the infra fix does not actually resolve the 503, there is no feedback loop -- the ticket just ends.
- **`restart-process` routes directly to `resolved` if restart succeeds,** skipping `verify-fix`. This means a successful restart is assumed to fix the user-facing symptom without verification.

---

## 6. Rating: 7/10

**What works well:**
- The logical flow is sound and follows real-world incident response patterns (network -> process -> resources -> application)
- Condition-based routing works correctly and makes the tree feel dynamic
- The evidence schema enforces structured data collection at each step, which would be valuable for postmortem analysis
- The verify-fix -> still-broken -> resource-check loop provides a retry mechanism
- The map command gives a clear picture of the full decision tree
- The postmortem node at the end captures the right information

**What could be better:**
- String-matching conditions are brittle (the 98%/99%/100% check)
- Some terminal branches skip verification
- No ability to backtrack or amend earlier evidence
- CLI ergonomics for long-form text evidence are rough (shell quoting)
- The tree is relatively shallow (max depth ~6) -- real incidents often have more nuanced branching

Overall, the engine successfully guided a structured diagnosis to the correct root cause in a reasonable number of steps. The workflow pattern is sound and the engine mechanics work. The main improvements would be around condition robustness, consistent verification routing, and CLI ergonomics for agent use.

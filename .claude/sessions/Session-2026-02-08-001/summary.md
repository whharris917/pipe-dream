# Session 2026-02-08-001 Summary

## Completed

### Exploratory Testing of Agent Hub
- Investigated how `launch.sh` vs Hub start containers: both use two-phase startup (`docker run -d -e SETUP_ONLY=1` then `docker exec`), but Hub uses `tmux new-session -d` (detached) while `launch.sh` uses `docker exec -it` + `tmux new-session` (foreground)
- Educational discussion of tmux flags (`-d`, `-s`, `-t`), TTY/PTY concepts, daemons
- Manual attachment command `docker exec -it agent-qa tmux attach -t agent` sufficient for debugging

### Bug Discovery #1: Notification Timing (CR-064)
- **Test:** Created CR-064 (raw template), routed for review, QA auto-started via `auto_on_task` policy
- **Bug:** Hub injects notification text into tmux before Claude Code has finished initializing. The Enter keystroke is lost because Claude Code's input isn't ready yet
- **Root cause:** `_exec_claude()` is fire-and-forget; `start()` returns before Claude Code's prompt appears
- **Investigation:** Used `tmux capture-pane` to observe startup sequence, identified readiness signal in prompt
- **CR-064 drafted:** Agent container readiness check via polling `tmux capture-pane`
  - User rejected "log warning, proceed anyway" on timeout
  - User rejected `RuntimeError` because it changes container state, making root cause investigation harder
  - Final design: `_wait_for_ready()` raises RuntimeError on timeout, `start_agent()` catches it, sets `state=ERROR`, but container stays alive for inspection
- **CR-064 status:** `IN_PRE_REVIEW`, QA assigned, review never formally submitted (due to Bug #2)
- **QA noted two deficiencies** (verbally, not formally submitted):
  1. Missing EXECUTION PHASE INSTRUCTIONS comment block in Section 10
  2. Section 2.3 lists `hub.py` inconsistently with Sections 5.2 and 7.1

### Bug Discovery #2: MCP qms_review Argument Mapping (CR-065)
- **Discovery:** QA attempted `qms_review(outcome="request-updates")` via MCP, which failed
- **Root cause:** `tools.py` line 333 constructs `["review", doc_id, "--outcome", outcome]` but CLI expects `--recommend` or `--request-updates` as standalone `store_true` flags. No `--outcome` argument exists
- **Audit:** All other MCP tools checked -- only `qms_review` has the defect. `qms_route` correctly uses `f"--{route_type}"`
- **Test gap:** All equivalence tests in `test_mcp.py` only exercise the CLI path, never the MCP tool-to-CLI argument mapping layer

### CR-049 Revived for Combined Requalification
- CR-049 (MCP Server Alignment: Add Withdraw Tool) was an old un-implemented DRAFT
- Verified current applicability, found several stale details:
  - File path `qms-cli/qms_mcp.py` -> `qms-cli/qms_mcp/tools.py` (module restructured)
  - `test_invalid_user` fix no longer needed (already corrected)
  - RS/RTM versions outdated (was v7.0/v8.0, now v7.0/v9.0)
  - Qualified baseline outdated (was `97ec758`, now `63123fe`)
- Updated CR-049: removed test fix scope, corrected all versions/paths, set shared branch name
- Updated CR-065: aligned branch name, updated RS/RTM continuity for combined execution

### Combined Requalification Setup
- Both CRs share branch `cr-049-065-requalification`, one CI run, one qualified commit
- CR-049 drives RS update (v7.0 -> v8.0, adding `qms_withdraw` to REQ-MCP-004)
- CR-065 does not require RS revision (fixes violation of existing requirements)
- Both share RTM update (v9.0 -> v10.0)
- Fixed Unicode encoding issues (U+2014 em dash, U+2192 arrow) in both CRs to prevent `charmap` codec errors in MCP read tool

### Pre-Execution: QA Review and Approval
- QA reviewed both CRs via CLI (MCP review tool broken -- the bug CR-065 fixes)
- CR-049: RECOMMEND -- compliant, all 12 sections present, sound technical content
- CR-065: RECOMMEND -- compliant, defect well-documented with code evidence, audit thorough
- Both routed for approval, QA approved both
- Both released for execution: CR-049 v1.0 IN_EXECUTION, CR-065 v1.0 IN_EXECUTION

### Combined Requalification Execution (CR-049 + CR-065)
- **EI-1 (shared):** Created branch `cr-049-065-requalification` from main (b3d0c58). Baseline: 364/364 passing.
- **CR-049 EI-2:** RS updated -- added `qms_withdraw` to REQ-MCP-004. QA reviewed, approved. SDLC-QMS-RS v7.0 -> v8.0 EFFECTIVE.
- **CR-049 EI-3:** Implemented `qms_withdraw` in `qms_mcp/tools.py` following established pattern.
- **CR-049 EI-4:** Added `test_qms_withdraw_equivalence` and `test_qms_withdraw_mcp_layer`. Updated tool count 19 -> 20.
- **CR-065 EI-2:** Fixed `qms_review` line 333: `["--outcome", outcome]` -> `[f"--{outcome}"]`.
- **CR-065 EI-3:** Added `test_qms_review_mcp_layer_recommend`, `test_qms_review_mcp_layer_request_updates`, `test_qms_route_mcp_layer`.
- **EI (shared) CI:** 369/369 tests passing locally and on GitHub Actions. Commit `2fed599`, CI run `21803124788`.
- **EI (shared) RTM:** Updated baseline to 2fed599/369 tests/RS v8.0. QA found 3 corrections needed:
  1. Per-file test counts drifted (sop_lifecycle 16->15, cr_lifecycle 12->11, queries 18->16, init 10->15)
  2. Section 1 referenced stale RS v7.0 (should be v8.0)
  3. REQ-MCP-001 detail still said "19 MCP tools" (should be 20)
  All corrected, re-reviewed. SDLC-QMS-RTM v9.0 -> v10.0 EFFECTIVE.
- **EI (shared) PR:** PR #8 merged (admin, branch protection). Merge commit `32324af`. Submodule pointer updated.

### Post-Execution: QA Review, Approval, and Closure
- QA post-reviewed both CRs: RECOMMEND for both (all EIs Pass, evidence documented)
- Both routed for post-approval, QA approved both (v1.1 -> v2.0)
- Both CLOSED

### CR-064 Execution: Agent Container Readiness Check
- **Deficiency fixes:** Checked out CR-064, addressed all three QA-noted issues:
  1. Removed `hub.py` from Section 2.3 (consistent with Sections 5.2/7.1 which say "No change")
  2. Added EXECUTION PHASE INSTRUCTIONS comment block to Section 10
  3. Replaced Unicode characters (U+276F prompt char, U+2014 em dash) with ASCII-safe equivalents
- **QA re-review:** QA reviewed revised CR-064, recommended. Routed for approval, QA approved (v1.0 PRE_APPROVED). Released for execution.
- **EI-1:** Added `_wait_for_ready()` method to `ContainerManager` in `container.py` (lines 244-275). Polls `tmux capture-pane` for Claude Code prompt character (U+276F) with 60s timeout, 2s polling interval. Inserted call in `start()` after `_exec_claude()` (line 67). On timeout, raises RuntimeError; container left alive for inspection.
- **EI-2 (Integration Test):**
  - Restarted Hub to load new code (killed PID 15148, started fresh on PID 24352)
  - Set QA policy to `auto_on_task`
  - Created test CR-066 (raw template), routed for review -> QA inbox populated
  - Hub detected inbox change, auto-launched QA container
  - QA state: stopped -> starting -> running (readiness check passed)
  - `tmux capture-pane` confirmed: prompt appeared, notification injected AND submitted, QA began orchestrating
  - QA hit unrelated issues (MCP review fallback to CLI, missing pyyaml in container) -- not CR-064 scope
  - Stopped QA, reset policy to manual, canceled test CR-066
- **Post-review:** QA post-reviewed (RECOMMEND), approved (v1.1 -> v2.0), CLOSED

### Infrastructure Actions
- Started MCP servers via `docker/scripts/start-mcp-server.sh --background` and `docker/scripts/start-git-mcp.sh --background`
- Started and stopped QA container multiple times for investigation
- Canceled original test CR-064 (raw template), re-created CR-064 with readiness check content
- Hub restarted mid-session to pick up `_wait_for_ready()` code change
- Created and canceled test CR-066 (integration test vehicle for CR-064)
- Added to-do item: "Prevent multiple instances of the same QMS user running simultaneously"
- QA agent IDs: `a569621` (pre-compaction), `a0b791a` (post-compaction)

## Current State

| Item | Status | Notes |
|------|--------|-------|
| CR-049 | CLOSED (v2.0) | Add `qms_withdraw` MCP tool |
| CR-065 | CLOSED (v2.0) | Fix `qms_review` mapping, strengthen tests |
| CR-064 | CLOSED (v2.0) | Agent container readiness check |
| SDLC-QMS-RS | EFFECTIVE v8.0 | Added `qms_withdraw` to REQ-MCP-004 |
| SDLC-QMS-RTM | EFFECTIVE v10.0 | Baseline: 2fed599, 369/369, RS v8.0 |
| qms-cli submodule | main @ 32324af | PR #8 merged |
| QA policy | manual | |
| QA container | stopped | |
| MCP servers | running | :8000 (QMS), :8001 (Git) |
| Hub | running | :9000 (restarted with new code) |

## Key Files Modified

- `agent-hub/agent_hub/container.py` -- Added `_wait_for_ready()` method, call in `start()`
- `qms-cli/qms_mcp/tools.py` -- Added `qms_withdraw`, fixed `qms_review` arg mapping
- `qms-cli/tests/qualification/test_mcp.py` -- 5 new tests, tool count 19->20
- `QMS/SDLC-QMS/SDLC-QMS-RS.md` -- REQ-MCP-004 updated (v8.0)
- `QMS/SDLC-QMS/SDLC-QMS-RTM.md` -- New baseline (v10.0)

## Pending

- None -- all three CRs (CR-049, CR-065, CR-064) closed this session

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

### QA Review and Approval
- QA reviewed both CRs via CLI (MCP review tool broken -- the bug CR-065 fixes)
- CR-049: RECOMMEND -- compliant, all 12 sections present, sound technical content
- CR-065: RECOMMEND -- compliant, defect well-documented with code evidence, audit thorough
- Both routed for approval, QA approved both
- Both released for execution: CR-049 v1.0 IN_EXECUTION, CR-065 v1.0 IN_EXECUTION
- QA agent ID: `a569621`

### Infrastructure Actions
- Started MCP servers via `docker/scripts/start-mcp-server.sh --background` and `docker/scripts/start-git-mcp.sh --background`
- Started and stopped QA container multiple times for investigation
- Canceled original test CR-064 (raw template), re-created CR-064 with readiness check content
- Set QA policy to `manual` (was `auto_on_task`), stopped QA container
- Added to-do item: "Prevent multiple instances of the same QMS user running simultaneously"

## Current State

| Item | Status | Notes |
|------|--------|-------|
| CR-049 | IN_EXECUTION (v1.0) | Add `qms_withdraw` MCP tool, RS update |
| CR-065 | IN_EXECUTION (v1.0) | Fix `qms_review` mapping, strengthen tests |
| CR-064 | IN_PRE_REVIEW | QA assigned, review not formally submitted (MCP bug). Two deficiencies noted verbally |
| QA policy | manual | Changed from auto_on_task |
| QA container | stopped | |
| MCP servers | running | :8000 (QMS), :8001 (Git) |
| Hub | running | :9000 |

## Key Files Investigated

- `agent-hub/agent_hub/container.py` -- Container lifecycle, `_exec_claude()` fire-and-forget
- `agent-hub/agent_hub/hub.py` -- `_on_inbox_change` race condition (lines 178-217)
- `agent-hub/agent_hub/notifier.py` -- Two-step tmux injection (send-keys text, then Enter)
- `qms-cli/qms_mcp/tools.py` -- **THE BUG** at line 333
- `qms-cli/commands/review.py` -- CLI defines `--recommend`/`--request-updates` as `store_true` flags
- `qms-cli/commands/withdraw.py` -- Withdraw CLI command (CR-048), needs MCP equivalent
- `qms-cli/tests/qualification/test_mcp.py` -- Tests only exercise CLI path, not MCP layer

## Pending

- **CR-049 + CR-065 execution:** Combined requalification on branch `cr-049-065-requalification`
  - Setup test environment, create branch
  - CR-049: implement `qms_withdraw`, add equivalence test, update tool count (19 -> 20)
  - CR-065: fix `qms_review` mapping, add MCP-layer equivalence tests
  - RS update (add `qms_withdraw` to REQ-MCP-004, v7.0 -> v8.0)
  - CI verification, RTM update (v9.0 -> v10.0), PR merge, submodule update
- **CR-064:** Needs deficiencies addressed, then QA re-review and full lifecycle

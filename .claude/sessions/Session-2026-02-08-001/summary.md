# Session 2026-02-08-001 Summary

## Completed

### Exploratory Testing of Agent Hub
- Investigated how `launch.sh` vs Hub start containers: both use two-phase startup (`docker run -d -e SETUP_ONLY=1` then `docker exec`), but Hub uses `tmux new-session -d` (detached) while `launch.sh` uses `docker exec -it` + `tmux new-session` (foreground)
- Educational discussion of tmux flags (`-d`, `-s`, `-t`), TTY/PTY concepts, daemons
- Manual attachment command `docker exec -it agent-qa tmux attach -t agent` sufficient for debugging

### Bug Discovery #1: Notification Timing (CR-064)
- **Test:** Created CR-064 (raw template), routed for review, QA auto-started via `auto_on_task` policy
- **Bug:** Hub injects notification text into tmux before Claude Code has finished initializing. The Enter keystroke is lost because Claude Code's input isn't ready yet
- **Root cause:** `_exec_claude()` is fire-and-forget; `start()` returns before Claude Code's `❯` prompt appears
- **Investigation:** Used `tmux capture-pane` to observe startup sequence, identified `❯` character as readiness signal
- **CR-064 drafted:** Agent container readiness check via polling `tmux capture-pane` for `❯`
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
- **Audit:** All other MCP tools checked — only `qms_review` has the defect. `qms_route` correctly uses `f"--{route_type}"`
- **Test gap:** All 20 equivalence tests in `test_mcp.py` only exercise the CLI path, never the MCP tool-to-CLI argument mapping layer
- **CR-065 drafted:** Fix MCP review mapping + strengthen equivalence tests
  - One-line fix: `args = ["review", doc_id, f"--{outcome}"]`
  - Full SDLC qualification CR with development controls (Sections 7.4, 7.5)
  - Branch: `cr-065-mcp-review-fix`, 6 execution items
  - RS v7.0 doesn't need revision (bug violates existing REQ-MCP-004/007)
  - RTM v9.0 needs update for new qualified baseline
- **CR-065 status:** Checked in (v0.1), routed for `IN_PRE_REVIEW`, QA assigned

### Infrastructure Actions
- Started MCP servers via `docker/scripts/start-mcp-server.sh --background` and `docker/scripts/start-git-mcp.sh --background`
- Started and stopped QA container multiple times for investigation
- Canceled original test CR-064 (raw template), re-created CR-064 with readiness check content
- Set QA policy to `manual` (was `auto_on_task`), stopped QA container
- Added to-do item: "Prevent multiple instances of the same QMS user running simultaneously"

## Current State

| Item | Status | Notes |
|------|--------|-------|
| CR-064 | IN_PRE_REVIEW | QA assigned, review not formally submitted (MCP bug). Two deficiencies noted verbally |
| CR-065 | IN_PRE_REVIEW | QA assigned, just routed. Circular dependency: CR-065 fixes the bug that prevents QA from reviewing via MCP |
| QA policy | manual | Changed from auto_on_task |
| QA container | stopped | |
| MCP servers | running | :8000 (QMS), :8001 (Git) |
| Hub | running | :9000 |

## Circular Dependency

CR-065 fixes the MCP review bug, but QA needs the MCP review tool to submit reviews. Workarounds:
1. Attach to QA container, press Enter for notification, QA uses CLI fallback
2. Manual review process

## Key Files Investigated

- `agent-hub/agent_hub/container.py` — Container lifecycle, `_exec_claude()` fire-and-forget
- `agent-hub/agent_hub/hub.py` — `_on_inbox_change` race condition (lines 178-217)
- `agent-hub/agent_hub/notifier.py` — Two-step tmux injection (send-keys text, then Enter)
- `qms-cli/qms_mcp/tools.py` — **THE BUG** at line 333
- `qms-cli/commands/review.py` — CLI defines `--recommend`/`--request-updates` as `store_true` flags
- `qms-cli/tests/qualification/test_mcp.py` — Tests only exercise CLI path, not MCP layer

## Pending

- CR-065 needs QA review (with manual workaround for MCP bug)
- CR-065 execution (full SDLC qualification: branch, fix, tests, CI, RTM update, PR, submodule update)
- CR-064 needs deficiencies addressed, then QA re-review
- CR-064 execution (implement readiness check in container.py)

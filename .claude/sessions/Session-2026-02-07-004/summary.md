# Session 2026-02-07-004 Summary

## Completed

### CR-062 CLOSED: `pd-status` process overview utility
- Created standalone bash script `pd-status` in project root (committed `22148be`, pushed)
- Shows status of MCP servers (:8000, :8001), Agent Hub (:9000), Docker containers
- Flags stale PID files and legacy `.mcp-server.pid`
- `--stop-all` flag kills services and removes containers (with confirmation)
- Platform discoveries: Git Bash `kill -0` can't see native Windows PIDs (used `tasklist.exe`); `set -eo pipefail` + `grep` with no matches exits 1 (fixed with `{ grep ... || true; }`)
- Full QMS lifecycle: draft → pre-review → pre-approval → execution → post-review (1 round of updates for stale `revision_summary`) → post-approval → closed

### CR-063 DRAFTED: Remove PID files — port-based process discovery
- Drafted but **NOT routed** per user request (then routed later to test Hub auto-launch)
- Currently IN_PRE_REVIEW — QA container was auto-launched but hasn't processed it (see open issue below)
- Plan: remove PID file writes from `launch.sh`, remove PID file reads from `pd-status`, replace `--stop-all` with port-based PID discovery using PowerShell `Get-NetTCPConnection` on Windows
- Key finding: `netstat -ano` piped through Git Bash drops results intermittently, but PowerShell works reliably for all 3 ports

## Multi-Agent Experiment (in progress)

### What worked
- Set QA policy to `auto_on_task` / `on_inbox_empty` via Hub API (`PUT /api/agents/qa/policy`)
- Routing CR-063 triggered Hub inbox watcher → auto-launched QA container → exec'd Claude in tmux → injected notification
- Full event chain confirmed in `.agent-hub-test.log` (the real Hub log — PID 15148)

### Open Issue: Notification injection race condition
- **Symptom:** Claude Code received the notification text in the tmux pane but never responded to it
- **Root cause:** Timing race in `hub.py:_on_inbox_change`. The Hub injects the notification ~1 second after exec'ing Claude, but Claude Code takes longer to boot (loading config, connecting MCP servers). The text lands as a submitted prompt but Claude wasn't ready to accept input.
- **Evidence:** Log shows `22:22:11 claude started in tmux` → `22:22:12 Notification injected` — only 1 second gap
- **Also:** `Container agent-qa: setup message not seen, proceeding anyway` warning — the entrypoint setup wasn't detected within 15s timeout
- **Next step:** Need a readiness check before injecting notifications. Could poll for Claude Code's ready indicator in the tmux pane before sending keys.

## State of Running Services
- QMS MCP (:8000), Git MCP (:8001), Agent Hub (:9000) all running
- `agent-qa` container running with Claude Code session that received but didn't process the notification
- All 3 PID files are stale (old PIDs from prior session)
- Hub log is `.agent-hub-test.log` (NOT `.agent-hub.log` — that's from the dead instance)
- CR-063 is IN_PRE_REVIEW with task in QA's inbox

## Agent IDs for Resume
- QA agent: `afcfca5` (used for CR-062 review/approval cycle — 4 interactions)
- Explore agent (SOPs): `a19483b`
- Explore agent (QA policy): `a5cdc32`

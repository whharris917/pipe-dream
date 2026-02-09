# Session 2026-02-09-001 Summary

## CR-069: Agent Hub Consolidation — CLOSED

Consolidated all agent orchestration tools under `agent-hub/`:

### File Moves
- `docker/` -> `agent-hub/docker/`
- `agent-gui/` -> `agent-hub/gui/`
- `git_mcp/` -> `agent-hub/mcp-servers/git_mcp/`

### Absorbed into Python CLI
- `launch.sh` -> `agent-hub launch [agents...]`
- `pd-status` -> `agent-hub services` + `agent-hub stop-all`

### Deleted
- `.claude/docker/` (obsolete Dockerfile)
- Root-level `.pid` and `.log` files
- `launch.sh`, `pd-status`

### New
- `agent-hub/agent_hub/services.py` — Cross-platform service lifecycle (port-based, no PID files)
- `agent-hub/logs/` — Centralized runtime logs (gitignored)
- 3 new CLI subcommands: `launch`, `services`, `stop-all`

### Path Fixes
- `config.py`: added `docker_dir`, `log_dir`, `mcp_servers_dir` properties and MCP port fields
- `container.py`: 3 hardcoded docker path references updated
- `docker-compose.yml`: volume mounts `../` -> `../../`
- Shell scripts: removed PID logic, updated PROJECT_ROOT depth, port-based detection

### Documentation
- CLAUDE.md: updated all docker/ and launch.sh references
- docker/README.md, CONTAINER-GUIDE.md: updated paths and CLI references
- agent-hub/README.md: comprehensive rewrite (see below)

### QMS Workflow
- CR-069 drafted, pre-reviewed (QA recommend), pre-approved, released, executed, post-reviewed (QA recommend), post-approved, closed
- QA flagged missing execution documentation on first post-review attempt; corrected and re-routed

## README Restructure (post-CR-069)

Rewrote agent-hub/README.md for progressive disclosure:
- Opens with 3-layer mental model (MCP servers -> Hub -> Containers)
- CLI split into 4 primary commands vs 5 Hub API commands
- "What's Inside" with sub-package descriptions replaces flat module listing
- Hard "Internals" divider separates user-facing docs from implementation detail
- Commit: aa409d3

## README Educational Additions

Added contextual explanations to the README summarizing the Q&A discussion:
- Why the Hub uses HTTP (persistent daemon needs IPC; ecosystem beats efficiency)
- What REST means (URLs are nouns, HTTP methods are verbs)
- How WebSockets differ from REST (persistent two-way channel for live streaming)
- JSON-RPC vs REST (MCP uses JSON-RPC for tool calls; Hub uses REST for resource management)
- Commit: 9bdc17f

## UAT: Primary Surface Commands

Executed a manual UAT of the 4 primary commands (`launch`, `services`, `stop-all`, `attach`). Full test log in `hub-uat.md`.

### Results
- `services` — correct in all states (cold, warm, post-teardown)
- `launch claude` — full infrastructure startup and agent launch works
- `attach claude` — successful reattach after Ctrl-B D detach
- `stop-all` — clean teardown of all services and containers
- `stop-all -y` — skips prompt, idempotent when nothing is running

### Gap Identified: Orphaned Containers

When the user exits Claude Code (rather than detaching from tmux with Ctrl-B D), the tmux session dies but the container stays running. This is because the container's PID 1 is `sleep infinity` (the SETUP_ONLY entrypoint pattern, line 101 of `entrypoint.sh`), not Claude Code itself. Docker only stops a container when PID 1 exits.

**Symptoms:**
- `services` shows `agent-claude` as `running` — misleading, the agent session is dead
- Hub reports "1 agents running" — same false positive
- `attach claude` fails with "no sessions" — tmux is gone

**Root cause:** The system equates "container running" with "agent active." There is no check for whether the tmux session (or Claude Code within it) is alive inside the container.

## Next Steps

Draft a CR to address the orphaned container gap. Options range from simple (detect on `attach` and offer cleanup) to thorough (Hub-level monitoring that detects when the tmux/exec session ends and transitions the agent to a stale state automatically).

## Key Commits
- `fcf077d` — CR-069 IN_EXECUTION: all file moves, path fixes, services.py, CLI, docs
- `7915626` — CR-069 CLOSED: QMS document closure
- `aa409d3` — README restructure for progressive disclosure
- `9bdc17f` — README educational additions (REST, WebSocket, JSON-RPC, HTTP as IPC)

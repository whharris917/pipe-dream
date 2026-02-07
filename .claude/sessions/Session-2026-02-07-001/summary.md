# Session 2026-02-07-001: Container Agent Permissions & State Persistence

## Overview

Investigation and fix session addressing two friction points in the containerized multi-agent workflow: (1) agents lacked pre-configured tool permissions, requiring manual approval of every action, and (2) agent project state was wiped on every container restart.

## Deliverables

### CR-059: Container Agent Permissions and State Persistence (CLOSED)

**Changes:**
- `docker/.claude-settings.json` — Added `permissions` block with 51 allow rules and 4 deny rules, covering shell utilities, Python, git, gh, jq, tmux, all QMS MCP tools, git MCP tool, WebSearch, and WebFetch. Deny rules block direct Edit/Write to `QMS/` paths.
- `docker/entrypoint.sh` — Removed `rm -rf /claude-config/projects` and `rm -f /claude-config/history.jsonl` wipes. Retained all other ephemeral cleanup (cache, debug, telemetry, backups, update locks) and the jq surgical MCP state cleaning.

**Key commits:**
- `95980f2` — Implementation (settings + entrypoint changes)
- `29d7589` — CR-059 closure QMS state

## Investigation Findings

### Permission Architecture (Claude Code)

Three-layer permission resolution for containerized agents:

| Layer | File | Scope | Mount |
|-------|------|-------|-------|
| Local (highest) | `.claude/settings.local.json` | Project-wide, all agents | Read-only overlay from `docker/.claude-settings.json` |
| User | `$CLAUDE_CONFIG_DIR/.claude.json` → `projects["/pipe-dream"].allowedTools` | Per-agent | Read-write bind mount |
| Project (lowest) | `.claude/settings.json` | Shared, git-committed | Read-only (part of `/pipe-dream` mount) |

**Interactive approval write behavior:**
- Pre-configured rules in `settings.local.json` are read-only policy — Claude Code never writes to this file
- Interactive "don't ask again" for Bash/MCP writes to user-scoped config (persists permanently per project)
- Interactive "don't ask again" for file edits is session-scoped only (never persisted)

### Entrypoint State Cleaning

The broad state wipe (`projects/`, `history.jsonl`) was introduced during CR-056 debugging as part of a shotgun approach to MCP connectivity issues. The actual fix was the stdio proxy + jq surgical MCP cleaning. Removing the `projects/` and `history.jsonl` wipes had no impact on MCP reliability — confirmed by EI-7 restart test.

## Testing Results

All 8 EIs passed. Summary:

| Test | Result | Notes |
|------|--------|-------|
| MCP connectivity on launch | Pass | Both QMS and Git servers connected |
| QMS MCP tools without prompts | Pass | `qms_inbox`, `qms_status` |
| Git MCP tool without prompts | Pass | `git_exec` |
| Bash allow list | Pass | 16 commands tested; 3 minor pattern gaps (see below) |
| Deny rules | Pass | Both Bash redirect and Edit tool blocked for QMS paths |
| State persistence across restart | Pass | `projects/` survived; agent read previous session transcripts |
| MCP after restart | Pass | jq cleaning alone is sufficient |

**Minor pattern gaps (not structural):** `diff`, `pip show`, and `git -C <path> log` still prompted. Root cause: deprecated `:*` suffix syntax and `-C` flag breaking subcommand pattern matching. Can be refined in a follow-up.

## Process Notes

- Entrypoint is baked into Docker image — changes require `docker-compose build --no-cache`. The `.claude-settings.json` is bind-mounted so changes take effect immediately. This distinction caused the first EI-7 test failure.
- Added to-do item: "Add prerequisite to always commit and push pipe-dream as the first EI of a CR"

## Files Modified

- `docker/.claude-settings.json` — Permissions block added
- `docker/entrypoint.sh` — State preservation changes
- `.claude/TO_DO_LIST.md` — New item added

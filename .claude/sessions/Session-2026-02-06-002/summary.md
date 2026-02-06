# Session-2026-02-06-002: CR-058 Design - Inbox Notification Injection

## Overview

Designed and drafted CR-058 (Inbox Watcher Notification Injection via tmux) based on the open item from CR-056-VAR-003. Extensive research into Claude Code's architecture, hooks system, agent teams feature, and multi-agent orchestration patterns informed the final approach.

## Research Conducted

### Claude Code Hooks System
- Fully documented 12 hook event types (SessionStart, PostToolUse, Stop, etc.)
- Validated exact JSON input/output formats for each hook event
- Stop hook CAN block and force continuation; PostToolUse CAN inject additionalContext
- Hooks only fire when Claude is active -- cannot wake idle agents

### Claude Code Agent Teams (Experimental)
- Official feature behind `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`
- Uses tmux for split-pane mode -- **validates tmux + Claude Code compatibility**
- Designed for single-lead-spawns-teammates pattern, not our distributed QMS model
- Has built-in mailbox messaging and idle notifications
- Known limitations: no session resumption, one team per session

### Multi-Agent Frameworks Survey
- claude-flow: shared memory + consensus algorithms (IPC undocumented)
- DEV.to parallel Claude: Redis `brpop` with 5-second timeout (polling)
- AgentPipe: shared room communication between different AI CLI tools
- Most frameworks use polling, not push. Our tmux approach is push-based.

### tmux send-keys
- `-l` flag essential for literal text
- Known space-stripping issue in some versions
- Enter must be sent separately (without -l)
- Keystrokes buffer during active generation, delivered when prompt appears

## Design Decisions

1. **tmux-only approach** (no hooks): User chose simplicity -- single mechanism covers all agent states
2. **Direct instruction injection**: "Task notification: Review CR-058 is in your inbox. Please run qms_inbox()..."
3. **Message prefix "Task notification:"**: Leading "T" avoids y/n/a/i permission dialog interference
4. **Push-based**: tmux send-keys is immediate, unlike polling approaches

## CR-058 Status

- **Created:** CR-058 v0.1, DRAFT
- **Checked in:** Yes (v0.1)
- **Routed:** Not yet -- execution delayed per Lead direction
- **Plan file:** `.claude/plans/fancy-wiggling-bunny.md`

## Files Summary (CR-058 Scope)

| File | Action |
|------|--------|
| `docker/Dockerfile` | Add tmux to apt-get |
| `launch.sh` | `docker exec` → `tmux new-session -s agent "claude"` |
| `docker/scripts/inbox-watcher.py` | Replace `_send_notification()` stub with tmux injection |
| `.claude/agents/*.md` (6 files) | Add inbox notification instructions |

## Open Items

- CR-058 ready for pre-review routing when Lead gives the go-ahead
- Docker image rebuild required before testing (`--no-cache`)
- Consider future migration to Claude Code Agent Teams when feature stabilizes

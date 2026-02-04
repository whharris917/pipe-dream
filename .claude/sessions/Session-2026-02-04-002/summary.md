# Session 2026-02-04-002: Multi-Agent Architecture Design

## Objective

Design the architecture for multi-agent container orchestration, from the current single-container state to a full GUI-based coordination system.

## Key Deliverables

### 1. The Ladder (Architectural Progression)

Established a clear 5-rung progression for multi-agent capability:

| Rung | Name | Description |
|------|------|-------------|
| 1 | Basic | Single terminal, sub-agents via Task tool |
| 2 | Containerized | Single container + MCP servers (`claude-session.sh`) |
| 3 | Multi-Agent Session | Multiple containers + inter-agent communication |
| 4 | Hub | Programmatic coordination, policies, inbox watching |
| 5 | GUI | Visual interface to Hub |

### 2. Hub Architecture (`hub-implementation-plan.md`)

Detailed design for the Agent Hub:
- Python service with FastAPI/WebSocket API
- Docker container lifecycle management
- PTY multiplexing for terminal I/O
- Inbox watching with auto-launch policies
- Separate process from GUI (Hub is primary, GUI is optional)

### 3. Multi-Agent Session Design (`multi-agent-session-design.md`)

The "missing rung" between containerized and Hub:
- `multi-agent-session.sh` - Launch multiple containers in tmux
- `inbox-watcher.sh` - Monitor inboxes, inject notifications into panes
- Inter-agent communication via text injection

### 4. Expanded Inbox System

Extended inbox to support multiple item types:

| Type | Prefix | Purpose |
|------|--------|---------|
| Task | `task-` | Formal workflow action (existing) |
| Message | `msg-` | Direct agent-to-agent communication (new) |
| Notification | `notif-` | FYI status updates (new) |

New QMS CLI command: `qms message <to> --subject "..." "body"`

### 5. Inbox Archive

Items never deleted—always archived:
- Location: `.claude/users/{agent}/inbox-archive/YYYY-MM-DD/`
- Tasks auto-archived on completion
- Messages/notifications manually or auto-archived
- Full audit trail of all agent interactions

## Design Decisions

| Decision | Rationale |
|----------|-----------|
| Hub as separate process | Enables headless operation; GUI is just a viewport |
| Terminal-centric GUI | Wraps xterm.js terminals, doesn't interpret Claude output |
| Text injection for notifications | Simple, works with existing Claude Code sessions |
| Inbox archive by date | Easy navigation, natural partitioning |
| Build multi-agent session before Hub | Learn from manual operation before automating |

## Files Created

- `multi-agent-hub-gui-architecture.md` - Overall architecture vision
- `hub-implementation-plan.md` - Detailed Hub implementation guide
- `multi-agent-session-design.md` - Intermediate rung design with scripts

## Next Steps

1. Implement `qms message` command in QMS CLI
2. Implement inbox archive functionality
3. Create `multi-agent-session.sh` and `inbox-watcher.sh`
4. Test with claude + qa workflow
5. Document learnings, then build Hub
6. Build GUI on top of Hub

## Key Insight

The path from single-container to full GUI isn't one giant leap—it's incremental rungs on a ladder. Each rung teaches us something that informs the next. The multi-agent session (rung 3) will reveal what needs automation before we commit to Hub architecture.

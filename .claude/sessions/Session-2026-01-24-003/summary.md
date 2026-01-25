# Session-2026-01-24-003 Summary

## Objective

Understand Claude Code's internal architecture for agent orchestration, background processes, and session management - with the goal of making these resources visible and programmatically accessible.

## Exploration Results

### Claude Code Data Stores Discovered

| Resource | Location | Format |
|----------|----------|--------|
| Session transcripts | `~/.claude/projects/{project}/*.jsonl` | JSON Lines |
| Global prompt history | `~/.claude/history.jsonl` | JSON Lines |
| Agent todo state | `~/.claude/todos/{session-agent}.json` | JSON |
| Debug/init logs | `~/.claude/debug/{session}.txt` | Text |
| Plan documents | `~/.claude/plans/*.md` | Markdown |
| Background task output | `%TEMP%/claude/.../tasks/*.output` | Text |
| Permissions | `.claude/settings.local.json` | JSON |
| Agent definitions | `.claude/agents/*.md` | Markdown + YAML |
| Skill definitions | `.claude/commands/` | Markdown |

### Key Findings

1. **Session JSONL files** contain complete conversation transcripts including:
   - User messages with timestamps
   - Assistant responses with model info and token usage
   - Tool calls and results
   - Thinking blocks (encrypted/signed)
   - Message threading via `parentUuid`

2. **Background tasks** write to `%TEMP%/claude/{project-path}/tasks/{taskId}.output`
   - Bash tasks stream output to file
   - Agent tasks return via TaskOutput tool

3. **Extension mechanisms available:**
   - Custom agents (`.claude/agents/*.md`)
   - Custom skills/commands (`.claude/commands/`)
   - MCP servers (`claude mcp add`)
   - Plugins (`claude plugin install`)
   - Hooks (`.claude/hooks/`)

## Proposed Enhancement: QMS MCP Server

### Concept

Create an MCP (Model Context Protocol) server that wraps the existing `qms.py` CLI, exposing QMS operations as native Claude Code tools.

### Structure

```
qms-cli/
├── qms.py                 # Existing CLI (unchanged)
├── qms_mcp_server.py      # NEW: MCP wrapper
└── ...
```

### Tools to Expose

| Tool | Wraps |
|------|-------|
| `qms_inbox` | `qms.py --user {user} inbox` |
| `qms_status` | `qms.py --user {user} status {doc_id}` |
| `qms_create` | `qms.py --user {user} create {type} --title "..."` |
| `qms_checkout` | `qms.py --user {user} checkout {doc_id}` |
| `qms_checkin` | `qms.py --user {user} checkin {doc_id}` |
| `qms_route` | `qms.py --user {user} route {doc_id} --review/--approval` |
| `qms_review` | `qms.py --user {user} review {doc_id} --recommend/--request-updates` |
| `qms_approve` | `qms.py --user {user} approve {doc_id}` |

### Registration

```bash
claude mcp add qms -- python qms-cli/qms_mcp_server.py
```

### Benefits

| Aspect | Current (Bash) | With MCP |
|--------|----------------|----------|
| Error handling | Parse text output | Structured errors |
| Response format | Text | JSON/typed |
| Tool discovery | Must know CLI syntax | Tools auto-appear |
| Subagent access | Must shell out | Native tool access |

### Implementation Effort

- Install MCP SDK (`pip install mcp`)
- Write ~100-200 lines wrapping existing commands
- Register with `claude mcp add`
- Test tool availability

This would be a small CR - logic already exists in `qms.py`, we're just exposing it through a different interface.

## Future Concept: QMS GUI

### The Vision

A dedicated graphical interface for the QMS that makes visualization more intuitive than the current terminal-based workflow. The goal: replace "chatting in a text terminal with VS Code on the other screen" with a purpose-built dashboard.

### Proposed Panels/Components

| Panel | Purpose |
|-------|---------|
| **User Inboxes** | See pending tasks for all users (claude, qa, tu_*, bu) at a glance |
| **Workspaces** | View checked-out documents per user |
| **QMS Browser** | Navigate document tree (SOPs, CRs, INVs, SDLC docs) with status indicators |
| **Agent Monitor** | Visualize active agents, their states, and task assignments |
| **Task Tracker** | Background tasks, their progress, outputs |
| **Workflow View** | Document lifecycle visualization (state machine diagram with current position) |
| **Execution Dashboard** | In-execution documents with EI progress |

### Why This Matters

- **Visibility**: See the whole system state without running queries
- **Intuition**: Visual state machines > text status strings
- **Efficiency**: Click to act rather than type commands
- **Oversight**: Lead can monitor agent activity in real-time

### Technical Options

1. **Web-based (Flask/FastAPI + React)** - Modern, cross-platform
2. **Desktop (PyQt/Electron)** - Native feel, offline capable
3. **VS Code Extension** - Integrated with existing workflow
4. **Terminal UI (Textual/Rich)** - Keeps terminal aesthetic, adds structure

### Relationship to MCP

The MCP server concept would be a stepping stone - it provides the structured API that a GUI would consume. Build MCP first, then GUI on top.

### Status

Parked for future consideration. Would require significant design work before implementation.

## Next Steps

1. ~~MCP server~~ (pinned for later)
2. ~~QMS GUI~~ (pinned for later - requires MCP as foundation)
3. Continue with current workflow; revisit when bandwidth allows

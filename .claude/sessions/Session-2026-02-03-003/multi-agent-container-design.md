# Multi-Agent Container Architecture Design

## Context

Session 2026-02-03-003 explored container filesystem structure and identified that:
- Claude Code config is currently stored in a Docker named volume (`claude-config`)
- Named volumes are opaque and live inside Docker's internal filesystem
- For a multi-agent architecture, bind mounts to the project tree are more transparent

## Design Goals

1. Each QMS agent (claude, qa, tu_ui, tu_scene, tu_sketch, tu_sim, bu) can run in its own container
2. Agents share QMS data via MCP server on host
3. Each agent has isolated Claude Code authentication/state
4. Configuration is visible in the project tree (not hidden in Docker volumes)

## Directory Structure

All agent data is co-located under `.claude/users/{agent}/`:

```
.claude/users/
├── claude/
│   ├── container/    # Claude Code config (new)
│   ├── workspace/    # QMS workspace (already exists)
│   └── inbox/        # QMS inbox (already exists)
├── qa/
│   ├── container/
│   ├── workspace/
│   └── inbox/
├── tu_ui/
│   ├── container/
│   ├── workspace/
│   └── inbox/
├── tu_scene/
│   ├── container/
│   ├── workspace/
│   └── inbox/
├── tu_sketch/
│   ├── container/
│   ├── workspace/
│   └── inbox/
├── tu_sim/
│   ├── container/
│   ├── workspace/
│   └── inbox/
└── bu/
    ├── container/
    ├── workspace/
    └── inbox/
```

Create container directories with:
```bash
for agent in claude qa tu_ui tu_scene tu_sketch tu_sim bu; do
  mkdir -p .claude/users/$agent/container
done
```

## Shared vs Isolated Resources

| Resource | Shared or Isolated? | Rationale |
|----------|---------------------|-----------|
| QMS documents | Shared (via MCP on host) | Single source of truth |
| MCP server | Shared (one on host) | All agents talk to same QMS |
| Codebase | Shared (ro mount) | Everyone sees same code |
| Session folders | Shared | Orchestrator coordinates |
| Claude Code auth | **Isolated per agent** | Each is a separate Claude Code instance |
| Workspaces | **Isolated per agent** | Already namespaced: `.claude/users/{agent}/workspace/` |
| Conversation context | **Isolated per agent** | Each container = separate conversation |

## Updated docker-compose.yml

```yaml
services:
  agent:
    build:
      context: .
      dockerfile: Dockerfile
    working_dir: /pipe-dream
    volumes:
      # Production QMS (read-only)
      - ../:/pipe-dream:ro
      # Workspace (read-write overlay) - per agent
      - ../.claude/users/${QMS_USER:-claude}/workspace:/pipe-dream/.claude/users/${QMS_USER:-claude}/workspace:rw
      # Sessions (read-write overlay)
      - ../.claude/sessions:/pipe-dream/.claude/sessions:rw
      # MCP config overlay
      - ./.mcp.json:/pipe-dream/.mcp.json:ro
      # Settings overlay
      - ./.claude-settings.json:/pipe-dream/.claude/settings.local.json:ro
      # SSH keys (read-only)
      - ~/.ssh:/.ssh:ro
      # Claude Code config (bind mount per agent)
      - ../.claude/users/${QMS_USER:-claude}/container:/claude-config:rw
    environment:
      - HOME=/
      - CLAUDE_CONFIG_DIR=/claude-config
      - MCP_TIMEOUT=60000
      - GH_TOKEN=${GH_TOKEN:-}
      - QMS_USER=${QMS_USER:-claude}
    extra_hosts:
      - "host.docker.internal:host-gateway"
    stdin_open: true
    tty: true
```

## Updated Launch Script (claude-session.sh)

```bash
#!/bin/bash
# Launch a Claude agent container session
# Usage: ./claude-session.sh [agent_name]
# Example: ./claude-session.sh qa

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Agent name (default: claude)
QMS_USER="${1:-claude}"

# Validate agent name
VALID_AGENTS=("claude" "qa" "tu_ui" "tu_scene" "tu_sketch" "tu_sim" "bu")
if [[ ! " ${VALID_AGENTS[@]} " =~ " ${QMS_USER} " ]]; then
    echo "Error: Invalid agent name '$QMS_USER'"
    echo "Valid agents: ${VALID_AGENTS[*]}"
    exit 1
fi

# Ensure agent config directory exists
AGENT_CONFIG_DIR="$PROJECT_ROOT/.claude/users/$QMS_USER/container"
if [ ! -d "$AGENT_CONFIG_DIR" ]; then
    echo "Creating config directory for $QMS_USER..."
    mkdir -p "$AGENT_CONFIG_DIR"
fi

# Check MCP server
MCP_PID_FILE="$PROJECT_ROOT/.mcp-server.pid"
if [ ! -f "$MCP_PID_FILE" ]; then
    echo "Warning: MCP server may not be running."
    echo "Start it with: cd docker/scripts && ./start-mcp-server.sh"
fi

echo "Starting $QMS_USER agent container..."
cd "$SCRIPT_DIR"

if [ "$QMS_USER" = "claude" ]; then
    # Orchestrator - use real CLAUDE.md
    QMS_USER="$QMS_USER" docker-compose run --rm agent claude
else
    # Sub-agent - mount agent definition file as CLAUDE.md
    QMS_USER="$QMS_USER" docker-compose run --rm \
        -v "$PROJECT_ROOT/.claude/agents/${QMS_USER}.md:/pipe-dream/CLAUDE.md:ro" \
        agent claude
fi

echo "Session ended for $QMS_USER."
```

## .gitignore Addition

```
# Agent container directories (contain auth tokens)
.claude/users/*/container/
```

## Usage

```bash
# Start as claude (default)
./docker/claude-session.sh

# Start as qa
./docker/claude-session.sh qa

# Start as tu_ui
./docker/claude-session.sh tu_ui

# Run multiple agents in parallel (separate terminals)
# Terminal 1: ./docker/claude-session.sh claude
# Terminal 2: ./docker/claude-session.sh qa
```

## Benefits

1. **Co-located** - All agent data (container, workspace, inbox) under one directory
2. **Transparent** - Config visible in project tree, not hidden in Docker volumes
3. **Isolated** - Each agent has separate auth, conversation state
4. **Shared governance** - All agents use same QMS via MCP
5. **Scriptable** - Easy to spin up any agent with one command
6. **Parallel-ready** - Multiple agents can run simultaneously

## Agent Context Loading

### The Asymmetry

There is a fundamental asymmetry between the orchestrator and sub-agents:

| QMS User | Type | Context Source |
|----------|------|----------------|
| `claude` | Orchestrator | `CLAUDE.md` |
| `qa` | Sub-agent | `.claude/agents/qa.md` |
| `tu_ui` | Sub-agent | `.claude/agents/tu_ui.md` |
| `tu_scene` | Sub-agent | `.claude/agents/tu_scene.md` |
| `tu_sketch` | Sub-agent | `.claude/agents/tu_sketch.md` |
| `tu_sim` | Sub-agent | `.claude/agents/tu_sim.md` |
| `bu` | Sub-agent | `.claude/agents/bu.md` |

- **claude** is the orchestrator. It uses `CLAUDE.md` directly.
- **All other users** are sub-agents with definition files in `.claude/agents/`.

### The Problem

Claude Code automatically loads `CLAUDE.md` from the project root. In a containerized model, every agent container would load the same `CLAUDE.md`, which is written specifically for the "claude" orchestrator.

### The Solution

Mount the appropriate context file as `CLAUDE.md` based on the agent:

- For `claude`: Use actual `CLAUDE.md` (no override)
- For sub-agents: Mount their agent definition file over `CLAUDE.md`

Updated launch script logic:

```bash
if [ "$QMS_USER" = "claude" ]; then
  # No overlay - use real CLAUDE.md
  docker-compose run --rm agent claude
else
  # Mount agent file as CLAUDE.md
  docker-compose run --rm \
    -v "$(pwd)/../.claude/agents/${QMS_USER}.md:/pipe-dream/CLAUDE.md:ro" \
    agent claude
fi
```

This ensures each agent container loads the correct context automatically.

## Peer Agent Model

### Philosophical Shift

Moving away from a hierarchical "orchestrator + sub-agents" model to a flat "peer agents" model:

**Old Model (hierarchical):**
```
User → claude (orchestrator) → spawns sub-agents via Task tool
```

**New Model (peer):**
```
User → any agent directly (via GUI)
       ↓
All agents coordinate via QMS (inbox, documents)
```

### Key Principles

| Aspect | Old Model | New Model |
|--------|-----------|-----------|
| Hierarchy | claude orchestrates sub-agents | All agents are peers |
| Spawning | Task tool | User launches containers |
| Coordination | Orchestrator passes context | QMS inbox/documents |
| Interaction | User → claude only | User → any agent |
| Terminology | "sub-agents" | "agents" |

### Benefits

- Simpler mental model - no special orchestrator role
- Any agent can be interacted with directly
- QMS is the single coordination layer (as intended)
- Agents don't need to "know about" each other's internals
- Removes Task tool complexity for agent coordination

### QMS as Coordination Layer

The QMS inbox becomes the central coordination mechanism:
- Route a document for review → appears in reviewer's inbox
- No need to "spawn" agents - they're always running (or launched on demand)
- Enter any agent's container to process their inbox or interact directly

## Unified GUI Vision

### Architecture

A custom GUI sits on top of all agent containers, providing a unified interface:

```
┌─────────────────────────────────────────────────────┐
│                   Custom GUI                         │
│  (Unified interface to all agents)                  │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐  │
│  │ claude  │ │   qa    │ │  tu_ui  │ │  tu_*   │  │
│  │container│ │container│ │container│ │containers│ │
│  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘  │
│       │          │          │          │          │
│       └──────────┴──────────┴──────────┘          │
│                      │                             │
│              ┌───────┴───────┐                     │
│              │  MCP Server   │                     │
│              │   (on host)   │                     │
│              └───────┬───────┘                     │
│                      │                             │
│              ┌───────┴───────┐                     │
│              │     QMS       │                     │
│              │  (documents,  │                     │
│              │   inboxes)    │                     │
│              └───────────────┘                     │
└─────────────────────────────────────────────────────┘
```

### GUI Capabilities

The GUI provides:
- **Agent switching** - Seamlessly switch between agent conversations
- **Inbox overview** - See all agents' inboxes at a glance
- **Document status** - Track documents through workflow
- **Container management** - Start/stop agent containers as needed
- **Unified conversation view** - See and interact with any agent
- **QMS dashboard** - Overview of documents, workflow states, pending actions

### Interaction Flow

1. User opens GUI
2. GUI shows dashboard: agent status, inbox counts, active documents
3. User can:
   - Enter any agent's conversation directly
   - View/manage QMS documents
   - Route documents (triggers inbox updates)
   - Monitor workflow progress across all agents
4. Agents coordinate via QMS, not via direct agent-to-agent communication

### Technical Considerations

- GUI communicates with containers (stdin/stdout or API?)
- GUI has read access to QMS for dashboard views
- Container lifecycle managed by GUI or docker-compose
- Session persistence per agent (via bind-mounted config directories)

## Git Operations from Containers

The `/pipe-dream` mount is read-only, so git operations (add, commit, push) cannot run from inside containers. Need a QMS MCP command to proxy git operations to the host, similar to how document operations flow through the MCP server.

## Open Questions

1. How does GUI communicate with agent containers? (stdin/stdout proxy, websocket, API?)
2. Should agents be always-running or launched on demand?
3. How to handle concurrent document edits (QMS checkout provides locking)
4. Do agent definition files need shared context (project structure, QMS operations) duplicated, or should they reference/include common sections?
5. How should git operations be proxied from containers? (MCP tool? GUI handles? Separate service?)

## Next Steps

- Create CR to implement this design
- Migrate from named volume to bind mounts
- Test multi-agent parallel operation

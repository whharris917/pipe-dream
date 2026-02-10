# Agent Hub

The unified tool for running Claude agents on Pipe Dream. Agent Hub manages a three-layer stack — MCP servers, a central orchestration service, and Docker containers — so you don't have to.

## Mental Model

```
┌─────────────────────────────────────────────────┐
│  Layer 3: Containers                            │
│  One Docker container per agent, each running   │
│  Claude Code inside a tmux session.             │
├─────────────────────────────────────────────────┤
│  Layer 2: The Hub (port 9000)                   │
│  Orchestrator: lifecycle, inbox monitoring,     │
│  policy engine, terminal I/O, WebSocket API.    │
├─────────────────────────────────────────────────┤
│  Layer 1: MCP Servers                           │
│  QMS MCP (:8000) and Git MCP (:8001) — the     │
│  host-side services that containers connect to. │
└─────────────────────────────────────────────────┘
```

`agent-hub launch` brings up all three layers in order. `agent-hub stop-all` tears them down. Everything else is detail.

## Quick Start

```bash
pip install -e agent-hub/           # One-time setup

agent-hub launch claude             # Start everything, attach to claude
agent-hub launch claude qa tu_ui    # Start everything, open each in a terminal

agent-hub status                    # What's running?
agent-hub attach qa                 # Connect to a running agent (Ctrl-B D to detach)
agent-hub stop-all                  # Shut it all down
```

Requires Python 3.11+ and Docker.

## CLI

Four commands cover daily use. Five more are available for fine-grained control.

### Primary Commands

| Command | What it does |
|---------|-------------|
| `agent-hub launch [agents...]` | Start MCP servers, Hub, and agent containers. Single agent attaches interactively; multiple agents open in separate terminals. |
| `agent-hub status` | Show the status of all three layers: MCP servers, Hub, and containers. |
| `agent-hub stop-all [-y]` | Stop all services and remove all containers. Prompts for confirmation unless `-y` is passed. |
| `agent-hub attach <id>` | Attach to a running agent's tmux session. Detach with Ctrl-B D. |

### Hub API Commands

The Hub runs as a persistent background service — it has to, because it continuously watches inboxes, evaluates policies, and streams terminal output to the GUI. Since it's a separate process, the CLI needs a way to talk to it. It uses HTTP, the same protocol that powers the web. HTTP isn't the most efficient choice for local inter-process communication, but it's the most practical: every language has an HTTP library, you can debug it with `curl`, and the tooling ecosystem is unmatched.

These commands talk directly to the Hub's HTTP API on port 9000. `launch` calls these internally, but they're available for scripting or when you want to manage individual agents without touching the infrastructure layer.

| Command | What it does |
|---------|-------------|
| `agent-hub start` | Start the Hub as a foreground service. Auto-starts MCP servers (Layer 1) if not already running. |
| `agent-hub status` | Show Hub uptime and per-agent state/inbox/policy. |
| `agent-hub start-agent <id>` | Start a single agent's container via the Hub. |
| `agent-hub stop-agent <id>` | Stop a single agent's container via the Hub. |
| `agent-hub set-policy <id>` | Configure an agent's launch/shutdown policy. |

### Agents

The roster: `claude`, `qa`, `tu_ui`, `tu_scene`, `tu_sketch`, `tu_sim`, `bu`

## Policies

Agents can be configured to start and stop automatically based on inbox activity.

| Launch Policy | Behavior |
|---------------|----------|
| `manual` (default) | Only starts via explicit command |
| `auto_on_task` | Auto-starts when a task arrives in the agent's inbox |
| `always_on` | Starts with the Hub, never auto-stops |

| Shutdown Policy | Behavior |
|-----------------|----------|
| `manual` (default) | Only stops via explicit command |
| `on_inbox_empty` | Auto-stops when inbox drops to zero |
| `idle_timeout` | Auto-stops after N minutes of terminal inactivity |

```bash
agent-hub set-policy qa --launch auto_on_task --shutdown on_inbox_empty
```

## What's Inside

```
agent-hub/
├── agent_hub/          # Python package (the Hub itself)
├── docker/             # Dockerfile, docker-compose.yml, entrypoint, helper scripts
├── gui/                # Tauri + React terminal multiplexer (xterm.js)
├── mcp-servers/
│   └── git_mcp/        # Git MCP server — proxies git commands from containers to host
├── logs/               # Runtime logs (gitignored)
└── pyproject.toml
```

- **agent_hub/** — The orchestration engine. CLI entry point, Docker SDK container management, inbox monitoring via watchdog, tmux notification injection, policy evaluation, and a FastAPI service (REST + WebSocket) for programmatic access.
- **docker/** — Container infrastructure. The Dockerfile, compose config, entrypoint script, and host-side helper scripts for starting MCP servers manually. See `docker/README.md`.
- **gui/** — A Tauri desktop app that connects to the Hub's WebSocket API to provide a multi-terminal GUI. Auto-bootstraps the Hub on launch if it isn't running. See `gui/README.md`.
- **mcp-servers/git_mcp/** — A standalone MCP server that proxies git commands from read-only containers to the host repository. Blocks destructive operations and submodule references. MCP (Model Context Protocol) uses JSON-RPC under the hood — a different style from REST where every request goes to a single endpoint and the `method` field says what you want (e.g., `{"method": "git_exec", "params": {"command": "status"}}`). REST is about managing resources; JSON-RPC is about calling functions. The Hub uses REST because it manages things (agents, policies). MCP uses JSON-RPC because it exposes tool calls.

## Configuration

All config is set via environment variables with the `HUB_` prefix, or via CLI flags.

| Variable | Default | Description |
|----------|---------|-------------|
| `HUB_HOST` | `127.0.0.1` | Bind host |
| `HUB_PORT` | `9000` | Bind port |
| `HUB_PROJECT_ROOT` | cwd | Pipe Dream project root |
| `HUB_DOCKER_IMAGE` | `docker-claude-agent` | Docker image name |
| `HUB_CONTAINER_PREFIX` | `agent-` | Container name prefix |
| `HUB_DEFAULT_LAUNCH_POLICY` | `manual` | Default launch policy |
| `HUB_DEFAULT_SHUTDOWN_POLICY` | `manual` | Default shutdown policy |
| `HUB_DEFAULT_IDLE_TIMEOUT` | `30` | Default idle timeout (minutes) |
| `HUB_PTY_BUFFER_SIZE` | `262144` | PTY scrollback buffer (bytes per agent) |

---

## Internals

Everything below this line is implementation detail for developers working on Agent Hub itself.

### Agent Lifecycle

```
STOPPED ──> STARTING ──> RUNNING ──> STOPPING ──> STOPPED
                │                        │
                └────────> ERROR <───────┘
```

Container startup uses a two-phase pattern: `docker run -d` with `SETUP_ONLY=1` (entrypoint configures the environment, then sleeps), followed by `docker exec` to start Claude Code inside a tmux session named `agent`.

### Inbox Monitoring

Watchdog monitors `.claude/users/{agent_id}/inbox/` directories. When a task file appears: inbox count updates, launch policy evaluates (may auto-start), a tmux notification is injected if the agent is running, and shutdown policy evaluates (may auto-stop if empty). Notifications are prefixed with `"Task notification:"` — the leading `T` cannot be mistaken for a Claude Code permission dialog response.

### REST API

REST (Representational State Transfer) is a convention for structuring HTTP APIs: URLs represent things (resources), and HTTP methods represent what you're doing to them. GET reads, POST triggers an action, PUT updates. This style works well when the API is about managing things — agents, policies, status — as opposed to calling functions.

The Hub exposes a REST API on `/api` consumed by the CLI and GUI.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/status` | Hub status (all agents + uptime) |
| GET | `/api/agents` | List all agents |
| GET | `/api/agents/{id}` | Get agent detail |
| POST | `/api/agents/{id}/start` | Start agent container |
| POST | `/api/agents/{id}/stop` | Stop agent container |
| GET | `/api/agents/{id}/policy` | Get agent policy |
| PUT | `/api/agents/{id}/policy` | Set agent policy |

### WebSocket API

While REST is request/response (client asks, server answers), WebSockets provide a persistent two-way channel — either side can send messages at any time. This is what makes live terminal streaming possible: the Hub pushes terminal output to the GUI as it happens, without the GUI having to poll for it.

The Hub provides a WebSocket endpoint at `/ws` for real-time terminal I/O and event broadcasting, consumed by the GUI's xterm.js terminals.

**Client -> Server:**

| Type | Fields | Description |
|------|--------|-------------|
| `subscribe` | `agent_id` | Start receiving PTY output |
| `unsubscribe` | `agent_id` | Stop receiving PTY output |
| `input` | `agent_id, data` | Send keystrokes (UTF-8) |
| `resize` | `agent_id, cols, rows` | Resize terminal |

**Server -> Client:**

| Type | Fields | Description |
|------|--------|-------------|
| `subscribed` | `agent_id, buffer` | Confirmed; buffer = base64 scrollback |
| `unsubscribed` | `agent_id` | Confirmed |
| `output` | `agent_id, data` | PTY output (base64) |
| `agent_state_changed` | `agent_id, state, agent` | State transition (broadcast) |
| `inbox_changed` | `agent_id, count` | Inbox count changed (broadcast) |
| `error` | `message` | Error |

### PTY Manager

The Hub attaches a persistent PTY session to each running agent via Docker's exec socket API. This provides live idle detection (for `idle_timeout` policy), a scrollback buffer (256KB default, served to WebSocket clients on subscribe), and a callback interface for real-time output streaming.

### Dependencies

fastapi, uvicorn, docker, watchdog, click, pydantic, pydantic-settings, httpx, mcp

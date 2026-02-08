# Agent Hub

Multi-agent container orchestration for Pipe Dream. Manages Docker container lifecycle, inbox monitoring, and policy-driven auto-start/stop for QMS agents.

## Architecture

```
agent-hub/
├── agent_hub/
│   ├── models.py       # Agent, AgentState, LaunchPolicy, ShutdownPolicy
│   ├── config.py       # HubConfig (pydantic-settings, env-configurable)
│   ├── container.py    # Docker SDK lifecycle (SETUP_ONLY two-phase startup)
│   ├── inbox.py        # Watchdog-based inbox monitoring
│   ├── notifier.py     # tmux send-keys notification injection
│   ├── policy.py       # Launch/shutdown policy evaluation engine
│   ├── hub.py          # Core orchestrator wiring all components
│   ├── pty_manager.py  # PTY session management (Docker exec socket I/O)
│   ├── cli.py          # Click CLI (6 commands)
│   └── api/
│       ├── server.py   # FastAPI app factory with lifespan management
│       └── routes.py   # REST endpoints on /api
├── tests/
└── pyproject.toml
```

## Installation

```bash
cd agent-hub
pip install -e .
```

Requires Python 3.11+ and a running Docker daemon.

## Quick Start

```bash
# Start the Hub (foreground service on :9000)
agent-hub start

# In another terminal:
agent-hub status
agent-hub start-agent qa
agent-hub stop-agent qa
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `agent-hub start` | Start the Hub as a foreground service |
| `agent-hub status` | Show hub uptime and all agent states |
| `agent-hub start-agent <id>` | Start an agent's container |
| `agent-hub stop-agent <id>` | Stop an agent's container |
| `agent-hub set-policy <id>` | Set an agent's launch/shutdown policy |
| `agent-hub attach <id>` | Attach to a running agent's terminal |

### `start` Options

| Flag | Default | Description |
|------|---------|-------------|
| `--host` | `127.0.0.1` | Host to bind |
| `--port` | `9000` | Port to bind |
| `--project-root` | cwd | Pipe Dream project root |
| `--log-level` | `info` | Logging level |

### `set-policy` Options

| Flag | Values | Description |
|------|--------|-------------|
| `--launch` | `manual`, `auto_on_task`, `always_on` | When to start the agent |
| `--shutdown` | `manual`, `on_inbox_empty`, `idle_timeout` | When to stop the agent |
| `--idle-timeout` | minutes (int) | Idle timeout duration |

## REST API

All endpoints are prefixed with `/api`.

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

## Agent Lifecycle

Agents transition through these states:

```
STOPPED ──► STARTING ──► RUNNING ──► STOPPING ──► STOPPED
                │                        │
                └────────► ERROR ◄───────┘
```

## Container Startup (SETUP_ONLY Pattern)

The Hub uses a two-phase startup matching the existing `launch.sh` pattern:

1. `docker run -d` with `SETUP_ONLY=1` — entrypoint runs setup, then sleeps
2. `docker exec` — starts `claude` inside a `tmux` session named `agent`

This separates container provisioning from Claude Code initialization.

## Policies

### Launch Policies

| Policy | Behavior |
|--------|----------|
| `manual` | Only starts via explicit command |
| `auto_on_task` | Auto-starts when inbox receives a task |
| `always_on` | Starts with the Hub, never auto-stops |

### Shutdown Policies

| Policy | Behavior |
|--------|----------|
| `manual` | Only stops via explicit command |
| `on_inbox_empty` | Auto-stops when inbox drops to zero |
| `idle_timeout` | Auto-stops after N minutes of inactivity |

## Inbox Monitoring

Uses `watchdog` to watch `.claude/users/{agent_id}/inbox/` directories. When a new task file appears:

1. Inbox count is updated on the agent record
2. Launch policy is evaluated (may auto-start the agent)
3. If the agent is running, a notification is injected via `tmux send-keys`
4. Shutdown policy is evaluated (may auto-stop if inbox is empty)

Notifications start with `"Task notification:"` — the leading `T` is not a valid Claude Code permission dialog response (`y`/`n`/`a`/`i`), mitigating accidental prompt responses.

## Environment Variables

All config can be set via environment variables with the `HUB_` prefix:

| Variable | Default | Description |
|----------|---------|-------------|
| `HUB_HOST` | `127.0.0.1` | Bind host |
| `HUB_PORT` | `9000` | Bind port |
| `HUB_PROJECT_ROOT` | cwd | Project root path |
| `HUB_DOCKER_IMAGE` | `docker-claude-agent` | Docker image name |
| `HUB_CONTAINER_PREFIX` | `agent-` | Container name prefix |
| `HUB_DEFAULT_LAUNCH_POLICY` | `manual` | Default launch policy |
| `HUB_DEFAULT_SHUTDOWN_POLICY` | `manual` | Default shutdown policy |
| `HUB_DEFAULT_IDLE_TIMEOUT` | `30` | Default idle timeout (minutes) |
| `HUB_PTY_BUFFER_SIZE` | `262144` | PTY scrollback buffer size per agent (bytes) |

## PTY Manager

The Hub attaches a persistent PTY session to each running agent's tmux session using the Docker SDK's exec socket API. This provides:

- **Live idle detection:** `Agent.last_activity` is updated on every terminal output event, enabling the `idle_timeout` shutdown policy to function correctly.
- **Scrollback buffer:** A configurable ring buffer (default 256KB) captures recent terminal output per agent. Future WebSocket clients can retrieve this on connect.
- **Callback interface:** Output callbacks can be registered for real-time streaming (designed for a future WebSocket endpoint).

PTY sessions are automatically attached when an agent starts and detached when it stops. The Hub also attaches to containers discovered already running at startup.

### CLI Attach

`agent-hub attach <id>` connects your terminal directly to a running agent's tmux session:

```bash
agent-hub attach qa        # Attach to QA agent
                            # Detach with Ctrl-B D
```

This bypasses the Hub's PTY Manager and runs `docker exec -it` directly, giving you a raw interactive terminal.

## Agent Roster

The default roster includes all QMS agents:

`claude`, `qa`, `tu_ui`, `tu_scene`, `tu_sketch`, `tu_sim`, `bu`

## Dependencies

- **fastapi** + **uvicorn** — REST API server
- **docker** — Docker SDK for container management
- **watchdog** — File system monitoring for inboxes
- **click** — CLI framework
- **pydantic** + **pydantic-settings** — Config and data models
- **httpx** — HTTP client for CLI-to-Hub communication

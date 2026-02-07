# Multi-Agent Orchestration: Refreshed Design

*Session-2026-02-06-004 — Successor to Session-2026-02-04-002*

---

## 1. Where We Are

Three days of implementation work (Feb 4-6) turned the original design session's concepts into running infrastructure. Not everything landed as originally imagined — some things landed better, some were superseded by discoveries, and some remain unbuilt. This document describes the system as it actually exists, then charts the path forward to the Hub and GUI.

### 1.1 The Ladder (Revised)

The original 5-rung ladder remains the right mental model, but the rung descriptions now reflect reality:

```
┌─────────────────────────────────────────────────────────────────┐
│  5. GUI                                                         │
│     Tauri + xterm.js visual interface to Hub                    │
│     STATUS: Design only                                         │
├─────────────────────────────────────────────────────────────────┤
│  4. Hub                                                         │
│     Python service: container lifecycle, PTY mux, policies      │
│     STATUS: Design only (but informed by real implementation)   │
├─────────────────────────────────────────────────────────────────┤
│  3. Multi-Agent Sessions  ◄── WE ARE HERE                       │
│     launch.sh + tmux + inbox-watcher.py + stdio proxy           │
│     STATUS: Operational — CR-056 family CLOSED                  │
├─────────────────────────────────────────────────────────────────┤
│  2. Containerized Session                                       │
│     Single container + MCP servers                              │
│     STATUS: Complete (subsumed by rung 3)                       │
├─────────────────────────────────────────────────────────────────┤
│  1. Basic                                                       │
│     Single terminal, sub-agents via Task tool                   │
│     STATUS: Complete (still the default for non-container work) │
└─────────────────────────────────────────────────────────────────┘
```

Rung 3 is where we live. The jump to Rung 4 (Hub) is the next major undertaking, and the jump from 4 to 5 (GUI) follows naturally since the Hub's API is the GUI's backend.

### 1.2 What Was Actually Built

| Component | File(s) | What It Does |
|-----------|---------|--------------|
| **Unified launcher** | `launch.sh` | Single/multi-agent sessions from one command |
| **Container image** | `docker/Dockerfile` | Python 3.11 + Node + Claude Code + tmux + gh |
| **Entrypoint** | `docker/entrypoint.sh` | State hygiene, SETUP_ONLY mode, surgical jq cleaning |
| **Stdio proxy** | `docker/scripts/mcp_proxy.py` | Stdio-to-HTTP bridge; 100% MCP reliability |
| **Inbox watcher** | `docker/scripts/inbox-watcher.py` | Watchdog + tmux send-keys notification injection |
| **MCP config** | `docker/.mcp.json` | Stdio proxy config for qms + git servers |
| **Agent definitions** | `.claude/agents/*.md` (6 files) | Role, SOPs, permissions, notification handling |
| **Per-agent isolation** | `.claude/users/{agent}/container/` | Auth, config, conversation state per agent |
| **QMS MCP server** | `qms-cli/qms_mcp/` | Full QMS operations via MCP tools |
| **Git MCP server** | `git_mcp/` | Safe git operations on host from container |
| **MCP server launchers** | `docker/scripts/start-*.sh` | Streamable-HTTP servers on ports 8000/8001 |

### 1.3 What Was Not Built (From Original Design)

These items from Session-2026-02-04-002 were not implemented. Some are still relevant; others have been rendered moot:

| Original Item | Status | Notes |
|---------------|--------|-------|
| `qms message` command | **Deferred** | Agent-to-agent messaging. Still valuable for Hub. |
| Inbox archive | **Deferred** | Items-never-deleted policy. Still valuable. |
| Notification types (msg-, notif-) | **Deferred** | Only task- items exist today. |
| Host-level tmux session | **Superseded** | tmux runs *inside* each container instead. |
| `inotifywait`-based watcher | **Superseded** | Python `watchdog` is cross-platform. |
| `multi-agent-session.sh` | **Superseded** | `launch.sh` handles both single and multi. |

---

## 2. The Architecture That Emerged

The implementation revealed an architecture that differs from the original design in instructive ways.

### 2.1 Actual Topology

```
HOST
┌──────────────────────────────────────────────────────────────────────┐
│                                                                      │
│  ┌────────────────────┐   ┌────────────────────┐                     │
│  │  QMS MCP Server    │   │  Git MCP Server    │                     │
│  │  :8000 (HTTP)      │   │  :8001 (HTTP)      │                     │
│  └─────────▲──────────┘   └─────────▲──────────┘                     │
│            │ HTTP                    │ HTTP                           │
│            │                        │                                │
│  ┌─────────┼────────────────────────┼──────────────────────────┐     │
│  │         │          CONTAINERS    │                          │     │
│  │  ┌──────┴───────┐  ┌────────────┴─┐  ┌──────────────┐     │     │
│  │  │ mcp_proxy.py │  │ mcp_proxy.py │  │ mcp_proxy.py │     │     │
│  │  │  (stdio)     │  │  (stdio)     │  │  (stdio)     │     │     │
│  │  └──────▲───────┘  └──────▲───────┘  └──────▲───────┘     │     │
│  │         │                 │                  │             │     │
│  │  ┌──────┴───────┐  ┌─────┴────────┐  ┌─────┴────────┐    │     │
│  │  │  claude      │  │     qa       │  │   tu_ui      │    │     │
│  │  │  (tmux)      │  │   (tmux)     │  │   (tmux)     │    │     │
│  │  │ agent-claude │  │  agent-qa    │  │ agent-tu_ui  │    │     │
│  │  └──────────────┘  └──────────────┘  └──────────────┘    │     │
│  └───────────────────────────────────────────────────────────┘     │
│                                                                      │
│  ┌──────────────────┐                                                │
│  │  inbox-watcher   │ ── watches ──► .claude/users/*/inbox/          │
│  │  (host process)  │ ── injects ──► docker exec + tmux send-keys    │
│  └──────────────────┘                                                │
│                                                                      │
│  ┌──────────────────┐                                                │
│  │  Terminal × N    │  (mintty/Terminal.app — one per agent)          │
│  │  docker exec -it │                                                │
│  └──────────────────┘                                                │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

### 2.2 Key Architectural Discoveries

These weren't planned — they emerged from implementation.

**1. Stdio proxy is the MCP transport layer.**
The original design assumed direct HTTP from container to host MCP servers. In practice, Claude Code's HTTP MCP client fails ~10% of the time in containers (client-side, no request emitted). The stdio proxy (`mcp_proxy.py`) solved this completely: Claude spawns it as a local subprocess (100% reliable stdio), and the proxy handles HTTP forwarding with retries. This is now a permanent architectural element, not a workaround.

**2. tmux lives inside each container, not on the host.**
The original design placed tmux on the host, with containers as panes. What actually works: each container runs its own tmux session (`tmux new-session -s agent "claude"`), and the inbox watcher reaches in via `docker exec ... tmux send-keys`. This is better — each container is self-contained, and the host doesn't need tmux installed.

**3. Claude Code has a pending message queue.**
When a tmux send-keys injection arrives while Claude is generating output, Claude Code's native input handling captures it as a pending message. The agent sees a "pending message" indicator and processes it when ready. This is superior to the original "hope the agent notices ASCII art in the terminal" approach — it's a first-class input mechanism.

**4. Two-phase container startup is essential.**
`docker run -d` with an interactive process (Claude Code) fails because the TTY isn't connected. The SETUP_ONLY pattern (`sleep infinity` then `docker exec -it`) solves this cleanly and enables the launch.sh orchestration model.

**5. Surgical state cleaning enables session persistence.**
The `jq`-based cleaning of `.claude.json` (removing MCP state while preserving OAuth credentials) means agents don't need to re-authenticate between sessions. This was a hard-won discovery after 17 debugging phases.

### 2.3 What launch.sh Actually Orchestrates

Understanding what `launch.sh` does today is essential context for Hub design, because the Hub will absorb and extend this role:

```
./launch.sh claude qa tu_ui

  1. Check/start QMS MCP server (:8000)
  2. Check/start Git MCP server (:8001)
  3. Build Docker image if needed
  4. For each agent:
     a. docker run -d -e SETUP_ONLY=1 -e QMS_USER={agent} ... → agent-{agent}
     b. Sleep 3s (stagger to avoid race conditions)
     c. Open new terminal window
     d. docker exec -it agent-{agent} tmux new-session -s agent "claude"
  5. Start inbox-watcher.py in current terminal
  6. On exit: stop and remove containers
```

**What launch.sh does well:** Zero-friction startup, cross-platform terminal spawning, per-agent isolation.

**What launch.sh cannot do:** Policy-based auto-launch/stop, programmatic lifecycle control, PTY multiplexing for remote clients, state broadcasting, idle detection.

That gap is exactly what the Hub fills.

---

## 3. The Hub (Rung 4)

### 3.1 What the Hub Is

The Hub is a long-running Python service that replaces `launch.sh` as the container orchestrator. It absorbs everything launch.sh does today and adds programmability: policies, an API, state awareness, and PTY multiplexing for GUI clients.

The Hub is **not** an AI agent. It is infrastructure software — a coordinator process that manages agent containers the way a process supervisor manages worker processes.

### 3.2 What the Hub Replaces

| Today (launch.sh) | Tomorrow (Hub) |
|--------------------|----------------|
| Bash script, runs once | Long-running Python service |
| Manual start per agent | Policy-driven auto-launch |
| One terminal window per agent | PTY streams over WebSocket |
| No idle detection | Configurable idle timeout |
| Inbox watcher as separate process | Inbox watching built in |
| No API | REST + WebSocket API |
| No state broadcasting | Real-time state events to clients |

### 3.3 Revised Hub Architecture

The original Hub design (Session-2026-02-04-002) was broadly correct. The revisions below incorporate what we learned during implementation.

```
                        ┌─────────────────┐
                        │   GUI Client    │ (Rung 5 — future)
                        │  Tauri+xterm.js │
                        └────────┬────────┘
                                 │ WebSocket
                                 │
                        ┌────────▼────────┐
                        │      Hub        │
                        │   (Python)      │
                        │                 │
                        │  ┌───────────┐  │
                        │  │ Container │  │  Docker lifecycle
                        │  │ Manager   │  │  (start/stop/health)
                        │  └───────────┘  │
                        │  ┌───────────┐  │
                        │  │ PTY       │  │  Terminal I/O mux
                        │  │ Manager   │  │  (stdin/stdout/resize)
                        │  └───────────┘  │
                        │  ┌───────────┐  │
                        │  │ Inbox     │  │  File watcher
                        │  │ Watcher   │  │  (auto-launch trigger)
                        │  └───────────┘  │
                        │  ┌───────────┐  │
                        │  │ Policy    │  │  Launch/shutdown rules
                        │  │ Engine    │  │  (idle timeout, etc.)
                        │  └───────────┘  │
                        │  ┌───────────┐  │
                        │  │ MCP       │  │  Health checks for
                        │  │ Monitor   │  │  QMS + Git servers
                        │  └───────────┘  │
                        │  ┌───────────┐  │
                        │  │ API       │  │  REST + WebSocket
                        │  │ Server    │  │  endpoints
                        │  └───────────┘  │
                        └────────┬────────┘
                                 │ Docker API
                    ┌────────────┼────────────┐
                    │            │            │
              ┌─────▼─────┐ ┌───▼────┐ ┌────▼─────┐
              │  claude   │ │  qa    │ │  tu_ui   │  ...
              │  (tmux)   │ │ (tmux) │ │  (tmux)  │
              └───────────┘ └────────┘ └──────────┘
```

### 3.4 Revised Design Decisions

**Container management: Docker SDK, not docker-compose.**
`launch.sh` uses `docker run` with explicit flags. The Hub should use the Docker SDK (`aiodocker`) directly. docker-compose adds an abstraction layer we don't need — the Hub *is* the orchestrator.

**PTY attachment: `docker exec` with TTY, not container attach.**
The SETUP_ONLY pattern means containers run `sleep infinity` as PID 1. Claude runs via `docker exec ... tmux new-session`. The Hub's PTY manager should follow the same pattern: `docker exec` to start claude inside tmux, then capture the exec's stdin/stdout streams.

**Notification injection: Keep the tmux send-keys mechanism.**
The inbox watcher's `docker exec ... tmux send-keys` pattern works well and leverages Claude Code's pending message queue. The Hub should absorb the inbox watcher's logic wholesale rather than invent a new notification mechanism.

**MCP servers: Hub starts and monitors them.**
Today, `launch.sh` checks/starts MCP servers. The Hub should own this responsibility and add health monitoring (periodic pings to `:8000/health` and `:8001/health`).

**State persistence: File-based, minimal.**
Agent policies and Hub configuration should persist to a simple JSON file (e.g., `.claude/hub-config.json`). No database. The Hub is a development tool, not a production service.

**No authentication on the Hub API.**
The Hub runs locally. Adding auth would be premature complexity. The GUI connects to `localhost:9000` — no network exposure.

### 3.5 Agent Lifecycle (Revised)

```
               ┌──────────┐
               │ STOPPED  │  Container does not exist
               └────┬─────┘
                    │
     ┌──────────────┼──────────────┐
     │              │              │
     ▼              ▼              ▼
[API request]  [inbox task]   [hub start +
                               always-on]
     │              │              │
     └──────────────┼──────────────┘
                    │
               ┌────▼─────┐
               │ STARTING │  docker run -d SETUP_ONLY=1
               │          │  docker exec tmux claude
               └────┬─────┘
                    │
               ┌────▼─────┐
               │ RUNNING  │  PTY attached, I/O streaming
               └────┬─────┘
                    │
     ┌──────────────┼──────────────┐
     │              │              │
     ▼              ▼              ▼
[API request]  [idle timeout] [inbox empty
                               + policy]
     │              │              │
     └──────────────┼──────────────┘
                    │
               ┌────▼─────┐
               │ STOPPING │  docker stop + docker rm
               └────┬─────┘
                    │
               ┌────▼─────┐
               │ STOPPED  │
               └──────────┘
```

### 3.6 Hub API (Revised)

The original API design was solid. One refinement: add an endpoint for notification injection (so the GUI can trigger notifications independently of inbox changes).

```
REST /api
├── GET    /status                    # Hub status, all agents, MCP health
├── GET    /agents                    # List agents with state + inbox count
├── GET    /agents/{id}              # Agent details
├── POST   /agents/{id}/start        # Start agent container
├── POST   /agents/{id}/stop         # Stop agent container
├── GET    /agents/{id}/policy       # Get launch/shutdown policy
├── PUT    /agents/{id}/policy       # Set launch/shutdown policy
├── POST   /agents/{id}/notify       # Inject text into agent terminal
├── GET    /mcp/health               # MCP server health status
└── GET    /health                    # Hub health check

WebSocket /ws
├── subscribe(agent_id)              # Start receiving PTY output
├── unsubscribe(agent_id)            # Stop receiving PTY output
├── input(agent_id, data)            # Send keystrokes to agent
├── resize(agent_id, cols, rows)     # Resize agent terminal
└── ← events                        # State changes, inbox events
```

### 3.7 Technology Stack (Confirmed)

The original stack choices hold up. One change: `watchdog` instead of `watchfiles`, since the inbox watcher already uses it successfully.

| Component | Technology | Rationale |
|-----------|------------|-----------|
| Language | Python 3.11+ | Consistent with QMS CLI and MCP servers |
| Async | asyncio | Native, no external deps |
| HTTP/WS | FastAPI + uvicorn | Modern, async-native |
| Docker | aiodocker | Official async SDK |
| File watch | watchdog | Already proven in inbox-watcher.py |
| CLI | click | Consistent with QMS CLI |
| Config | pydantic-settings | Validated config from env/file |

### 3.8 What the Hub Absorbs from Existing Infrastructure

The Hub doesn't start from scratch. It absorbs tested, working components:

| Existing Component | Hub Module | Transformation |
|-------------------|------------|----------------|
| `launch.sh` container startup | `container.py` | Bash → Python Docker SDK |
| `launch.sh` MCP server checks | `mcp_monitor.py` | Bash → async health checks |
| `inbox-watcher.py` file watching | `inbox.py` | Standalone → integrated |
| `inbox-watcher.py` tmux injection | `notifier.py` | Standalone → integrated |
| `entrypoint.sh` SETUP_ONLY flow | (unchanged) | Hub drives same container image |
| `mcp_proxy.py` | (unchanged) | Runs inside container as before |
| `.mcp.json` | (unchanged) | Container MCP config unchanged |

The Hub wraps existing infrastructure in a programmable service layer. The container image, entrypoint, proxy, and MCP config stay exactly as they are.

---

## 4. The GUI (Rung 5)

### 4.1 What the GUI Is

The GUI is a desktop application that provides a visual interface to the Hub. It is a **terminal multiplexer with QMS awareness** — it renders agent terminal sessions via xterm.js and displays QMS workflow state in a sidebar.

The GUI is optional. The Hub operates independently. The GUI is a viewport, not a controller — it observes and relays, it does not interpret.

### 4.2 Why Tauri + xterm.js

This decision from the original design session holds up and is strengthened by implementation experience:

- **xterm.js** is the only terminal emulator that handles Claude Code's rich output correctly (ANSI escapes, interactive prompts, progress indicators). Trying to parse or re-render Claude's output would be a bottomless pit. We wrap it in a terminal and let it be a terminal.
- **Tauri** gives us a native desktop app with a tiny footprint. The Rust backend is minimal — it's essentially an IPC bridge. All logic lives in the Hub (Python) and the frontend (TypeScript/React).
- **React/TypeScript** for the frontend is standard and well-supported by the xterm.js ecosystem.

### 4.3 GUI Layout (Revised)

The original mockup was on the right track. Refined:

```
┌──────────────────────────────────────────────────────────────────────┐
│  Pipe Dream Agent Hub                                       [─][□][×]│
├──────────────┬───────────────────────────────────────────────────────┤
│              │  claude │ qa │ tu_ui │                                │
│  AGENTS      ├─────────┴────┴───────┴───────────────────────────────┤
│              │                                                       │
│  ● claude    │  ╭──────────────────────────────────────────╮         │
│    ▸ inbox 0 │  │  Welcome! Session 2026-02-06-004         │         │
│  ● qa       │  │  initialized. Inbox: empty.               │         │
│    ▸ inbox 1 │  │                                          │         │
│  ○ tu_ui     │  │  What would you like to work on?         │         │
│  ○ tu_scene  │  ╰──────────────────────────────────────────╯         │
│  ○ tu_sketch │                                                       │
│  ○ tu_sim    │  > _                                                  │
│  ○ bu        │                                                       │
│              │                                                       │
│──────────────│                                                       │
│              │                                                       │
│  QMS STATUS  │                                                       │
│              │                                                       │
│  In Review   │                                                       │
│   (none)     │                                                       │
│  In Approval │                                                       │
│   (none)     │                                                       │
│  In Execution│                                                       │
│   (none)     │                                                       │
│              │                                                       │
│──────────────│                                                       │
│              │                                                       │
│  MCP SERVERS │                                                       │
│  ● QMS :8000 │                                                       │
│  ● Git :8001 │                                                       │
│              │                                                       │
└──────────────┴───────────────────────────────────────────────────────┘

Legend: ● running  ○ stopped  ▸ expandable
```

**Sidebar sections:**
1. **Agents** — State (running/stopped), inbox count, right-click for start/stop/policy
2. **QMS Status** — Documents in active workflow stages (pulled from QMS MCP)
3. **MCP Servers** — Health status of host MCP servers

**Main area:**
- Tab bar with one tab per running agent
- Each tab contains an xterm.js terminal connected to that agent's PTY via the Hub's WebSocket
- Clicking a stopped agent in the sidebar offers to start it and open a tab

### 4.4 GUI Data Flow

```
Keystroke in xterm.js
    │
    ▼ WebSocket message: {type: "input", agent_id: "claude", data: "ls\r"}
Hub receives
    │
    ▼ docker exec stdin write
Container tmux session
    │
    ▼ Claude Code processes
Container stdout
    │
    ▼ docker exec stdout read
Hub PTY manager
    │
    ▼ WebSocket message: {type: "output", agent_id: "claude", data: "..."}
xterm.js renders
```

This is a pure passthrough. The GUI never interprets terminal data — it relays bytes.

### 4.5 GUI Events from Hub

The Hub pushes state events to all connected WebSocket clients:

| Event | Trigger | GUI Response |
|-------|---------|-------------|
| `agent_state_changed` | Container start/stop | Update sidebar icon |
| `inbox_changed` | File appears/removed | Update inbox count badge |
| `mcp_health_changed` | Health check result | Update MCP status indicators |
| `pty_output` | Agent terminal output | Write to xterm.js |

### 4.6 Interaction Patterns

**Start an agent:**
1. User right-clicks agent in sidebar → "Start"
2. GUI sends `POST /api/agents/{id}/start`
3. Hub starts container, attaches PTY
4. Hub pushes `agent_state_changed` event
5. GUI updates sidebar, opens new terminal tab
6. GUI sends WebSocket `subscribe({id})`
7. Terminal output starts flowing

**Agent receives inbox task:**
1. QMS routes document → task file lands in inbox
2. Hub inbox watcher detects new file
3. Hub pushes `inbox_changed` event to GUI
4. Hub injects notification via tmux send-keys (existing mechanism)
5. GUI updates inbox count badge
6. Agent processes notification when ready (Claude Code pending message queue)

**Stop an idle agent:**
1. Hub policy engine detects idle timeout
2. Hub stops container
3. Hub pushes `agent_state_changed` event
4. GUI closes terminal tab, updates sidebar

---

## 5. Development Plan

### 5.1 Hub Implementation Phases

The Hub should be built incrementally, with each phase producing a testable artifact.

**Phase 1: Skeleton + Container Manager**
- Project structure, pyproject.toml, models, config
- ContainerManager: start/stop containers using Docker SDK
- Replicate launch.sh's container creation logic in Python
- CLI: `agent-hub start-agent claude`, `agent-hub stop-agent claude`
- *Test:* Start a container via Hub, verify it runs, stop it

**Phase 2: Inbox Watcher Integration**
- Port inbox-watcher.py logic into Hub
- Inbox change detection triggers agent state updates
- Notification injection via docker exec + tmux send-keys
- *Test:* Route a document, verify Hub detects inbox change and injects notification

**Phase 3: PTY Manager**
- Attach to container exec streams
- Read/write terminal I/O programmatically
- *Test:* Start agent, capture its terminal output in a buffer

**Phase 4: API Server**
- FastAPI app with REST endpoints
- WebSocket endpoint for PTY streaming
- State change broadcasting
- *Test:* Start Hub, connect via curl/wscat, observe agent output

**Phase 5: Policy Engine**
- Launch policies (manual, auto-on-task, always-on)
- Shutdown policies (manual, idle-timeout, on-inbox-empty)
- MCP health monitoring
- *Test:* Configure auto-launch policy, route document, verify agent starts

**Phase 6: CLI Polish**
- `agent-hub start` (starts Hub as foreground service)
- `agent-hub status` (shows all agent states)
- `agent-hub start-agent / stop-agent` (manual lifecycle)
- `agent-hub attach` (future — terminal attachment)

### 5.2 GUI Implementation Phases

The GUI can begin after Phase 4 of the Hub (once the WebSocket API exists).

**Phase 1: Scaffold + Single Terminal**
- Tauri project setup
- React frontend with xterm.js
- Connect to Hub WebSocket
- Render one agent's terminal output
- *Test:* See claude's terminal output in the GUI window

**Phase 2: Multi-Agent Tabs**
- Tab bar for multiple agents
- Subscribe/unsubscribe on tab switch
- Start/stop agents from GUI
- *Test:* Run claude + qa, switch between tabs

**Phase 3: Sidebar**
- Agent list with state indicators
- Inbox count badges
- MCP health indicators
- Right-click context menus

**Phase 4: QMS Awareness**
- Poll QMS MCP for active document status
- Display documents in workflow stages
- Click-to-view document content

### 5.3 QMS Governance

The Hub and GUI are new codebases. Per SOP-005:

- **Hub:** Genesis Sandbox → Adoption CR (it's a new standalone tool)
- **GUI:** Genesis Sandbox → Adoption CR (separate system)
- **Both** get SDLC documentation (RS + RTM) at adoption time

The genesis sandbox model is appropriate here — these are new, self-contained systems that will benefit from free-form foundational development before being brought under full QMS governance.

---

## 6. What Changed from the Original Design

For the record, here are the meaningful divergences from Session-2026-02-04-002:

| Original Vision | What Actually Happened | Why |
|----------------|----------------------|-----|
| Direct HTTP MCP transport | Stdio proxy (`mcp_proxy.py`) | HTTP fails ~10% in containers |
| Host-level tmux multiplexer | tmux inside each container | Self-contained containers are cleaner |
| `inotifywait` for file watching | Python `watchdog` library | Cross-platform (Windows host) |
| ASCII art notification boxes | Direct instruction injection | Claude Code's pending message queue is better |
| Five separate launcher scripts | Single `launch.sh` | Consolidation after iterative development |
| Inbox archive system | Not built yet | Lower priority than core infrastructure |
| `qms message` command | Not built yet | Still valuable, deferred to Hub era |
| Hub design assumed reliable HTTP | Hub design now assumes stdio proxy | Proxy is permanent infrastructure |

None of these are failures — they're the natural refinement that happens when design meets implementation. The system that emerged is simpler and more reliable than what was originally envisioned.

---

## 7. Open Questions for This Session

1. **Hub development model:** Genesis Sandbox or CR-governed from the start? The sandbox model lets us iterate freely during foundation work, with an Adoption CR when the structure stabilizes.

2. **Hub location:** `agent-hub/` as a new top-level directory? Or a submodule like `flow-state` and `qms-cli`?

3. **GUI development model:** Same question. Likely also genesis → adoption.

4. **GUI location:** `agent-gui/` as top-level? Submodule?

5. **Priority ordering:** Hub Phase 1-3 first (container management without GUI), then GUI Phase 1 in parallel with Hub Phase 4-5? Or serial?

6. **Scope of `qms message` and inbox archive:** Build these as part of the Hub, or as QMS CLI features first?

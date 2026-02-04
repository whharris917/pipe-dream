# Multi-Agent Hub & GUI Architecture

This document captures the design discussion from Session-2026-02-04-002 regarding the coordination layer (Hub) and graphical interface (GUI) for multi-agent container orchestration.

## Design Principles

1. **Hub is primary** — The Hub is the source of truth for agent coordination; the GUI is optional
2. **Terminal-centric GUI** — The GUI wraps terminal emulators, not a custom chat interface
3. **Separation of concerns** — Hub manages lifecycle and state; GUI provides visualization
4. **Headless operation** — Agents can run and coordinate without the GUI

## Three-Layer Stack

```
                              ┌─────────────────┐
                              │      GUI        │
                              │   (optional)    │
                              └────────┬────────┘
                                       │ WebSocket
                                       │
┌──────────────────────────────────────┼──────────────────────────────────────┐
│                                      │                                       │
│                              ┌───────▼───────┐                              │
│                              │      Hub      │                              │
│                              │   (Python)    │                              │
│                              └───────┬───────┘                              │
│                                      │                                       │
│        ┌─────────────┬───────────────┼───────────────┬─────────────┐        │
│        │             │               │               │             │        │
│        ▼             ▼               ▼               ▼             ▼        │
│   ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐      │
│   │ claude  │   │   qa    │   │  tu_ui  │   │ tu_sim  │   │   ...   │      │
│   └────┬────┘   └────┬────┘   └────┬────┘   └────┬────┘   └────┬────┘      │
│        │             │             │             │             │            │
│        └─────────────┴─────────────┴─────────────┴─────────────┘            │
│                                    │                                         │
│                            ┌───────┴───────┐                                │
│                            │  MCP Servers  │                                │
│                            │  (QMS + Git)  │                                │
│                            └───────────────┘                                │
│                                                                              │
│                                  HOST                                        │
└──────────────────────────────────────────────────────────────────────────────┘
```

## The Hub (Python)

The Hub is a standalone process that coordinates all agent containers. It is purely programmatic—no AI agent lives in the Hub.

### Responsibilities

| Responsibility | Details |
|----------------|---------|
| **Container lifecycle** | Start, stop, restart agent containers |
| **PTY management** | Create/destroy PTYs attached to containers |
| **Inbox watching** | Monitor `.claude/users/*/inbox/` for changes |
| **Policy enforcement** | Auto-launch, idle timeout, shutdown on empty |
| **State broadcasting** | Push state changes to connected clients |
| **PTY multiplexing** | Route terminal I/O between clients and containers |

### Agent States

```
                    ┌──────────┐
                    │ INACTIVE │ (container not running)
                    └────┬─────┘
                         │
          ┌──────────────┼──────────────┐
          │              │              │
          ▼              ▼              ▼
    [manual launch] [auto-launch]  [always-on]
          │              │              │
          └──────────────┼──────────────┘
                         │
                    ┌────▼─────┐
                    │  ACTIVE  │ (container running)
                    └────┬─────┘
                         │
          ┌──────────────┼──────────────┐
          │              │              │
          ▼              ▼              ▼
    [manual stop]  [idle timeout]  [inbox empty]
          │              │              │
          └──────────────┼──────────────┘
                         │
                    ┌────▼─────┐
                    │ INACTIVE │
                    └──────────┘
```

### Launch Policies

| Policy | Behavior |
|--------|----------|
| `MANUAL` | Only launches when user explicitly requests |
| `AUTO_ON_TASK` | Launches when inbox receives a task |
| `ALWAYS_ON` | Starts with hub, never stops automatically |

### Shutdown Policies

| Policy | Behavior |
|--------|----------|
| `MANUAL` | Only stops when user explicitly requests |
| `ON_INBOX_EMPTY` | Stops when agent's inbox is empty |
| `IDLE_TIMEOUT` | Stops after N minutes of no activity |

### Hub API

```
WebSocket /ws
├── subscribe(agent_id)          # Start receiving PTY output for agent
├── unsubscribe(agent_id)        # Stop receiving PTY output
├── input(agent_id, data)        # Send keystrokes to agent PTY
├── resize(agent_id, cols, rows) # Resize agent PTY
└── events                       # Receive state change events

REST /api
├── GET    /agents               # List all agents and their states
├── GET    /agents/{id}          # Get agent details
├── POST   /agents/{id}/start    # Start agent container
├── POST   /agents/{id}/stop     # Stop agent container
├── GET    /agents/{id}/policy   # Get launch/shutdown policy
├── PUT    /agents/{id}/policy   # Set launch/shutdown policy
├── GET    /qms/status           # QMS overview (inbox counts, etc.)
└── GET    /health               # Hub health check
```

### Headless CLI

```bash
# Start the hub
$ agent-hub start
Hub listening on localhost:9000
Watching inboxes...
MCP servers: QMS (8000), Git (8001)

# In another terminal, use CLI
$ agent-hub status
AGENT       STATE      INBOX   POLICY
claude      ACTIVE     0       always-on
qa          INACTIVE   2       auto-launch
tu_ui       INACTIVE   0       manual
tu_scene    INACTIVE   1       auto-launch
tu_sketch   INACTIVE   0       manual
tu_sim      INACTIVE   0       manual
bu          INACTIVE   0       manual

$ agent-hub start qa
Starting qa...
qa is now ACTIVE

$ agent-hub attach qa
# Attaches terminal to qa's PTY (like tmux attach)
```

### Implementation Sketch

```python
# agent_hub/hub.py

class AgentHub:
    def __init__(self, config: HubConfig):
        self.agents: dict[str, Agent] = {}
        self.clients: list[WebSocketClient] = []
        self.inbox_watcher = InboxWatcher(self.on_inbox_change)
        self.docker = DockerClient()

    async def start(self):
        """Start the hub."""
        await self.inbox_watcher.start()
        await self.start_api_server()

        # Launch always-on agents
        for agent_id, agent in self.agents.items():
            if agent.policy.launch == LaunchPolicy.ALWAYS_ON:
                await self.start_agent(agent_id)

    async def start_agent(self, agent_id: str):
        """Start an agent container and attach PTY."""
        agent = self.agents[agent_id]

        # Start container
        container = await self.docker.start_container(
            image="claude-agent",
            environment={"QMS_USER": agent_id},
            volumes=self.get_agent_volumes(agent_id),
        )

        # Attach PTY
        agent.pty = await self.docker.attach_pty(container)
        agent.state = AgentState.ACTIVE

        # Broadcast state change
        await self.broadcast(AgentStateChanged(agent_id, AgentState.ACTIVE))

        # Start reading PTY output
        asyncio.create_task(self.relay_pty_output(agent))

    async def on_inbox_change(self, agent_id: str, tasks: list[Task]):
        """Called when an agent's inbox changes."""
        agent = self.agents[agent_id]

        if tasks and agent.state == AgentState.INACTIVE:
            if agent.policy.launch == LaunchPolicy.AUTO_ON_TASK:
                await self.start_agent(agent_id)

        elif not tasks and agent.state == AgentState.ACTIVE:
            if agent.policy.shutdown == ShutdownPolicy.ON_INBOX_EMPTY:
                await self.stop_agent(agent_id)

    async def relay_pty_output(self, agent: Agent):
        """Relay PTY output to subscribed clients."""
        async for data in agent.pty.read():
            for client in self.clients:
                if agent.id in client.subscriptions:
                    await client.send(PtyOutput(agent.id, data))
```

## The GUI (Tauri + xterm.js)

The GUI is a terminal multiplexer with QMS awareness. It does not interpret Claude's output—it renders terminals.

### Technology Choices

| Component | Technology | Rationale |
|-----------|------------|-----------|
| Framework | Tauri | Lightweight, uses system webview, Rust backend |
| Terminal | xterm.js | Battle-tested, full ANSI support, used by VS Code |
| Frontend | React/TypeScript | Standard web UI framework |

### What the GUI Does

- Renders terminal tabs connected to agent PTYs (via Hub)
- Shows agent status in sidebar
- Displays QMS document tree and inbox counts
- Provides right-click menus for agent lifecycle

### What the GUI Does NOT Do

- Parse or render Claude's markdown (terminal handles it)
- Intercept or modify conversation (pure passthrough)
- Implement Claude Code features (it's just a terminal)

### GUI Mockup

```
┌─────────────────────────────────────────────────────────────────┐
│  Pipe Dream                                            [─][□][×]│
├────────────────┬────────────────────────────────────────────────┤
│ AGENTS         │ claude │ qa │                                  │
│                ├────────┴────┴──────────────────────────────────┤
│ ● claude    ▼  │                                                │
│ ○ qa        ▼  │  $ claude                                      │
│ ○ tu_ui     ▼  │                                                │
│ ○ tu_scene  ▼  │  ╭────────────────────────────────────────╮    │
│ ○ tu_sketch ▼  │  │ Session-2026-02-04-002 initialized     │    │
│ ○ tu_sim    ▼  │  │                                        │    │
│ ○ bu        ▼  │  │ What would you like to work on?        │    │
│                │  ╰────────────────────────────────────────╯    │
│────────────────│                                                │
│ QMS            │  > Let's discuss the GUI architecture_         │
│                │                                                │
│ In Review (2)  │                                                │
│  CR-056        │                                                │
│  SOP-008       │                                                │
│                │                                                │
│ In Approval (1)│                                                │
│  CR-055        │                                                │
│                │                                                │
│────────────────│                                                │
│ DOCUMENTS      │                                                │
│                │                                                │
│ > QMS/         │                                                │
│   > SOP/       │                                                │
│   > CR/        │                                                │
│ > flow-state/  │                                                │
└────────────────┴────────────────────────────────────────────────┘
```

### Implementation Sketch

```typescript
// Pseudocode for GUI

class AgentGUI {
    hub: WebSocket;
    terminals: Map<string, XTerminal>;

    connect() {
        this.hub = new WebSocket("ws://localhost:9000/ws");
        this.hub.onmessage = this.handleHubMessage;
    }

    handleHubMessage(msg: HubMessage) {
        switch (msg.type) {
            case "agent_state_changed":
                this.updateSidebar(msg.agent_id, msg.state);
                break;
            case "pty_output":
                this.terminals.get(msg.agent_id)?.write(msg.data);
                break;
        }
    }

    openAgentTab(agentId: string) {
        // Create terminal
        const term = new Terminal();
        this.terminals.set(agentId, term);

        // Subscribe to PTY output
        this.hub.send({ type: "subscribe", agent_id: agentId });

        // Forward keystrokes to Hub
        term.onData(data => {
            this.hub.send({ type: "input", agent_id: agentId, data });
        });
    }

    launchAgent(agentId: string) {
        fetch(`http://localhost:9000/api/agents/${agentId}/start`, { method: "POST" });
    }
}
```

## File Structure

```
pipe-dream/
├── agent-hub/                    # Hub (Python)
│   ├── agent_hub/
│   │   ├── __init__.py
│   │   ├── __main__.py           # CLI entry point
│   │   ├── hub.py                # Core hub logic
│   │   ├── container.py          # Docker management
│   │   ├── pty.py                # PTY handling
│   │   ├── inbox.py              # Inbox watcher
│   │   ├── policy.py             # Launch/shutdown policies
│   │   ├── api.py                # REST + WebSocket server
│   │   └── config.py             # Configuration
│   ├── requirements.txt
│   └── pyproject.toml
│
├── agent-gui/                    # GUI (Tauri)
│   ├── src-tauri/                # Rust backend (minimal - just IPC)
│   ├── src/                      # Web frontend
│   │   ├── App.tsx
│   │   ├── components/
│   │   │   ├── Sidebar.tsx
│   │   │   ├── AgentTabs.tsx
│   │   │   ├── Terminal.tsx      # xterm.js wrapper
│   │   │   └── QMSTree.tsx
│   │   └── hooks/
│   │       └── useHub.ts         # WebSocket connection
│   └── ...
│
├── docker/                       # Container infra (existing)
├── qms-cli/                      # QMS CLI (existing)
├── git_mcp/                      # Git MCP server (existing)
└── ...
```

## Startup Sequence

```bash
# 1. Start MCP servers (existing scripts)
$ ./docker/scripts/start-mcp-server.sh --background
$ ./docker/scripts/start-git-mcp.sh --background

# 2. Start Hub
$ agent-hub start --daemon
# Hub starts, launches "always-on" agents (claude by default)

# 3. (Optional) Start GUI
$ agent-gui
# Connects to Hub, shows terminal tabs
```

## Data Flow: Terminal I/O

```
User types in xterm.js
        │
        ▼ (via WebSocket)
Hub receives input
        │
        ▼ (via PTY)
Container stdin
        │
        ▼
Claude Code process
        │
        ▼
Container stdout
        │
        ▼ (via PTY)
Hub receives output
        │
        ▼ (via WebSocket)
xterm.js renders output
```

## Data Flow: Agent Lifecycle

```
User right-clicks "qa" → "Launch"
        │
        ▼
GUI sends: POST /api/agents/qa/start
        │
        ▼
Hub → Docker: start qa container
        │
        ▼
Hub → GUI (WebSocket): agent_state_changed("qa", "ACTIVE")
        │
        ▼
GUI updates sidebar, opens new terminal tab
        │
        ▼
GUI sends: subscribe("qa")
        │
        ▼
Hub begins relaying qa PTY output to GUI
```

## Open Questions

1. **PTY attachment**: `docker exec -it` vs Docker API's attach endpoint?
2. **Hub port**: Default 9000? Configurable?
3. **Authentication**: Should Hub require auth for API access?
4. **Multiple GUIs**: Can multiple GUI instances connect to same Hub?
5. **Persistence**: Should Hub persist agent policies across restarts?

## Next Steps

1. Create CR for Hub implementation (genesis sandbox or standard CR?)
2. Decide on genesis vs incremental approach for GUI
3. Prototype Hub with single agent to validate PTY multiplexing
4. Prototype GUI with single terminal tab to validate xterm.js integration

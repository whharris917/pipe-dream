# Agent Hub GUI

Tauri v2 desktop application that provides a visual terminal multiplexer for Pipe Dream's multi-agent orchestration hub.

## Prerequisites

- **Node.js** >= 22
- **Rust** >= 1.75 (via [rustup](https://rustup.rs))
- **Visual Studio Build Tools** with C++ workload (Windows only)
- **Agent Hub CLI** installed and venv active (`agent-hub` in PATH)

## Development

```bash
npm install
npm run tauri dev
```

This starts Vite dev server on port 1420 and launches the Tauri window.

## Build

```bash
npm run tauri build
```

Produces a standalone executable in `src-tauri/target/release/`.

## Architecture

```
src/
├── main.tsx                  # React entry point
├── App.tsx                   # Root: layout, bootstrap + WebSocket lifecycle, keyboard shortcuts
├── ensureHub.ts              # Auto-bootstrap: spawn Hub if not running, poll until ready
├── types.ts                  # TypeScript types mirroring Hub models
├── constants.ts              # Hub URL, agent display names, reconnect config
├── hub-api.ts                # REST client (fetch agents, start/stop, policy)
├── hooks/
│   ├── useHubConnection.ts   # WebSocket singleton + React hook
│   └── useAgentStore.ts      # Zustand state store
├── components/
│   ├── Sidebar/              # Agent roster, MCP/QMS placeholders
│   ├── Terminal/             # Tab bar, xterm.js terminal views
│   └── StatusBar.tsx         # Connection status + hub uptime
└── styles/
    └── global.css            # Catppuccin Mocha dark theme
```

### Auto-Bootstrap

The GUI auto-starts the Hub if it isn't running:

1. On mount, `ensureHub()` checks `GET /api/health`
2. If down, status bar shows "Starting Hub..." (pulsing yellow dot)
3. Spawns `agent-hub start` via Tauri shell (scoped to that single command)
4. Polls `/api/health` every 1s for up to 30s
5. Once Hub responds, connects WebSocket normally

The Hub's own startup auto-starts MCP servers, so the GUI only needs to ensure the Hub layer. If `agent-hub` is not in PATH (venv not active), the spawn fails silently and the GUI falls back to reconnect-with-backoff.

### Key Design Decisions

- **Demand-driven bootstrap** — GUI spawns Hub on demand via Tauri shell
- **Single WebSocket** multiplexes all agent PTY subscriptions
- **Terminal persistence** via CSS visibility toggle (tabs stay alive in memory)
- **Base64 to Uint8Array** decode for raw byte writes to xterm.js
- **Buffer replay muting** — DA escape responses suppressed during scrollback write
- **Zustand** for state (WebSocket handler needs `getState()` outside React)
- **No Tauri IPC** for Hub communication — pure HTTP/WS to localhost:9000

### Hub API Surface

**REST** (`http://localhost:9000/api`): `/health`, `/status`, `/agents`, `/agents/{id}`, `/agents/{id}/start`, `/agents/{id}/stop`, `/agents/{id}/policy`

**WebSocket** (`ws://localhost:9000/ws`): subscribe/unsubscribe/input/resize messages; receives output (base64), agent_state_changed, inbox_changed events

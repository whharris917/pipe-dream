# Agent Hub GUI

Tauri v2 desktop application that provides a visual terminal multiplexer for Pipe Dream's multi-agent orchestration hub.

## Prerequisites

- **Node.js** >= 22
- **Rust** >= 1.75 (via [rustup](https://rustup.rs))
- **Visual Studio Build Tools** with C++ workload (Windows only)
- **Agent Hub** running on `localhost:9000`

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
├── App.tsx                   # Root: layout, WebSocket lifecycle, keyboard shortcuts
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

### Key Design Decisions

- **Single WebSocket** multiplexes all agent PTY subscriptions
- **Terminal persistence** via CSS visibility toggle (tabs stay alive in memory)
- **Base64 to Uint8Array** decode for raw byte writes to xterm.js
- **Zustand** for state (WebSocket handler needs `getState()` outside React)
- **No Tauri IPC** for Hub communication — pure HTTP/WS to localhost:9000

### Hub API Surface

**REST** (`http://localhost:9000/api`): `/health`, `/status`, `/agents`, `/agents/{id}`, `/agents/{id}/start`, `/agents/{id}/stop`, `/agents/{id}/policy`

**WebSocket** (`ws://localhost:9000/ws`): subscribe/unsubscribe/input/resize messages; receives output (base64), agent_state_changed, inbox_changed events

# Session 2026-02-08-002 Summary

## Completed

### CR-066: Agent Hub PTY Manager (CLOSED v2.0)

**Design & Approval:**
- Reviewed multi-agent orchestration refresh design doc (Session-2026-02-06-004)
- Identified Rung 4 remaining work: PTY Manager, WebSocket endpoint, MCP Monitor
- Drafted CR-066, QA reviewed/approved, released for execution

**Implementation (EI-1 through EI-4, commit 98dab02):**
- Created `agent-hub/agent_hub/pty_manager.py` (PTYSession + PTYManager)
- Integrated into Hub lifecycle (hub.py): attach/detach/discovery/sync
- Added CLI `attach` command, README docs, config/model fields

**UAT (EI-5, 10 tests against live Docker):**
- 9 PASS, 1 PARTIAL PASS (idle timeout)
- F-001: tmux status bar noise defeats idle detection
- F-002: discovery doesn't capture container_id

**Fixes (EI-6 through EI-8, commit f21264d):**
- F-001: Rate-based activity filter in `Hub._on_pty_output()` — requires two PTY events
  within 10s to count as activity. tmux status bar (~60s) filtered; real output passes.
  Idle timeout verified: fired at 3m (previously defeated by noise).
- F-002: Added `ContainerManager.get_container_id()`, wired into both discovery paths.
- EI-8: Lead manually verified CLI attach (tmux renders, Ctrl-B D detaches cleanly).

**Post-review & closure:**
- QA post-reviewed (recommend) and approved (v2.0)
- Closed

### Key Technical Insights

- **tmux status bar** generates terminal output every ~60s even when idle. Any PTY-based
  idle detection must filter this noise. Rate-based filtering (require sustained output)
  is more robust than size-based thresholds.
- **OS sleep suspends asyncio** — timers, sleep(), and background tasks all freeze.
  Wall-clock-based idle calculations work correctly across sleep (idle time = real elapsed).
- **Docker exec socket types** vary by platform (`recv`/`send` vs `read`/`write`).
  The `_recv`/`_send` helpers in PTYSession handle both.

## Current State

| Item | Status | Notes |
|------|--------|-------|
| CR-066 | CLOSED (v2.0) | All 8 EIs Pass |
| Agent Hub | genesis, not under SDLC | Rung 4 Hub: PTY Manager complete |
| QA agent | a35c443 | Available for resume |

## Key Files

- `agent-hub/agent_hub/pty_manager.py` -- PTYSession + PTYManager
- `agent-hub/agent_hub/hub.py` -- PTY integration + rate-based activity filter
- `agent-hub/agent_hub/container.py` -- get_container_id() for discovery
- `agent-hub/agent_hub/models.py` -- pty_attached field
- `agent-hub/agent_hub/cli.py` -- attach command
- `agent-hub/agent_hub/config.py` -- pty_buffer_size
- `agent-hub/README.md` -- PTY Manager documentation

---

## Next Steps: Hub → GUI Readiness

The Hub needs three more pieces before GUI integration (Rung 5) can begin. These are
ordered by dependency — the GUI's Phase 1 (single terminal in a window) is blocked
only by item 1. Items 2-3 are needed for the GUI sidebar but can land in parallel.

### 1. WebSocket Endpoint (GUI BLOCKER)

**What:** A `/ws` WebSocket endpoint on the Hub that streams PTY output and accepts input.

**Why:** The GUI renders agent terminals via xterm.js. xterm.js needs a bidirectional
byte stream — WebSocket is the transport. Without this, the GUI has no way to display
agent terminals. This is the single critical-path item.

**Interface (from design doc Section 3.6):**
```
WebSocket /ws
├── subscribe(agent_id)           # Start receiving PTY output
├── unsubscribe(agent_id)         # Stop receiving PTY output
├── input(agent_id, data)         # Send keystrokes to agent
├── resize(agent_id, cols, rows)  # Resize agent terminal
└── ← events                     # State changes, inbox events
```

**PTY Manager already provides the backend:**
- `register_callback(fn)` → subscribe to output for WebSocket broadcasting
- `get_buffer(agent_id)` → scrollback on late-joining clients
- `write(agent_id, data)` → keystroke injection
- `resize(agent_id, cols, rows)` → terminal resize

**Scope:** New file `agent-hub/agent_hub/api/websocket.py`. Wire into FastAPI app.
Add Hub methods for state-change event broadcasting.

### 2. MCP Health Monitor (GUI sidebar)

**What:** Periodic health checks for QMS MCP (:8000) and Git MCP (:8001) servers.

**Why:** The GUI sidebar shows MCP server health indicators. The Hub currently doesn't
monitor MCP servers at all — `launch.sh` checked them at startup but the Hub doesn't.

**Interface (from design doc Section 3.6):**
```
GET /mcp/health    # { qms: { status, url, last_check }, git: { ... } }
```

**Scope:** New file `agent-hub/agent_hub/mcp_monitor.py`. Periodic async HTTP pings.
Push `mcp_health_changed` events to WebSocket clients.

### 3. Notification Endpoint (GUI interaction)

**What:** `POST /agents/{id}/notify` — inject text into an agent's terminal.

**Why:** The GUI needs to send notifications to agents independently of inbox file
drops. The Hub's `notifier.py` already has `inject_notification()` — this just needs
an API route.

**Scope:** One new route in `agent-hub/agent_hub/api/routes.py`. Trivial.

### Existing REST API (already built)

These endpoints already exist and cover the GUI sidebar's core needs:

| Endpoint | Purpose | GUI Use |
|----------|---------|---------|
| `GET /health` | Hub liveness | Connection status |
| `GET /status` | All agents + uptime | Initial load |
| `GET /agents` | Agent list with state | Sidebar agent list |
| `GET /agents/{id}` | Agent detail | Agent panel |
| `POST /agents/{id}/start` | Start container | Sidebar right-click |
| `POST /agents/{id}/stop` | Stop container | Sidebar right-click |
| `GET /agents/{id}/policy` | Get policy | Policy display |
| `PUT /agents/{id}/policy` | Set policy | Policy editor |

### Suggested CR Sequence

1. **CR for WebSocket endpoint** — unlocks GUI Phase 1 (single terminal in a window)
2. **CR for MCP Monitor + notify endpoint** — unlocks GUI Phase 3 (full sidebar)
3. **CR for GUI scaffold** (Tauri + xterm.js + single terminal) — first visual

Items 1 and 2 can be developed in parallel. Item 3 depends on item 1.

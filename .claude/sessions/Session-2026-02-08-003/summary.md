# Session 2026-02-08-003 Summary

## Completed

### CR-067: Agent Hub WebSocket Endpoint (CLOSED v2.0)

**Design & Approval:**
- Explored existing Hub architecture (API routes, PTY Manager, Hub lifecycle, models, config)
- Read design doc (Session-2026-02-06-004 multi-agent-orchestration-refresh.md Section 3.6)
- Planned Broadcaster + WebSocket handler architecture
- Drafted CR-067, QA reviewed/approved, released for execution

**Implementation (EI-1 through EI-4, commit 2deaa6a):**
- Created `agent-hub/agent_hub/broadcaster.py` — ConnectionState (per-connection WebSocket + subscription set + unique ID) + Broadcaster (asyncio.Lock-protected connection set, snapshot iteration for broadcast, stale connection cleanup)
- Created `agent-hub/agent_hub/api/websocket.py` — FastAPI `/ws` route with JSON message dispatch: subscribe (validates agent, sends base64 scrollback buffer), unsubscribe, input (requires subscription, writes to PTY), resize (requires subscription)
- Modified `agent-hub/agent_hub/api/server.py` — imports ws_router/Broadcaster, creates Broadcaster on app.state, wires via hub.set_broadcaster() in lifespan, mounts ws_router
- Modified `agent-hub/agent_hub/hub.py` — added `_broadcaster` attribute + `set_broadcaster()` (registers as PTY callback), `_broadcast_state()` helper emitting from start_agent/stop_agent/_container_sync_loop, inbox events from _on_inbox_change, cleanup in stop()

**UAT (EI-5, commit 102f983):**
- Created `tests/test_websocket_uat.py` with 10 tests via FastAPI TestClient
- T1: connect/disconnect lifecycle, T2: subscribe known agent, T3: subscribe unknown (error), T4: unsubscribe, T5: input without subscription (error), T6: resize without subscription (error), T7: unknown message type (error), T8: missing agent_id (error), T9: broadcast_agent_state, T10: broadcast_inbox_change
- All 10 PASS (3.00s)

**Documentation (EI-6, commit 102f983):**
- Updated `agent-hub/README.md`: architecture tree, WebSocket API section with message protocol tables and example session, PTY Manager section updated, dependencies updated

**Post-review & closure (commit 152b5d4):**
- QA post-reviewed (recommend) and approved (v2.0)
- Closed

### Key Technical Decisions

- **Broadcaster as separate class** (not inside Hub): Hub manages lifecycle, Broadcaster manages WebSocket delivery. No circular dependencies — Hub imports Broadcaster under TYPE_CHECKING only.
- **Base64 encoding for PTY data**: Uniform JSON protocol over WebSocket. xterm.js can decode base64 to Uint8Array easily. Binary frames can be added later if profiling shows bottleneck.
- **Subscription model**: Per-connection `set[str]` of agent IDs. PTY output goes only to subscribers; state/inbox events go to all clients.
- **Snapshot iteration**: Broadcast methods copy connection set under lock, iterate outside lock. Failed sends trigger stale connection cleanup without interrupting other clients.
- **Subscribe to stopped agent**: Allowed. Client receives state-change events when agent starts later.

## Current State

| Item | Status | Notes |
|------|--------|-------|
| CR-067 | CLOSED (v2.0) | All 6 EIs Pass |
| Agent Hub | Genesis sandbox | Rung 4 Hub: WebSocket endpoint complete |
| QA agent | ab18c0d | Available for resume |

## Key Files

- `agent-hub/agent_hub/broadcaster.py` — ConnectionState + Broadcaster fan-out
- `agent-hub/agent_hub/api/websocket.py` — /ws route + message dispatch
- `agent-hub/agent_hub/api/server.py` — App factory with Broadcaster wiring
- `agent-hub/agent_hub/hub.py` — Broadcaster integration + event emission
- `agent-hub/README.md` — WebSocket API documentation
- `agent-hub/tests/test_websocket_uat.py` — 10 protocol tests

## Message Protocol Reference

**Client -> Server:** subscribe, unsubscribe, input, resize
**Server -> Client:** subscribed (+ buffer), unsubscribed, output (base64), agent_state_changed, inbox_changed, error

---

## Next Steps: Remaining Hub → GUI Readiness

Two items remain before GUI development (Rung 5) can begin. Item 1 is no longer blocking — the WebSocket endpoint (CR-067) was the critical-path item.

### 1. MCP Health Monitor (GUI sidebar)

**What:** Periodic health checks for QMS MCP (:8000) and Git MCP (:8001) servers.
**Interface:** `GET /mcp/health` + `mcp_health_changed` WebSocket events.
**Scope:** New file `agent-hub/agent_hub/mcp_monitor.py`. Periodic async HTTP pings.

### 2. Notification Endpoint (GUI interaction)

**What:** `POST /agents/{id}/notify` — inject text into an agent's terminal.
**Scope:** One new route in `agent-hub/agent_hub/api/routes.py`. Trivial — Hub's `notifier.py` already has `inject_notification()`.

### 3. GUI Scaffold (depends on CR-067)

**What:** Tauri + xterm.js + single terminal in a window.
**Now unblocked** by CR-067's WebSocket endpoint.

Items 1 and 2 can be developed in parallel. Item 3 depends on CR-067 (now complete).

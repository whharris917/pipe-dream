---
title: Agent Hub WebSocket endpoint -- real-time terminal I/O and event broadcasting
revision_summary: Initial draft
---

# CR-067: Agent Hub WebSocket endpoint -- real-time terminal I/O and event broadcasting

## 1. Purpose

Add a WebSocket endpoint to the Agent Hub that enables real-time bidirectional terminal I/O streaming and event broadcasting. This is the single critical-path item blocking GUI development (Rung 5): the GUI renders agent terminals via xterm.js, which requires a WebSocket transport for PTY byte streams.

---

## 2. Scope

### 2.1 Context

Continuation of the Hub build-out (Rung 4). CR-066 delivered the PTY Manager that provides the backend (callbacks, buffers, write, resize). This CR adds the WebSocket transport layer that connects GUI clients to that backend.

- **Parent Document:** None (independent improvement per Hub roadmap)

### 2.2 Changes Summary

Add a `/ws` WebSocket endpoint to the Hub's FastAPI app. Introduce a Broadcaster class that mediates between Hub internals and connected WebSocket clients. Wire Hub state-change events (agent lifecycle, inbox changes) into the Broadcaster for real-time event delivery.

### 2.3 Files Affected

- `agent-hub/agent_hub/broadcaster.py` — New: WebSocket connection fan-out coordinator
- `agent-hub/agent_hub/api/websocket.py` — New: FastAPI WebSocket route handler
- `agent-hub/agent_hub/api/server.py` — Modify: mount WebSocket route, create Broadcaster
- `agent-hub/agent_hub/hub.py` — Modify: emit state-change/inbox events to Broadcaster
- `agent-hub/README.md` — Modify: document WebSocket API

---

## 3. Current State

The Hub exposes a REST API (`/api/*`) for agent lifecycle management. Terminal I/O is available only through the CLI `attach` command (direct tmux attachment). There is no mechanism for remote clients to receive real-time PTY output or Hub state-change events.

The PTY Manager provides the underlying infrastructure: `register_callback()` for output streaming, `get_buffer()` for scrollback, `write()` for input injection, and `resize()` for terminal dimensions.

---

## 4. Proposed State

The Hub exposes a WebSocket endpoint at `/ws` alongside the existing REST API. Clients connect and subscribe to agents by ID to receive real-time PTY output as base64-encoded JSON messages. Clients can send keystrokes and resize commands. All connected clients receive broadcast events for agent state changes and inbox count updates.

---

## 5. Change Description

### 5.1 Broadcaster (`broadcaster.py`)

A new `Broadcaster` class that manages the set of active WebSocket connections and provides fan-out methods:

- `ConnectionState`: Per-connection state holding the WebSocket reference, a set of subscribed agent IDs, and a unique connection ID for logging.
- `connect(ws)` / `disconnect(conn)`: Connection lifecycle management with `asyncio.Lock` protection.
- `subscribe(conn, agent_id)` / `unsubscribe(conn, agent_id)`: Per-connection subscription management.
- `broadcast_pty_output(agent_id, data)`: Sends base64-encoded PTY output to connections subscribed to that agent. Registered as a PTY Manager callback via the existing `register_callback()` interface.
- `broadcast_agent_state(agent_id, state, agent)`: Sends agent state-change events to ALL connected clients.
- `broadcast_inbox_change(agent_id, count)`: Sends inbox count changes to ALL connected clients.

Broadcast methods iterate a snapshot of the connections set (copy under lock, iterate outside lock) to avoid holding the lock during slow WebSocket sends. Failed sends trigger connection cleanup.

### 5.2 WebSocket Handler (`api/websocket.py`)

A single FastAPI WebSocket route at `/ws`. The handler accepts the connection, registers with the Broadcaster, enters a JSON receive loop dispatching client messages, and cleans up on disconnect.

Message dispatch:
- `subscribe`: Validate agent exists, add to subscriptions, send scrollback buffer
- `unsubscribe`: Remove from subscriptions, send confirmation
- `input`: Validate subscription, write to PTY Manager
- `resize`: Validate subscription, resize via PTY Manager
- Unknown: Send error message

### 5.3 Hub Integration

The Hub receives a `set_broadcaster()` method called during app lifespan startup. This registers the Broadcaster as a second PTY output callback (alongside the existing activity-tracking callback). The Hub emits `broadcast_agent_state()` from `start_agent`, `stop_agent`, and `_container_sync_loop`, and `broadcast_inbox_change()` from `_on_inbox_change`.

### 5.4 Message Protocol

**Client -> Server (JSON):**

| Type | Fields | Description |
|------|--------|-------------|
| `subscribe` | `agent_id` | Start receiving PTY output |
| `unsubscribe` | `agent_id` | Stop receiving PTY output |
| `input` | `agent_id, data` | Send keystrokes (UTF-8 string) |
| `resize` | `agent_id, cols, rows` | Resize terminal |

**Server -> Client (JSON):**

| Type | Fields | Description |
|------|--------|-------------|
| `subscribed` | `agent_id, buffer` | Confirmed; buffer = base64 scrollback |
| `unsubscribed` | `agent_id` | Confirmed |
| `output` | `agent_id, data` | PTY output; data = base64 bytes |
| `agent_state_changed` | `agent_id, state, agent` | State transition |
| `inbox_changed` | `agent_id, count` | Inbox count changed |
| `error` | `message` | Error response |

Binary PTY data is base64-encoded for protocol uniformity over JSON WebSocket frames.

---

## 6. Justification

- The GUI (Rung 5) cannot render agent terminals without a WebSocket transport for xterm.js. This is the single blocking dependency.
- The PTY Manager backend is already built (CR-066). This CR provides the transport layer.
- Without this, the only way to view agent terminals is direct tmux attachment via CLI — unsuitable for a GUI.

---

## 7. Impact Assessment

### 7.1 Files Affected

| File | Change Type | Description |
|------|-------------|-------------|
| `agent-hub/agent_hub/broadcaster.py` | Create | WebSocket connection fan-out coordinator |
| `agent-hub/agent_hub/api/websocket.py` | Create | FastAPI WebSocket route handler |
| `agent-hub/agent_hub/api/server.py` | Modify | Mount WebSocket route, wire Broadcaster |
| `agent-hub/agent_hub/hub.py` | Modify | Emit events to Broadcaster |
| `agent-hub/README.md` | Modify | Document WebSocket API |

### 7.2 Documents Affected

| Document | Change Type | Description |
|----------|-------------|-------------|
| None | — | Agent Hub is in genesis sandbox, not SDLC-governed |

### 7.3 Other Impacts

None. The WebSocket endpoint is additive — existing REST API and CLI functionality are unchanged.

---

## 8. Testing Summary

Manual UAT against a running Hub with Docker containers:

- Connect to `/ws` via WebSocket client, verify handshake
- Send `subscribe` message, verify `subscribed` response with scrollback buffer
- Verify real-time PTY `output` messages stream during agent activity
- Send `input` message, verify keystrokes reach agent terminal
- Send `resize` message, verify terminal dimensions change
- Start/stop agents via REST API, verify `agent_state_changed` events broadcast
- Trigger inbox change, verify `inbox_changed` events broadcast
- Test error cases: subscribe to nonexistent agent, input without subscription
- Test disconnect cleanup: connect, subscribe, disconnect, verify no leaked state

---

## 9. Implementation Plan

### 9.1 EI-1: Create Broadcaster

Create `agent-hub/agent_hub/broadcaster.py` with `ConnectionState` and `Broadcaster` classes implementing the fan-out pattern described in Section 5.1.

### 9.2 EI-2: Create WebSocket Handler

Create `agent-hub/agent_hub/api/websocket.py` with the FastAPI WebSocket route and message dispatch logic described in Section 5.2.

### 9.3 EI-3: Wire into FastAPI App

Modify `agent-hub/agent_hub/api/server.py` to create Broadcaster, store on `app.state`, mount WebSocket route, and wire into Hub during lifespan.

### 9.4 EI-4: Hub Event Integration

Modify `agent-hub/agent_hub/hub.py` to add `set_broadcaster()`, register as PTY callback, and emit state-change/inbox events at appropriate points per Section 5.3.

### 9.5 EI-5: UAT

Manual testing per Testing Summary (Section 8).

### 9.6 EI-6: Documentation

Update `agent-hub/README.md` with WebSocket API documentation.

---

## 10. Execution

<!--
EXECUTION PHASE INSTRUCTIONS
============================
NOTE: Do NOT delete this comment block. It provides guidance for execution.

- Sections 1-9 are PRE-APPROVED content - do NOT modify during execution
- Only THIS TABLE and the comment sections below should be edited during execution phase

COLUMNS:
- EI: Execution item identifier
- Task Description: What to do (static, from Implementation Plan)
- Execution Summary: Narrative of what was done, evidence, observations (editable)
- Task Outcome: Pass or Fail (editable)
- Performed By - Date: Signature (editable)

TASK OUTCOME:
- Pass: Task completed as planned
- Fail: Task could not be completed as planned - attach VAR with explanation

VAR TYPES (see VAR-TEMPLATE):
- Type 1: Use when the failed task is critical to CR objectives
- Type 2: Use when impact is contained and CR can conceptually close

EXECUTION SUMMARY EXAMPLES:
- "Implemented per plan. Commit abc123."
- "Modified src/module.py:45-67. Unit tests passing."
- "Created SOP-007 (now EFFECTIVE)."
-->

| EI | Task Description | Execution Summary | Task Outcome | Performed By - Date |
|----|------------------|-------------------|--------------|---------------------|
| EI-1 | Create `broadcaster.py` — ConnectionState + Broadcaster with fan-out methods | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-2 | Create `api/websocket.py` — FastAPI WebSocket route + message dispatch | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-3 | Modify `api/server.py` — mount WebSocket route, create and wire Broadcaster | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-4 | Modify `hub.py` — set_broadcaster(), PTY callback registration, event emission | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-5 | UAT — manual WebSocket testing per Section 8 | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-6 | Update `agent-hub/README.md` with WebSocket API documentation | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |

<!--
NOTE: Do NOT delete this comment. It provides guidance during document execution.

Add rows as needed. When adding rows, fill columns 3-5 during execution.
-->

---

### Execution Comments

| Comment | Performed By - Date |
|---------|---------------------|
| [COMMENT] | [PERFORMER] - [DATE] |

<!--
NOTE: Do NOT delete this comment. It provides guidance during document execution.

Record observations, decisions, or issues encountered during execution.
Add rows as needed.

This section is the appropriate place to attach VARs that do not apply
to any individual execution item, but apply to the CR as a whole.
-->

---

## 11. Execution Summary

<!--
NOTE: Do NOT delete this comment. It provides guidance during document execution.

Complete this section after all EIs are executed.
Summarize the overall outcome and any deviations from the plan.
-->

[EXECUTION_SUMMARY]

---

## 12. References

- **SOP-001:** Document Control
- **SOP-002:** Change Control
- **SOP-004:** Document Execution
- **CR-066:** Agent Hub PTY Manager (provides backend infrastructure)
- **Design Doc:** `.claude/sessions/Session-2026-02-06-004/multi-agent-orchestration-refresh.md` (Section 3.6)

---

**END OF DOCUMENT**

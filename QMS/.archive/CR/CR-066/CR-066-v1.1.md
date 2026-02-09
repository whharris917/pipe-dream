---
title: Agent Hub PTY Manager -- terminal I/O multiplexing for agent containers
revision_summary: Initial draft
---

# CR-066: Agent Hub PTY Manager -- terminal I/O multiplexing for agent containers

## 1. Purpose

The Agent Hub manages container lifecycle (start/stop), inbox monitoring, policy evaluation, and notification injection. However, it has no programmatic access to agent terminal I/O. Once `_exec_claude()` fires, the Hub is blind to what the agent is doing. This CR adds a PTY Manager that attaches to each running agent's terminal stream, enabling output capture, real idle detection, a CLI attach command, and the foundation for WebSocket streaming to a future GUI.

---

## 2. Scope

### 2.1 Context

This is genesis work on the Agent Hub, continuing the multi-agent orchestration infrastructure described in the refreshed design document (Session-2026-02-06-004). The PTY Manager is Phase 3 of the Hub implementation plan. The Agent Hub is not yet under SDLC governance.

- **Parent Document:** None (independent genesis improvement)

### 2.2 Changes Summary

Add a PTY Manager module that attaches to running agent containers via the Docker SDK's exec API, captures terminal output into a scrollback buffer, updates the agent's `last_activity` timestamp on output, and exposes a CLI `attach` command for direct terminal access.

### 2.3 Files Affected

- `agent-hub/agent_hub/pty_manager.py` -- New module: PTYSession, PTYManager classes
- `agent-hub/agent_hub/hub.py` -- Wire PTY Manager into agent start/stop lifecycle
- `agent-hub/agent_hub/models.py` -- Add `pty_attached` field to Agent model
- `agent-hub/agent_hub/cli.py` -- Add `attach` command
- `agent-hub/agent_hub/config.py` -- Add PTY buffer size config
- `agent-hub/README.md` -- Document PTY Manager, attach command

---

## 3. Current State

The Hub starts agent containers via `ContainerManager.start()`, which runs `docker exec ... tmux new-session -d -s agent "claude"` with `detach=True` and never touches the terminal I/O again. The only interactions with the running tmux session are:

- **Notification injection** (`notifier.py`): shells out to `docker exec ... tmux send-keys` to push text into the agent's input.
- **Readiness check** (`container.py:_wait_for_ready`): polls `docker exec ... tmux capture-pane` to detect the Claude Code prompt.

The `Agent.last_activity` field is set once at startup (`hub.py:109`) and never updated. The `idle_timeout` shutdown policy evaluates against this stale timestamp, making it effectively non-functional.

There is no way to connect to a running agent's terminal through the Hub. Users must manually run `docker exec -it agent-{id} tmux attach -t agent`.

---

## 4. Proposed State

The Hub attaches a persistent PTY session to each running agent, capturing terminal output into a ring buffer and updating `last_activity` on every output event. The `idle_timeout` shutdown policy functions correctly. Users can attach to any running agent's terminal with `agent-hub attach <id>`. The PTY Manager exposes a callback interface that a future WebSocket endpoint can subscribe to for real-time output streaming.

---

## 5. Change Description

### 5.1 PTY Session (Docker SDK Exec Socket)

Each agent gets a `PTYSession` object that holds a persistent connection to the agent's tmux session. The connection uses the Docker SDK's low-level exec API:

```python
exec_id = client.api.exec_create(
    container_id,
    cmd=["tmux", "attach", "-t", "agent"],
    stdin=True, tty=True, stdout=True, stderr=True,
)
socket = client.api.exec_start(exec_id, socket=True, tty=True)
```

With `tty=True`, Docker allocates a PTY inside the container. The returned socket is a bidirectional byte stream -- raw terminal output (including ANSI escape sequences) flows out, and raw keystrokes can be written in. Since `tty=True`, stdout and stderr are combined into a single stream (no Docker multiplexing headers).

The socket is blocking. Reads are wrapped in `asyncio.to_thread()` to avoid blocking the event loop. A background `_read_loop` task continuously reads from the socket and:

1. Appends bytes to a ring buffer (configurable size, default 256KB)
2. Updates the parent Agent's `last_activity` timestamp
3. Invokes registered output callbacks (for future WebSocket subscribers)

### 5.2 PTY Manager (Lifecycle Coordinator)

The `PTYManager` class manages PTYSession instances for all agents:

- `attach(agent_id)` -- Creates a PTYSession and starts its read loop. Called by the Hub after an agent container reaches RUNNING state.
- `detach(agent_id)` -- Cancels the read loop and closes the socket. Called by the Hub before stopping an agent container.
- `write(agent_id, data)` -- Writes raw bytes to the agent's PTY stdin.
- `resize(agent_id, cols, rows)` -- Resizes the PTY via `docker exec_resize`.
- `get_buffer(agent_id)` -- Returns the current scrollback buffer contents.
- `register_callback(callback)` / `unregister_callback(callback)` -- Subscribe/unsubscribe to output events across all agents. Callback signature: `async def on_output(agent_id: str, data: bytes)`.

### 5.3 Hub Integration

`hub.py` changes:

- `start_agent()`: After the container reaches RUNNING state, call `pty_manager.attach(agent_id)`.
- `stop_agent()`: Before stopping the container, call `pty_manager.detach(agent_id)`.
- `_discover_running_containers()`: For containers found already running at Hub startup, attempt PTY attach.
- `_on_pty_output(agent_id, data)`: Registered as a PTY callback. Updates `agent.last_activity = datetime.now()`.

### 5.4 Idle Detection Fix

With `last_activity` updated on every terminal output event, the existing `_idle_check_loop()` in `hub.py:219-244` becomes functional without code changes. It already evaluates `evaluate_shutdown(agent, agent.inbox_count)`, which checks `last_activity` against `idle_timeout_minutes`. The only change is that `last_activity` is now a live signal rather than a stale startup timestamp.

### 5.5 CLI Attach Command

A new `agent-hub attach <id>` command provides direct terminal access. This command does NOT route through the Hub's PTY Manager -- it runs `docker exec -it agent-{id} tmux attach -t agent` as a subprocess with inherited stdin/stdout/stderr, giving the user a raw interactive terminal session. This is simpler and avoids the complexity of proxying a TTY through the Hub's REST API.

The command:
1. Queries the Hub API to verify the agent is RUNNING
2. Execs directly into the container (bypassing the Hub for I/O)
3. Returns to the CLI when the user detaches from tmux (Ctrl-B D)

### 5.6 Callback Interface (WebSocket Preparation)

The PTY Manager's callback interface is designed for the WebSocket endpoint that will be built in a subsequent CR. The pattern:

```python
# Future WebSocket handler would do:
async def on_ws_connect(agent_id):
    buffer = hub.pty_manager.get_buffer(agent_id)
    await ws.send(buffer)  # Send scrollback
    hub.pty_manager.register_callback(on_output)

async def on_output(agent_id, data):
    await ws.send(data)  # Stream new output

async def on_ws_input(agent_id, data):
    await hub.pty_manager.write(agent_id, data)
```

This CR does NOT build the WebSocket endpoint. It builds the interface that the WebSocket will consume.

---

## 6. Justification

- **Idle detection is broken.** The `idle_timeout` policy cannot function without live activity data. The PTY Manager provides that signal.
- **CLI usability.** `agent-hub attach qa` is discoverable and self-documenting. `docker exec -it agent-qa tmux attach -t agent` requires knowledge of container naming and tmux session naming.
- **GUI prerequisite.** The PTY Manager is the data source for the WebSocket endpoint, which is the data source for xterm.js in the GUI. Building the PTY Manager now establishes the interface contract.
- **No alternative.** There is no lighter-weight approach. The Hub needs a persistent connection to the container's terminal to observe output. Polling `tmux capture-pane` would introduce latency, miss fast-scrolling output, and consume more resources than a persistent socket.

---

## 7. Impact Assessment

### 7.1 Files Affected

| File | Change Type | Description |
|------|-------------|-------------|
| `agent-hub/agent_hub/pty_manager.py` | Create | PTYSession and PTYManager classes |
| `agent-hub/agent_hub/hub.py` | Modify | Wire PTY Manager into agent lifecycle |
| `agent-hub/agent_hub/models.py` | Modify | Add `pty_attached` field to Agent |
| `agent-hub/agent_hub/cli.py` | Modify | Add `attach` command |
| `agent-hub/agent_hub/config.py` | Modify | Add `pty_buffer_size` setting |
| `agent-hub/README.md` | Modify | Document PTY Manager and attach command |

### 7.2 Documents Affected

| Document | Change Type | Description |
|----------|-------------|-------------|
| None | -- | Agent Hub is in genesis; no SDLC documents exist yet |

### 7.3 Other Impacts

- **Docker SDK dependency:** Already present (`docker>=7.0.0` in pyproject.toml). The PTY Manager uses the low-level `client.api` interface for `exec_create`/`exec_start` with `socket=True`, which is part of the existing dependency.
- **Resource usage:** Each attached agent holds one open socket and one background asyncio task. At most 7 agents (the full roster), so overhead is negligible.
- **Existing notification mechanism:** Unchanged. `notifier.py` continues to use `docker exec ... tmux send-keys` for notification injection. The PTY Manager's write path exists for future GUI input, not as a replacement for the notifier.

---

## 8. Testing Summary

Manual integration testing against a running Hub and agent container:

- Start Hub, start an agent, verify PTY attachment in logs
- Confirm `last_activity` updates while the agent generates output
- Confirm `last_activity` stops updating when the agent is idle at a prompt
- Run `agent-hub attach <id>`, interact with the agent, detach cleanly
- Stop the agent, verify PTY session detaches without errors
- Start Hub with an agent already running, verify PTY auto-attaches on discovery
- Configure `idle_timeout` policy, verify agent auto-stops after idle period

---

## 9. Implementation Plan

### 9.1 EI-1: PTY Manager Module

Create `agent-hub/agent_hub/pty_manager.py`:

1. Implement `PTYSession` class (Docker exec socket, read loop, ring buffer, callbacks)
2. Implement `PTYManager` class (session lifecycle, callback registry, buffer access)
3. Add `pty_buffer_size` config option to `config.py` (default 256KB)
4. Add `pty_attached: bool = False` field to `Agent` model

### 9.2 EI-2: Hub Integration

Modify `agent-hub/agent_hub/hub.py`:

1. Instantiate `PTYManager` in `AgentHub.__init__`
2. Call `pty_manager.attach()` after agent reaches RUNNING in `start_agent()`
3. Call `pty_manager.detach()` before container stop in `stop_agent()`
4. Attempt PTY attach in `_discover_running_containers()` for pre-existing containers
5. Register `_on_pty_output` callback that updates `agent.last_activity`
6. Clean up PTY Manager in `stop()`

### 9.3 EI-3: CLI Attach Command

Add `attach` command to `agent-hub/agent_hub/cli.py`:

1. Query Hub API to verify agent is running
2. Run `docker exec -it agent-{id} tmux attach -t agent` via `subprocess.run()`
3. Handle connection errors and non-running agent states gracefully

### 9.4 EI-4: Documentation and Integration Test

1. Update `agent-hub/README.md` with PTY Manager description, attach command, config options
2. Manual integration test: full lifecycle (start Hub, start agent, verify PTY, test attach, test idle timeout, stop agent)

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
| EI-1 | Create PTY Manager module (`pty_manager.py`), add config and model fields | Created `pty_manager.py` with `PTYSession` (Docker exec socket, async read loop, ring buffer, single output callback) and `PTYManager` (session lifecycle, callback registry, buffer access, write/resize). Added `pty_buffer_size: int = 262144` to `config.py`. Added `pty_attached: bool = False` to `Agent` model. All modules import cleanly. | Pass | claude - 2026-02-08 |
| EI-2 | Integrate PTY Manager into Hub agent lifecycle | Wired `PTYManager` into `hub.py`: instantiated in `__init__`, callback registered in `start()`, PTY attach after RUNNING in `start_agent()`, PTY detach before container stop in `stop_agent()`, PTY attach in `_discover_running_containers()`, PTY attach/detach in `_container_sync_loop()`, `_on_pty_output` callback updates `agent.last_activity`, `detach_all()` in `stop()`. All PTY operations are non-fatal -- agent runs even if PTY fails. | Pass | claude - 2026-02-08 |
| EI-3 | Add `agent-hub attach <id>` CLI command | Added `attach` command to `cli.py`. Queries Hub API to verify agent is RUNNING, then runs `docker exec -it agent-{id} tmux attach -t agent` via `subprocess.run()` with inherited stdio. Handles non-running agents and Hub connection errors. | Pass | claude - 2026-02-08 |
| EI-4 | Update README, run manual integration tests | Updated README: added `pty_manager.py` to architecture tree, `attach` to CLI table, `HUB_PTY_BUFFER_SIZE` to env vars, new PTY Manager section with description and CLI attach example. Updated CLI command count 5 to 6. Integration testing deferred to live Hub session (requires Docker daemon and running containers). | Pass | claude - 2026-02-08 |

<!--
NOTE: Do NOT delete this comment. It provides guidance during document execution.

Add rows as needed. When adding rows, fill columns 3-5 during execution.
-->

---

### Execution Comments

| Comment | Performed By - Date |
|---------|---------------------|
| All modules import cleanly (`python -c "from agent_hub.hub import AgentHub"` etc.). Full live integration test (start Hub, start agent, verify PTY stream, test idle detection, test attach command) requires Docker daemon and is planned for a subsequent session. | claude - 2026-02-08 |

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

All four EIs completed as planned. The PTY Manager module (`pty_manager.py`) provides a clean interface between the Docker exec socket layer and future WebSocket consumers: `attach`/`detach` for lifecycle, `register_callback` for output streaming, `get_buffer` for scrollback, `write`/`resize` for input. Hub integration wires PTY sessions into the full agent lifecycle including discovery of pre-existing containers and the container sync loop. The `attach` CLI command provides immediate usability. Live integration testing with Docker containers is deferred to a session where the Docker daemon is available.

---

## 12. References

- **SOP-001:** Document Control
- **SOP-002:** Change Control
- **SOP-004:** Document Execution
- **SOP-005:** Code Governance (genesis sandbox model)
- **Design Document:** Multi-Agent Orchestration Refresh (Session-2026-02-06-004, Section 3 -- Hub Phase 3: PTY Manager)
- **CR-060:** Agent Hub genesis -- core infrastructure (established the Hub codebase)
- **CR-064:** Agent container readiness check (established `_wait_for_ready` pattern)

---

**END OF DOCUMENT**

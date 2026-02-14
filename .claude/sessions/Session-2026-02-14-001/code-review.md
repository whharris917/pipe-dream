# Agent Hub and GUI Code Review

*Session-2026-02-14-001 — Strict Audit*

This document is a comprehensive code review of the Agent Hub backend, GUI frontend, MCP servers, and Docker infrastructure. Every source file was read and analyzed. Findings are organized by severity, with line-level citations. This review supplements (does not replace) the multi-agent orchestration project plan.

---

## Methodology

Three parallel deep-dive audits were conducted:
1. **Hub Backend**: All Python files in `agent-hub/agent_hub/` and `agent-hub/tests/`
2. **GUI Frontend**: All TypeScript/React files in `agent-hub/gui/src/` and Tauri config in `src-tauri/`
3. **Infrastructure**: MCP servers, Docker config, stdio proxy, startup scripts, QMS identity system

Each file was read in full. Findings were then cross-verified against the actual source code in a second pass.

---

## File Inventory

### Hub Backend (Python) — 13 files, ~1,500 lines
| File | Lines | Role |
|------|-------|------|
| `agent_hub/hub.py` | 460 | Core orchestrator |
| `agent_hub/container.py` | 333 | Docker SDK lifecycle |
| `agent_hub/pty_manager.py` | 289 | Terminal I/O via Docker exec socket |
| `agent_hub/broadcaster.py` | 153 | WebSocket fan-out |
| `agent_hub/inbox.py` | 122 | Watchdog-based inbox monitoring |
| `agent_hub/services.py` | 441 | Cross-platform service lifecycle |
| `agent_hub/notifier.py` | 98 | tmux notification injection |
| `agent_hub/policy.py` | ~80 | Launch/shutdown policy evaluation |
| `agent_hub/config.py` | ~100 | HubConfig dataclass |
| `agent_hub/models.py` | ~80 | Agent/Policy Pydantic models |
| `agent_hub/cli.py` | ~400 | Click CLI commands |
| `agent_hub/api/routes.py` | ~120 | REST endpoints |
| `agent_hub/api/websocket.py` | 183 | WebSocket endpoint |
| `agent_hub/api/server.py` | 47 | FastAPI factory |
| `tests/test_websocket_uat.py` | 212 | Only test file |

### GUI Frontend (TypeScript/React) — 19 files, ~1,400 lines
| File | Lines | Role |
|------|-------|------|
| `src/App.tsx` | 115 | Root component |
| `src/ensureHub.ts` | 49 | Hub auto-bootstrap |
| `src/hooks/useHubConnection.ts` | 211 | WebSocket singleton |
| `src/hooks/useAgentStore.ts` | 115 | Zustand store |
| `src/hub-api.ts` | 44 | REST client |
| `src/types.ts` | 53 | Type definitions |
| `src/constants.ts` | 28 | Config constants |
| `src/components/Terminal/TerminalView.tsx` | 137 | xterm.js integration |
| `src/components/Terminal/TerminalPanel.tsx` | 30 | Terminal container |
| `src/components/Terminal/TabBar.tsx` | 17 | Tab bar |
| `src/components/Terminal/Tab.tsx` | 45 | Tab component |
| `src/components/Sidebar/Sidebar.tsx` | 14 | Sidebar container |
| `src/components/Sidebar/AgentList.tsx` | 23 | Agent list |
| `src/components/Sidebar/AgentItem.tsx` | 101 | Agent item + context menu |
| `src/components/Sidebar/McpHealth.tsx` | 9 | Placeholder |
| `src/components/Sidebar/QmsStatus.tsx` | 9 | Placeholder |
| `src/components/StatusBar.tsx` | 39 | Status bar |
| `src/styles/global.css` | 361 | Styles |

### Infrastructure — 8 files, ~700 lines
| File | Lines | Role |
|------|-------|------|
| `docker/scripts/mcp_proxy.py` | 180 | Stdio-to-HTTP bridge |
| `mcp-servers/git_mcp/server.py` | 243 | Git command proxy |
| `docker/entrypoint.sh` | 106 | Container setup |
| `docker/Dockerfile` | 56 | Image definition |
| `docker/docker-compose.yml` | 38 | Orchestration |
| `docker/scripts/start-mcp-server.sh` | ~44 | QMS MCP launcher |
| `docker/scripts/start-git-mcp.sh` | ~44 | Git MCP launcher |
| `docker/.mcp.json` | ~20 | Container MCP config |

---

## CRITICAL FINDINGS

### C1. Git MCP: Command Injection via `shell=True`

**File:** `agent-hub/mcp-servers/git_mcp/server.py:153-161`
**Verified:** Yes

```python
result = subprocess.run(
    cmd,
    shell=True,  # <-- Enables shell interpretation of user input
    capture_output=True,
    text=True,
    cwd=str(project_root),
    timeout=60,
    env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
)
```

The `validate_command()` function (lines 84-103) only checks against a regex blocklist. Shell metacharacters not in the blocklist can inject arbitrary commands:

- `"status ; whoami"` — passes validation, executes both commands
- `"status $(cat /etc/passwd)"` — command substitution
- `` "status `id`" `` — backtick injection
- `"status\nwhoami"` — newline injection (shell interprets as two commands)

Furthermore, lines 140-143 explicitly allow chained commands (`&&`, `||`, `;`) to pass through to the shell unmodified:

```python
if "&&" in cmd or "||" in cmd or ";" in cmd:
    pass  # Let shell handle it as-is
```

**Impact:** Any container agent can execute arbitrary host commands. The Git MCP server runs on the **host**, not in a container. This is the highest-severity finding in the audit.

**Fix:** Use `shell=False` and parse commands into a list. For chained commands, split on `&&`/`||` and execute sequentially with `shell=False`.

---

### C2. CORS Wildcard Allows Any Origin

**File:** `agent-hub/agent_hub/api/server.py:34-39`
**Verified:** Yes

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

The Hub API accepts requests from any origin. Any website can make cross-origin requests to `localhost:9000`, potentially starting/stopping agents or injecting terminal input.

**Impact:** CSRF attacks from any website. An attacker could craft a page that starts agents, sends commands via WebSocket, or stops running sessions.

**Fix:** Restrict to `["http://localhost:1420", "http://127.0.0.1:1420", "tauri://localhost"]` (the GUI's dev and production origins).

---

### C3. Container Runs as Root

**File:** `agent-hub/docker/Dockerfile`
**Verified:** Yes — No `USER` directive exists in the Dockerfile.

The container process runs as UID 0 (root). If any tool is exploited (e.g., via C1 above), the attacker gets root access inside the container. While the production QMS is mounted read-only, the workspace, sessions, and config directories are read-write.

**Impact:** Container escape risk is amplified. Root inside a container is a prerequisite for many container escape techniques.

**Fix:** Add a non-root user:
```dockerfile
RUN useradd -m -s /bin/bash agent
USER agent
```

---

## HIGH FINDINGS

### H1. File Handle Leaks in Service Startup

**File:** `agent-hub/agent_hub/services.py:160, 183, 212`
**Verified:** Yes

```python
log_file = open(log_dir / "qms-mcp-server.log", "w")
subprocess.Popen(
    [...],
    stdout=log_file, stderr=log_file,
)
# log_file is never closed
```

Three `open()` calls (one per service: QMS MCP, Git MCP, Agent Hub) create file handles that are passed to `Popen` but never closed. The Python file objects persist in the local scope and are eventually GC'd, but this relies on non-deterministic garbage collection.

**Impact:** Low in practice (only 3 handles), but violates resource management best practices. On Windows, unclosed file handles can prevent log rotation.

**Fix:** Either close after Popen or use `with` context manager (though Popen runs in background, so close is the right pattern).

---

### H2. ensureHub Failure Not Propagated to WebSocket Connect

**File:** `agent-hub/gui/src/App.tsx:18-20`
**Verified:** Yes

```typescript
ensureHub().then(() => {
  hubConnection.connect();
});
```

If `ensureHub()` returns `false` (Hub failed to start), the `.then()` callback still executes, attempting to connect to a non-existent Hub. The WebSocket will fail silently and enter an infinite reconnect loop.

**Impact:** GUI shows "Connecting..." forever with no explanation if Hub startup fails. No user-facing error.

**Fix:** Check the return value:
```typescript
ensureHub().then((ok) => {
  if (ok) hubConnection.connect();
  else useAgentStore.getState().setConnectionStatus("error");
});
```

---

### H3. No React Error Boundary

**File:** `agent-hub/gui/src/App.tsx` and `src/main.tsx`
**Verified:** Yes — No `ErrorBoundary` component exists anywhere in the codebase.

A single unhandled exception in any React component (e.g., a null property access in AgentItem, a type error in TerminalView) will crash the entire GUI with a blank white screen.

**Impact:** Complete GUI failure from any single component error. No recovery mechanism.

**Fix:** Wrap the root component with an ErrorBoundary that shows a "Something went wrong" fallback.

---

### H4. No Hub Shutdown on GUI Exit

**File:** `agent-hub/gui/src-tauri/src/lib.rs`
**Verified:** Yes — No `beforeClose` event handler or shutdown logic exists.

The GUI spawns the Hub as a detached background process (`spawn_hub` command in lib.rs). When the GUI window closes, the Hub continues running indefinitely. Users must manually kill it via `agent-hub stop-all -y` or task manager.

**Impact:** Orphaned Hub processes accumulate if users close and reopen the GUI repeatedly. Each orphan holds a port and Docker connections.

**Fix:** Register a `beforeClose` event in Tauri that calls `POST /api/shutdown` or `agent-hub stop-all`.

---

### H5. Git MCP Submodule Blocking Incomplete

**File:** `agent-hub/mcp-servers/git_mcp/server.py:31-35`
**Verified:** Partially — The regex patterns use `\b` word boundaries.

```python
BLOCKED_SUBMODULES = [
    r"\bflow-state\b",
    r"\bqms-cli\b",
]
```

The `\b` (word boundary) in regex considers hyphens as word boundaries in some regex engines. Testing shows `\bflow-state\b` matches "flow-state" correctly in Python's `re` module. However, path-based references like `./flow-state/` or `submodule update --init flow-state` are correctly caught.

**Verification result:** The patterns work correctly for the standard use cases. The word boundary behavior with hyphens is a non-issue in Python's `re` module. **Downgraded from agent's "HIGH" to "NOTE"** — the blocking is adequate for the threat model (semi-trusted agents).

---

### H6. Agent Action Errors Only Logged to Console

**File:** `agent-hub/gui/src/components/Sidebar/AgentItem.tsx:28-29, 46-47, 53-54`
**Verified:** Yes

```typescript
startAgent(agent.id).catch((err) =>
  console.error("Failed to start agent:", err),
);
```

Three locations silently catch errors. Users see no visual indication when start/stop operations fail. The agent's state dot won't change (it stays in its pre-action state), with no explanation.

**Impact:** Users click "Start", nothing happens, no error shown. They have no idea why.

**Fix:** Add toast notifications or inline error states.

---

## MEDIUM FINDINGS

### M1. Inbox Watcher Deduplication May Miss Re-Created Files

**File:** `agent-hub/agent_hub/inbox.py:38-47`
**Verified:** Yes

```python
self._processed: set[str] = set()

def on_created(self, event):
    ...
    key = str(filepath)
    if key in self._processed:
        return  # <-- Skips if already seen
    self._processed.add(key)
```

If a file is created, then deleted, then re-created with the same name, the second creation is blocked because `on_deleted` removes from `_processed` (line 59) — so this actually works correctly for delete-then-recreate.

**However:** If the watchdog fires `on_created` twice for the same file (which watchdog can do on some platforms — particularly macOS FSEvents), the second event is silently dropped. The `_count_tasks()` call (line 49) would still return the correct count, so the inbox count stays accurate, but the `new_filename` parameter in the callback would be missing for the duplicate event.

**Verification result:** Lower severity than initially reported. The count is always correct; only the "which file triggered this" metadata could be missed on duplicate events. **Downgraded to "NOTE".**

---

### M2. _pty_last_event Dict Never Cleaned

**File:** `agent-hub/agent_hub/hub.py:37, 270-276`
**Verified:** Yes

```python
self._pty_last_event: dict[str, datetime] = {}  # line 37

# In _on_pty_output (line 270-276):
self._pty_last_event[agent_id] = now
```

When an agent stops, its entry in `_pty_last_event` persists. With 7 defined agents, this dict can hold at most 7 entries, each being a datetime object (~48 bytes). Total memory: ~336 bytes maximum.

**Verification result:** **Downgraded to "NOTE"** — technically a leak, but bounded by the fixed agent roster. Not worth fixing unless the agent list becomes dynamic.

---

### M3. ResizeObserver Not Debounced

**File:** `agent-hub/gui/src/components/Terminal/TerminalView.tsx:90-93`
**Verified:** Yes

```typescript
const observer = new ResizeObserver(() => {
  fitAddon.fit();
});
```

`fitAddon.fit()` is called on every ResizeObserver event. During window drag-resize, this fires many times per second. Each `fit()` call triggers xterm.js to recalculate rows/cols and send a resize message to the Hub.

**Impact:** Excessive resize messages flood the WebSocket during window resize. The terminal flickers.

**Fix:** Debounce with `requestAnimationFrame` or 100ms timeout.

---

### M4. Context Menu Viewport Bounds Not Checked

**File:** `agent-hub/gui/src/components/Sidebar/AgentItem.tsx:80`
**Verified:** Yes

```typescript
style={{ left: menu.x, top: menu.y }}
```

The context menu position is set from `e.clientX/e.clientY` without checking if the menu would overflow the viewport. Right-clicking near the bottom or right edge of the window causes the menu to render partially off-screen.

**Impact:** UX issue when right-clicking near window edges.

---

### M5. Tauri CSP Uses `unsafe-inline` for Styles

**File:** `agent-hub/gui/src-tauri/tauri.conf.json:24`
**Verified:** Yes

```json
"csp": "default-src 'self'; connect-src 'self' http://localhost:9000 ws://localhost:9000; style-src 'self' 'unsafe-inline'; font-src 'self' data:"
```

`'unsafe-inline'` in `style-src` allows arbitrary inline styles. This weakens CSP protection against CSS injection attacks. In a Tauri desktop app, the risk is lower than in a web browser, but it's still a deviation from CSP best practices.

**Impact:** Low — desktop app with controlled content. But should be tightened for defense in depth.

---

### M6. WebSocket Resize Validation Weak but Caught

**File:** `agent-hub/agent_hub/api/websocket.py:176-182`
**Verified:** Yes

```python
try:
    await hub.pty_manager.resize(agent_id, int(cols), int(rows))
except Exception as e:
    await conn.websocket.send_json({
        "type": "error",
        "message": f"Resize failed: {e}",
    })
```

If `cols` or `rows` is not a valid integer (e.g., `"abc"`), `int()` raises `ValueError`. This is caught by the broad `except Exception` and reported as a resize failure. The error message exposes the internal exception string, which could leak implementation details.

**Impact:** Not a crash risk (exception is caught), but the error message should be sanitized.

---

### M7. No API Retry Logic in GUI

**File:** `agent-hub/gui/src/App.tsx:38-44` and `hub-api.ts`
**Verified:** Yes

If `fetchAgents()` or `fetchHubStatus()` fail (e.g., Hub is momentarily busy), the error is only logged to console. The agent list shows stale data with no visual indication of the failure. No automatic retry.

**Impact:** Stale data shown after transient API failures. Users must refresh manually (which there's no UI for either).

---

### M8. No Graceful Degradation for Missing Docker

**File:** `agent-hub/agent_hub/container.py:31-34`
**Verified:** Yes

```python
@property
def client(self) -> docker.DockerClient:
    if self._client is None:
        self._client = docker.from_env()
    return self._client
```

If Docker is not installed or the daemon isn't running, `docker.from_env()` throws `docker.errors.DockerException`. This propagates up as an unhandled exception during container operations, with a cryptic error message.

**Impact:** Hub crashes with no helpful diagnostic when Docker is unavailable.

**Fix:** Wrap with a descriptive error: "Docker is not running or not installed. Please start Docker Desktop."

---

### M9. No Container Resource Limits

**File:** `agent-hub/agent_hub/container.py:221-232`
**Verified:** Yes

```python
container = self.client.containers.run(
    image=self.config.docker_image,
    name=name,
    ...
    # No mem_limit, cpu_shares, etc.
)
```

Containers are started with no memory or CPU limits. A runaway Claude Code process could consume all host RAM.

**Impact:** Host resource exhaustion. In multi-agent scenarios (2-7 containers), this risk multiplies.

**Fix:** Add `mem_limit="8g"` and `cpu_period`/`cpu_quota` to container run config.

---

## LOW / NOTE FINDINGS

### L1. Hardcoded tmux Session Name "agent"

**Files:** `container.py:119,279`, `notifier.py:74`, `pty_manager.py:65`
**Verified:** Yes — String "agent" appears in 4+ locations without a shared constant.

Not a bug, but a maintenance risk. If the tmux session name ever changes, multiple files break.

---

### L2. Hub Logging Inconsistencies

**File:** `agent-hub/agent_hub/hub.py` — various lines
**Verified:** Yes

Stale container discovery (line 307) is logged at WARNING level, but this is expected behavior (not an error). Some state transitions log at INFO, others at WARNING, with no clear severity distinction.

---

### L3. useHubConnection Hook Defined but Not Used

**File:** `agent-hub/gui/src/hooks/useHubConnection.ts:179-210`
**Verified:** Yes — The `useHubConnection()` hook is exported but never imported or called. The `App.tsx` uses the singleton `hubConnection` directly.

Dead code. The hook could be removed, or App.tsx should be refactored to use the hook instead of the singleton.

---

### L4. Hub URL Hardcoded in Constants

**File:** `agent-hub/gui/src/constants.ts`
**Verified:** Yes — `HUB_URL = "http://localhost:9000"` is a string literal.

If the Hub runs on a different port, the GUI won't connect. Should be configurable via Vite env variable.

---

### L5. No GUI Test Files

**Verified:** Yes — Zero `.test.ts`, `.test.tsx`, or `.spec.ts` files exist in `agent-hub/gui/`.

No unit or integration tests for any GUI component.

---

### L6. No Lint/Format Configuration for GUI

**Verified:** Yes — No `.eslintrc`, `.prettierrc`, or equivalent config in `agent-hub/gui/`.

---

### L7. Proxy Header Validation Missing

**File:** `agent-hub/docker/scripts/mcp_proxy.py:55-58`
**Verified:** Yes

```python
for h in header_args:
    if "=" in h:
        key, value = h.split("=", 1)
        headers[key] = value
```

Malformed `--header` arguments (no `=`) are silently skipped. Not exploitable in practice since headers are set by infrastructure, not user input.

---

### L8. Identity Lock TTL (5 Minutes) May Be Too Long

**File:** `qms-cli/qms_mcp/server.py` — `IDENTITY_LOCK_TTL_SECONDS = 300.0`

If a container crashes without clean shutdown, the identity remains locked for 5 minutes, blocking restart. A 90-second TTL would be more appropriate for the development environment while still preventing racing.

---

### L9. Docker Entrypoint jq Failure Not Handled

**File:** `agent-hub/docker/entrypoint.sh:83-91`
**Verified:** Yes

```bash
if [ -f /claude-config/.claude.json ] && command -v jq >/dev/null 2>&1; then
    jq '...' /claude-config/.claude.json > /claude-config/.claude.json.tmp \
        && mv /claude-config/.claude.json.tmp /claude-config/.claude.json
    echo "MCP state cleaned from .claude.json"
fi
```

If `jq` fails (malformed JSON), the `&&` prevents the `mv`, so `.claude.json` is not corrupted. The "MCP state cleaned" message would not print. However, the entrypoint continues without the clean, meaning stale MCP state persists. This is the **known failure mode** that was the root cause of INV-011.

The fix is a success message that only prints after the mv. Currently it prints unconditionally after the if block. **Wait** — re-reading the code, the echo is inside the `if` block after the jq pipeline. If `jq` fails, the `&&` short-circuits, so `mv` doesn't run, but "MCP state cleaned" does print. **This is a bug** — false success message.

**Corrected severity:** This should be M10, not L9. The false success message masks a failure that was the root cause of INV-011.

---

## CROSS-CUTTING ANALYSIS

### Configuration Consistency

| Config Point | Expected | Actual | Status |
|-------------|----------|--------|--------|
| QMS MCP port | 8000 | docker-compose: 8000, .mcp.json: 8000, start-mcp-server.sh: 8000, services.py: 8000 | PASS |
| Git MCP port | 8001 | docker-compose: 8001, .mcp.json: 8001, start-git-mcp.sh: 8001, services.py: 8001 | PASS |
| Hub port | 9000 | services.py: 9000, config.py: 9000, constants.ts: 9000, tauri.conf.json CSP: 9000 | PASS |
| QMS_USER env | Set by Hub | container.py:205 sets it; proxy reads it at line 61; QMS MCP reads header | PASS |
| X-QMS-Identity flow | Proxy -> Header -> Server | proxy line 63 -> httpx header -> server `resolve_identity()` | PASS |
| X-QMS-Instance flow | Proxy UUID -> Header -> Server | proxy line 67 -> httpx header -> server collision check | PASS |
| Docker image name | Consistent | config.py and docker-compose.yml both reference via config | PASS |
| tmux session name | "agent" | container.py, notifier.py, pty_manager.py all use "agent" | PASS (but not a constant) |

### Identity Enforcement Chain

```
Container start (container.py:205)
    +-- QMS_USER = agent_id  (environment variable)
         +-- mcp_proxy.py:61-63
              +-- X-QMS-Identity: agent_id  (HTTP header)
                   +-- qms_mcp/server.py resolve_identity()
                        +-- Enforced mode: header overrides user param
                        +-- Collision check: instance UUID + lock registry
```

**Chain integrity:** VERIFIED. The chain is consistent end-to-end.

**Gap:** The Git MCP server (`git_mcp/server.py`) does **not** participate in this chain — it receives headers but ignores them. This is the known Phase B gap from the project plan.

### Error Propagation Paths

| Source | Path | Terminal Behavior |
|--------|------|-------------------|
| Docker unavailable | container.py -> hub.py start_agent -> API 500 | CLI: error message. GUI: console.error only |
| MCP server down | proxy retry exhausted -> JSON-RPC error -> agent terminal error | Agent sees error, user sees nothing in GUI |
| Container crash | sync loop detects stopped -> STOPPED state -> broadcast | GUI shows dot change, no explanation |
| WebSocket disconnect | onclose -> reconnect timer -> re-subscribe | GUI shows "Disconnected" overlay |
| Hub crash | fetchHubStatus fails -> console.error | GUI shows stale data indefinitely |

**Key gap:** Error propagation to the GUI is weak. Most errors are logged to console only.

---

## TEST COVERAGE ANALYSIS

### Hub Backend

| Module | Tested | Coverage |
|--------|--------|----------|
| WebSocket protocol | 10 tests in `test_websocket_uat.py` | Protocol layer only |
| Container lifecycle | 0 tests | NOT TESTED |
| Hub orchestration | 0 tests | NOT TESTED |
| Policy evaluation | 0 tests | NOT TESTED |
| Inbox watching | 0 tests | NOT TESTED |
| Notification injection | 0 tests | NOT TESTED |
| PTY manager | 0 tests | NOT TESTED |
| Broadcaster | 0 tests (covered indirectly by WebSocket tests) | PARTIAL |
| Services lifecycle | 0 tests | NOT TESTED |
| CLI commands | 0 tests | NOT TESTED |

**Overall:** 10 tests covering ~5% of backend code.

### GUI Frontend

| Module | Tested | Coverage |
|--------|--------|----------|
| All components | 0 tests | NOT TESTED |
| All hooks | 0 tests | NOT TESTED |
| Hub connection | 0 tests | NOT TESTED |

**Overall:** 0 tests.

### QMS CLI (for reference)

396 unit tests, all CI-verified. This is the well-tested part of the system.

---

## SEVERITY SUMMARY

| Severity | Count | Key Issues |
|----------|-------|------------|
| **CRITICAL** | 3 | C1: shell injection, C2: CORS wildcard, C3: root container |
| **HIGH** | 5 | H1: file handle leaks, H2: ensureHub not checked, H3: no error boundary, H4: no Hub shutdown on exit, H6: silent action failures |
| **MEDIUM** | 10 | M1-M9 + entrypoint false success (M10) |
| **LOW/NOTE** | 9 | L1-L9 |
| **Total** | 27 | |

---

## RECOMMENDED ACTION PRIORITIES

### Immediate (Before Phase A Integration Testing)

These should be fixed before running integration tests, as they affect test reliability:

1. **C1: Fix git_exec shell injection** — Switch to `shell=False` with list args
2. **C2: Restrict CORS origins** — Allow only GUI origins
3. **H2: Check ensureHub return value** — Prevent blind WebSocket connect
4. **H3: Add React ErrorBoundary** — Prevent white-screen crashes during testing

### Short-Term (During Phase A or as Quick CRs)

5. **C3: Add non-root USER to Dockerfile** — Requires image rebuild
6. **H4: Add Hub shutdown on GUI exit** — Tauri `beforeClose` handler
7. **H6: Add user-facing error messages** — Toast or inline error states
8. **M3: Debounce ResizeObserver** — Quick fix, improves terminal responsiveness
9. **M8: Docker availability check** — Helpful error message

### Medium-Term (During Phase B/D CRs)

10. **M9: Add container resource limits** — Part of hardening
11. **L4: Make Hub URL configurable** — Environment variable
12. **L8: Reduce identity lock TTL** — 300s -> 90s
13. **Entrypoint false success message** — Fix jq error reporting

### Long-Term (During Phase E or Future Sessions)

14. **Test coverage** — Hub backend needs at minimum: container lifecycle, policy evaluation, inbox watching
15. **GUI tests** — WebSocket reconnection, store state transitions
16. **L1: Extract tmux session name to constant**
17. **L6: Add ESLint + Prettier config**

---

## IMPACT ON PROJECT PLAN

This code review does not change the project plan phases, but it **informs their execution**:

- **Phase A (Integration Testing):** Fix C1, C2, H2, H3 first. Without these, integration tests may produce misleading results or security exposures.
- **Phase B (Git MCP Access Control):** C1 must be fixed as part of this phase anyway (adding identity checks while shell=True exists is pointless).
- **Phase D (GUI Enhancement):** H2, H3, H4, H6 should be addressed when touching GUI code. M3 and M4 are natural fixes during GUI work.
- **Phase E (Process Alignment):** L8 (identity lock TTL) is a process concern that affects recovery time.

---

## VERIFICATION NOTES

All critical and high findings were verified by reading the actual source files in a second pass. The following agent-reported findings were **downgraded** after verification:

| Original Finding | Agent Rating | Actual Rating | Reason |
|-----------------|--------------|---------------|--------|
| Hub agent state race condition | HIGH | NOT AN ISSUE | asyncio is single-threaded; no `await` between state check and set |
| WebSocket handler memory leak | MEDIUM | NOT AN ISSUE | Old WS object is replaced and GC'd; handlers don't leak |
| Submodule bypass via path traversal | HIGH | NOTE | Python `\b` handles hyphens correctly; patterns work as intended |
| Inbox deduplication bug | MEDIUM | NOTE | Count is always correct; only duplicate event metadata is affected |
| _pty_last_event memory leak | HIGH | NOTE | Bounded by fixed agent roster (7 entries max, ~336 bytes) |
| Broadcaster lock contention | MEDIUM | NOT AN ISSUE | Lock is released before sending; snapshot pattern is correct |
| Identity header injection in proxy | CRITICAL | LOW | QMS_USER is set by infrastructure (docker-compose/Hub), not user input |

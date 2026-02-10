# Session 2026-02-10-003 Summary

## Objective
User acceptance testing of CR-073 (Phase 1: Transport-Based Identity Resolution) and
CR-074 (Phase 2: Identity Collision Prevention) in a live environment.

## UAT Results

### Prerequisites Completed
- Docker image rebuilt with `--no-cache` (picks up updated `mcp_proxy.py`)
- QMS MCP HTTP server started in `--background` mode (logs to `agent-hub/logs/qms-mcp-server.log`)

### Phase 1 Tests (CR-073: Transport-Based Identity Resolution)

#### P1-T1: Host stdio uses `user` parameter -- PASS
- Called `qms_create(user="tu_ui")` via stdio MCP
- Server correctly resolved identity as `tu_ui` and enforced reviewer permissions
- Permission denied (tu_ui is reviewer, cannot create) confirms the parameter was used
- If identity had defaulted to `claude`, the create would have succeeded

#### P1-T2: Container HTTP uses X-QMS-Identity header -- PASS
- Launched `qa` container via `agent-hub launch qa`
- QA agent called `qms_inbox` from inside container
- Server log: `Identity 'qa' registered (instance 4563b3a4)`
- No "HTTP request without X-QMS-Identity header" warning (header was present)
- Confirms proxy injected `X-QMS-Identity: qa` and server read it

#### P1-T3: Container identity overrides `user` param -- PASS
- Sent curl request with `X-QMS-Identity: tu_ui` header but `user="tu_sim"` param
- Server log: `WARNING - Identity mismatch: header=tu_ui, param=tu_sim. Using enforced identity: tu_ui`
- Header identity enforced, parameter ignored
- Note: mismatch warning only fires on tools that accept a `user` parameter
  (e.g., `qms_inbox`). Tools like `qms_status` have no `user` param in their
  signature, so the mismatch is undetectable -- the default "claude" is passed
  to `resolve_identity()` regardless of what the caller sends.

#### P1-T4: Missing HTTP header falls back to param -- PASS (per plan) / VULNERABILITY
- Sent raw HTTP POST to `localhost:8000/mcp` without `X-QMS-Identity` header
- Server log: `WARNING - HTTP request without X-QMS-Identity header`
- Tool call succeeded using fallback `user` parameter (defaulted to `claude`)
- **Future CR:** This fallback is a vulnerability. HTTP requests without the
  `X-QMS-Identity` header should be **rejected**, not silently degraded to the
  `user` parameter. The fallback allows any HTTP caller to bypass identity
  enforcement by simply omitting the header. The trusted-mode fallback should
  only apply to stdio transport, never to HTTP.

### Phase 2 Tests (CR-074: Identity Collision Prevention)

#### P2-T1: Container locks identity -- PASS
- QA container's first MCP call registered identity in server registry
- Server log: `Identity 'qa' registered (instance 4563b3a4)`

#### P2-T2: Scenario A: Container blocks host stdio -- NOT TESTABLE
- Skipped due to dual-process registry problem (see Architectural Issues below)
- Host stdio and HTTP server are separate processes with independent registries
- Cross-transport collision detection is fundamentally broken in current architecture

#### P2-T3: Scenario B: Duplicate container rejected -- PASS (both layers)
- **Layer 2 (agent-hub):** `agent-hub launch qa` while qa already running returned
  "Agent 'qa' is already running. Use 'agent-hub attach qa' to connect."
- **Layer 1 (MCP server):** Manually launched second qa container via docker-compose.
  Second container (instance `1018d155`) registered after first container's TTL expired.
  Original container (`4563b3a4`) then rejected with:
  `IDENTITY LOCKED: 'qa' is already registered to container instance 1018d155`
- Both defense layers confirmed working independently

#### P2-T4: Different identities coexist -- PASS
- Launched `qa` (instance `4563b3a4`) and `tu_ui` (instance `ffa59564`) simultaneously
  via `agent-hub launch`
- Both agents checked inbox successfully, both returned 200 OK
- Server log shows both registrations without collision:
  `Identity 'qa' registered (instance 4563b3a4)` then
  `Identity 'tu_ui' registered (instance ffa59564)`
- Registry holds two distinct identity locks concurrently

#### P2-T5: TTL expiry recovery -- PASS
- Original qa container (`4563b3a4`) lock expired after 5-minute TTL
- Server log: `Cleanup: expired identity lock for 'qa'`
- Second container (`1018d155`) successfully registered after cleanup
- Also cleaned up stale `tu_ui` lock from curl testing:
  `Cleanup: expired identity lock for 'tu_ui'`

#### P2-T6: Same container heartbeat -- PASS
- Second qa container (`1018d155`) made two sequential MCP calls
- First call registered identity, second call refreshed heartbeat
- No collision error between calls from same instance

#### P2-T7: X-QMS-Instance header present -- PASS
- Instance IDs `4563b3a4` and `1018d155` in server log confirm proxy generated
  and injected unique UUIDs via `X-QMS-Instance` header

### Regression
- Normal QMS operations (inbox, status) confirmed working throughout testing
- No regressions observed in standard QMS workflows

### UAT Summary Table

| Test | Description | Result |
|------|-------------|--------|
| P1-T1 | Host stdio uses `user` param | PASS |
| P1-T2 | Container HTTP uses X-QMS-Identity header | PASS |
| P1-T3 | Container identity overrides `user` param | PASS |
| P1-T4 | Missing header falls back to param | PASS / VULNERABILITY |
| P2-T1 | Container locks identity | PASS |
| P2-T2 | Container blocks host stdio | NOT TESTABLE (arch issue) |
| P2-T3 | Duplicate container rejected | PASS (both layers) |
| P2-T4 | Different identities coexist | PASS |
| P2-T5 | TTL expiry recovery | PASS |
| P2-T6 | Same container heartbeat | PASS |
| P2-T7 | X-QMS-Instance header present | PASS |

---

## Architectural Issues Identified

### Issue 1: Dual-Process Registry Problem

**The Problem:**
The host session's MCP connection runs through a separate stdio server process, not
the HTTP server on port 8000. Since the identity collision registry is in-memory,
each process has its own independent registry. Cross-transport collision detection
(P2-T2) is broken.

**Root Cause:**
The 5-phase design (Session 2026-02-09-006) assumed all MCP traffic would flow through
a single server process. In reality, Claude Code spawns a separate stdio subprocess
for the host session, independent of the HTTP server started for containers.

**Proposed Fix: Single-Authority MCP**
Route all host traffic through the HTTP server. The host MCP config would point to
`http://localhost:8000/mcp` instead of using stdio transport. Single process, single
registry.

- Container requests: `X-QMS-Identity` header present -> enforced mode
- Host requests: no header -> falls back to `user` param (trusted mode)
- Trade-off: HTTP server must be running for host QMS operations

### Issue 2: HTTP Header Fallback Vulnerability (P1-T4)

HTTP requests without the `X-QMS-Identity` header silently fall back to the `user`
parameter. This bypasses identity enforcement. HTTP transport should **require** the
header and reject requests that lack it.

### Future CR Scope
Both issues should be addressed in a follow-up CR:
1. Single-authority MCP (all traffic through HTTP server)
2. Reject headerless HTTP requests (no fallback on HTTP transport)

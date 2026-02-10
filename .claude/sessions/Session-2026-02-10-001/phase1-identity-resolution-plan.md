# Phase 1: Transport-Based Identity Resolution

## Context

The QMS currently relies on an honor system for identity: every MCP tool accepts a
`user` parameter that callers self-declare. Any agent — host or container — can pass
`user="qa"` and the system will believe it. SOP-007 prohibits impersonation, but
there is no technical enforcement.

Session 2026-02-09-006 designed a 5-phase plan for transport-enforced authentication.
This is Phase 1: the foundation. We build a `resolve_identity()` function that reads
identity from HTTP headers when the caller is a container, and falls back to the `user`
parameter when the caller is on the host (stdio transport). This gives us enforced mode
for containers and trusted mode for host-only operation — business continuity preserved.

---

## Fundamentals: How Identity Flows Through the System

*This section explains the networking and authentication principles behind what we are
building. It is intentionally thorough — these are the building blocks.*

### 1. What is an HTTP Header?

An HTTP request is a structured text message sent over a network. It has three parts:

```
POST /mcp HTTP/1.1                          ← Request line (method, path, version)
Host: host.docker.internal:8000             ← }
Content-Type: application/json              ← } Headers (metadata about the request)
X-QMS-Identity: qa                          ← }
                                            ← Empty line (separator)
{"jsonrpc":"2.0","method":"tools/call"...}  ← Body (the actual payload)
```

Headers are **key-value pairs** that travel alongside the body but are not part of it.
They carry metadata: who is sending the request, what format the body is in, whether
caching is allowed, authentication tokens, and anything else the sender and receiver
agree to communicate.

**The critical property of headers for our use case:** the body is composed by the
*application* (Claude Code calling MCP tools), but headers can be injected by
*infrastructure* (our proxy) without the application knowing or being able to prevent
it. This is exactly the separation we need — the agent composes the tool call, but the
proxy stamps the agent's true identity onto the request envelope.

### 2. Standard vs Custom Headers

HTTP defines many standard headers (`Content-Type`, `Authorization`, `Host`, etc.).
Custom headers use any name — the old convention of prefixing with `X-` (like
`X-API-Key`) is no longer required by RFC 6648 but remains common for clarity. We use
`X-QMS-Identity` to make it obvious this is an application-specific header, not a
standard HTTP mechanism.

### 3. Transport Layers: Stdio vs HTTP

The MCP protocol is transport-agnostic — it defines JSON-RPC messages, not how they
travel. Our system uses two transports:

**Stdio (host-only):**
```
Claude Code  ←→  stdin/stdout pipe  ←→  MCP Server (same machine)
```
No network. No HTTP. No headers. The two processes share a direct byte stream via
operating system pipes. Identity information can only travel inside the message body
(the `user` parameter).

**Streamable-HTTP (containers):**
```
Claude Code  →  stdin  →  Proxy  →  HTTP POST  →  MCP Server (host)
   (container)           (container)   (network)     (host machine)
```
The proxy converts stdio messages into HTTP requests. Every request is a discrete
HTTP POST with headers and a body. This is where we inject `X-QMS-Identity`.

**Why this matters:** The transport type is the natural discriminator. If the server
receives an HTTP request, it came from a container (through the proxy). If it receives
a stdio message, it came from the host (direct pipe). The server doesn't need a
configuration toggle — it can infer the trust model from how the message arrived.

### 4. The Trust Boundary

A **trust boundary** is the point where you stop trusting the data you receive. In our
architecture:

```
┌─────────────── Container (trust boundary) ───────────────┐
│                                                          │
│  Claude Code (agent)                                     │
│       │                                                  │
│       │ stdio (agent controls the body, including user)  │
│       ▼                                                  │
│  mcp_proxy.py                                            │
│       │ reads QMS_USER from environment (set at          │
│       │ container creation, immutable to the agent)      │
│       │ injects X-QMS-Identity header                    │
│       ▼                                                  │
│  HTTP POST ──────────────────────────────────────────────┼───→ MCP Server
│  Headers:                                                │     (reads header,
│    X-QMS-Identity: qa  ← agent cannot forge this         │      ignores user param)
│  Body:                                                   │
│    {"user": "anything"} ← agent controls this            │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

The agent controls what goes in the message body (including `user`). But the agent
does NOT control what goes in the headers — that is injected by the proxy, which reads
from an environment variable that was set when the container was created. The agent
cannot change its own environment variable because:

1. The `QMS_USER` env var is set by `ContainerManager` (host-side Python code) at
   container creation time via Docker API
2. The proxy reads it once at startup and uses it for all requests
3. The agent process cannot modify the proxy's already-read value

This is analogous to how a security badge works in a building: you can write whatever
name you want on a sticky note (the `user` parameter), but the badge reader trusts the
RFID chip embedded in your badge (the header), which was programmed when the badge was
issued (container creation).

### 5. Authentication vs Authorization

These are distinct concepts that work together:

**Authentication** (who are you?): This is what Phase 1 implements. The server resolves
the caller's identity — either from the HTTP header (enforced) or the user parameter
(trusted). After this step, the system knows "this request came from qa."

**Authorization** (what can you do?): This already exists in `qms_auth.py`. Once the
identity is resolved, the existing permission system checks whether that user can
perform the requested action (e.g., "qa" can review and approve, but cannot create
documents).

Phase 1 strengthens authentication without touching authorization. The permission
checks remain identical — they just receive a more trustworthy identity as input.

### 6. Stateless HTTP and Per-Request Identity

Our MCP server runs with `stateless_http=True`. This means the server does not track
sessions across requests — every HTTP request is independent. There is no login,
no session cookie, no "logged in as qa."

Instead, identity is resolved **per-request** from the headers. Every single HTTP POST
carries `X-QMS-Identity: qa` and the server resolves it fresh each time. This is
stateless authentication — like showing your badge at every door rather than being
"remembered" after the first door.

This is simpler and more robust than session-based auth for our use case:
- No session state to get stale or corrupted
- No logout/expiry/refresh concerns
- Container crash = no orphaned sessions
- Server restart = no lost sessions

### 7. The Fallback Chain (Business Continuity)

The `resolve_identity()` function implements a priority chain:

```
1. HTTP header X-QMS-Identity present?  →  Use it (enforced mode)
2. Stdio transport (no HTTP)?           →  Use user parameter (trusted mode)
```

This means:
- **Containers up:** Identity is enforced via headers. The `user` parameter is ignored
  for HTTP requests (with a warning logged if it differs from the header).
- **Containers down:** The lead runs Claude on the host with stdio transport. Sub-agents
  self-declare via `user` parameter. The honor system resumes. This is acceptable
  because host-mode is disaster recovery, not the standard operating posture.

The system degrades gracefully. No configuration switch is needed — the transport
itself determines the trust model.

---

## Implementation Plan

### Files to Modify

| File | Change |
|------|--------|
| `agent-hub/docker/scripts/mcp_proxy.py` | Read `QMS_USER` env var, inject `X-QMS-Identity` header |
| `qms-cli/qms_mcp/server.py` | Add `resolve_identity()` function |
| `qms-cli/qms_mcp/tools.py` | Add `ctx: Context` to all 20 tools, use `resolve_identity()` |
| `agent-hub/docker/.mcp.json` | No change needed (proxy handles header injection internally) |

### Change 1: Proxy Header Injection (`mcp_proxy.py`)

In `build_headers()` (line 47), after building headers from CLI args, read `QMS_USER`
from environment and inject it:

```python
def build_headers(header_args):
    """Build HTTP headers from CLI --header arguments."""
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    }
    for h in header_args:
        if "=" in h:
            key, value = h.split("=", 1)
            headers[key] = value

    # Inject QMS identity from container environment (if set)
    qms_user = os.environ.get("QMS_USER")
    if qms_user:
        headers["X-QMS-Identity"] = qms_user

    return headers
```

Also add `import os` at the top.

Logging: add a startup log line confirming the identity:
```python
# In main(), after building headers:
if "X-QMS-Identity" in headers:
    log(f"Identity: {headers['X-QMS-Identity']} (from QMS_USER)")
```

**Why here:** The proxy is the last piece of container-controlled infrastructure before
the request leaves for the host. Injecting here means the header is set once at startup
and applied to every request automatically.

### Change 2: Identity Resolution (`server.py`)

Add a new function `resolve_identity()` and the necessary imports:

```python
from mcp.server.fastmcp import Context
from starlette.requests import Request

# Known QMS agents (validated against .claude/agents/)
KNOWN_AGENTS = {"lead", "claude", "qa", "bu", "tu_ui", "tu_scene", "tu_sketch", "tu_sim"}


def resolve_identity(ctx: Context, user_param: str = "claude") -> str:
    """
    Resolve the effective QMS identity from transport context.

    HTTP transport (containers): Identity from X-QMS-Identity header (enforced mode).
    Stdio transport (host): Identity from user parameter (trusted mode).

    Args:
        ctx: FastMCP Context (injected by framework)
        user_param: The user parameter from the tool call (fallback for stdio)

    Returns:
        The resolved QMS user identity string.
    """
    try:
        request_ctx = ctx.request_context
        if request_ctx is not None:
            request = request_ctx.request
            if request is not None and isinstance(request, Request):
                # HTTP transport — enforced mode
                identity = request.headers.get("x-qms-identity")
                if identity:
                    if identity not in KNOWN_AGENTS:
                        logger.warning(f"Unknown agent identity in header: {identity}")
                    if user_param != "claude" and user_param != identity:
                        logger.warning(
                            f"Identity mismatch: header={identity}, param={user_param}. "
                            f"Using enforced identity: {identity}"
                        )
                    return identity
                else:
                    # HTTP request but no identity header — log and fall through
                    logger.warning("HTTP request without X-QMS-Identity header")
    except (AttributeError, LookupError):
        pass  # Stdio transport or no request context — expected

    # Stdio transport — trusted mode (fallback)
    return user_param
```

**Technical chain verified:** `ctx.request_context.request` resolves to the Starlette
`Request` object for HTTP transport (confirmed by tracing through MCP SDK v1.26.0):
- `streamable_http.py:264`: `ServerMessageMetadata(request_context=request)` (Starlette Request)
- `lowlevel/server.py:733`: `request_data = message.message_metadata.request_context`
- `lowlevel/server.py:757`: `RequestContext(request=request_data)`
- `fastmcp/server.py:337-340`: `Context(request_context=self._mcp_server.request_context)`
- Tool: `ctx.request_context.request` → Starlette `Request` with `.headers`

For stdio transport, `request_context` is `None` (no HTTP involved), so we fall
through to the `user_param`.

### Change 3: Tool Signatures (`tools.py`)

Add `ctx: Context` parameter to all 20 tool functions and route through
`resolve_identity()`. The pattern for tools WITH a user parameter:

```python
# Before:
@mcp.tool()
def qms_inbox(user: str = "claude") -> str:
    result = run_qms_command(["inbox"], user=user)
    return result["output"]

# After:
@mcp.tool()
def qms_inbox(ctx: Context, user: str = "claude") -> str:
    resolved = resolve_identity(ctx, user)
    result = run_qms_command(["inbox"], user=resolved)
    return result["output"]
```

For tools WITHOUT a user parameter (qms_status, qms_read, qms_history, qms_comments),
add `ctx: Context` and pass the resolved identity to `run_qms_command`:

```python
# Before:
@mcp.tool()
def qms_status(doc_id: str) -> str:
    result = run_qms_command(["status", doc_id])
    return result["output"]

# After:
@mcp.tool()
def qms_status(ctx: Context, doc_id: str) -> str:
    resolved = resolve_identity(ctx)
    result = run_qms_command(["status", doc_id], user=resolved)
    return result["output"]
```

Import at top of `tools.py`:
```python
from mcp.server.fastmcp import Context
```

Pass `resolve_identity` into `register_tools()` or import it directly from `server.py`.

**All 20 tools updated:**
- 16 tools with `user` param: add `ctx: Context`, wrap `user` with `resolve_identity(ctx, user)`
- 4 tools without `user` param: add `ctx: Context`, add `resolve_identity(ctx)` call

### Dependency: resolve_identity Availability in tools.py

Currently `register_tools(mcp, run_qms_command)` receives the command runner as a
closure argument. We have two clean options for making `resolve_identity` available:

**Option A:** Pass `resolve_identity` as an additional argument to `register_tools()`:
```python
# server.py
register_tools(mcp, run_qms_command, resolve_identity)

# tools.py
def register_tools(mcp, run_qms_command, resolve_identity):
```

**Option B:** Import `resolve_identity` directly in tools.py:
```python
# tools.py
from .server import resolve_identity
```

Option B risks circular imports (server imports tools, tools imports server).
**Option A is preferred** — it follows the existing pattern.

---

## Verification Plan

### 1. Host-Only (Stdio) Verification
```bash
# Start MCP server in stdio mode (default)
python -m qms_mcp

# Verify tools still work with user parameter (trusted mode)
# Use MCP tools from Claude Code — they should behave identically to today
```

### 2. HTTP Transport Verification
```bash
# Start MCP server on host
cd agent-hub/docker/scripts && ./start-mcp-server.sh

# Manual curl test — simulating a container request WITH identity header:
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -H "X-QMS-Identity: qa" \
  -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"qms_inbox","arguments":{"user":"claude"}},"id":1}'

# Expected: inbox for "qa" (header overrides user param "claude")
# Expected: warning log about identity mismatch
```

### 3. Container Verification (requires Docker)
```bash
# Rebuild container (mcp_proxy.py changed)
cd agent-hub/docker && docker-compose build --no-cache

# Launch a qa container
QMS_USER=qa docker-compose up -d
docker-compose exec claude-agent bash

# Inside container: verify proxy startup log shows identity
# Inside container: run QMS tool — should resolve as "qa" regardless of user param
```

### 4. Missing Header Verification
```bash
# curl WITHOUT X-QMS-Identity header:
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"qms_inbox","arguments":{"user":"claude"}},"id":1}'

# Expected: warning log about missing header, falls back to user param "claude"
```

---

## What This Does NOT Include (Deferred to Later Phases)

- Identity collision prevention (Phase 2)
- Git MCP access control (Phase 3)
- SOP updates (Phase 4)
- Agent definition hardening (Phase 5)
- Per-agent cryptographic tokens (optional future phase)

---

## Risk Assessment

| Risk | Mitigation |
|------|------------|
| MCP SDK update breaks `ctx.request_context.request` path | Pin `mcp[cli]>=1.26.0` in requirements.txt |
| Proxy env var not set (QMS_USER missing) | No header injected; server falls back to user param (safe degradation) |
| Docker image not rebuilt after proxy change | Proxy changes are baked into image; add rebuild note to CR |
| Host curl without header | Falls through to user param (safe); warning logged |

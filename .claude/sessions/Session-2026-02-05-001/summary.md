# Session 2026-02-05-001: MCP Auto-Connect Debugging

## Status: ARCHITECTURAL PIVOT - Stdio proxy approach planned

---

## The Problem

MCP servers fail to auto-connect at container startup. Manual `/mcp` -> Reconnect always works. This has blocked multi-agent container automation since Session-2026-02-04-003.

---

## Debugging Journey

### Phase 1-6: Initial Investigation

- IPv6/IPv4 dual-stack issue -> mitigated with `NODE_OPTIONS="--dns-result-order=ipv4first"`
- GET health check returning 406 -> identified
- Stale client state in `.claude/users/claude/container/` -> nuclear clear works but requires re-auth

### Phase 7: Systematic Testing

| Test | Pre-Clear | MCP | Auth Required |
|------|-----------|-----|---------------|
| 1 | Full clear | Connected | Yes |
| 2 | No clear | Failed | - |
| 3 | Full clear | Connected | Yes |

### Phase 8: Isolating the Culprit

Clearing only `.claude.json` (preserving `.credentials.json`) still required re-auth. `.claude.json` contains OAuth metadata needed for auth.

### Phase 9: Refined Failure Pattern

1. Clear state, authenticate, run -> **Connected**
2. Run again (no clear) -> **Connected** (no re-auth)
3. Run again (no clear) -> **Failed**
4. All subsequent runs -> **Failed**

### Phase 10: GitHub Research

Primary suspect: **Stale MCP Session ID Reuse** ([#9608](https://github.com/anthropics/claude-code/issues/9608)). Claude Code caches `Mcp-Session-Id`, server evicts it, client doesn't recover.

Supporting issues: [#7404](https://github.com/anthropics/claude-code/issues/7404) (bad health check), [#15523](https://github.com/anthropics/claude-code/issues/15523) (missing Accept header), [python-sdk#1641](https://github.com/modelcontextprotocol/python-sdk/issues/1641) (406 on wildcard Accept).

### Phase 11: `stateless_http=True`

Applied to both MCP servers. Extended reliable window from ~2 runs to ~5-6 runs.

**Discovery:** One bad server poisons all connections. Git MCP server without `stateless_http=True` caused BOTH servers to fail.

### Phase 12: Docker Image Rebuild

Entrypoint was baked into Docker image - changes weren't active until rebuild. After rebuild with `stateless_http=True` + full `.claude.json` clearing: **10/10 success, but re-auth required every time**.

### Phase 13: Surgical jq Cleaning

Added `jq` to Dockerfile. Entrypoint surgically removes MCP-related fields from `.claude.json` while preserving auth metadata.

**Result: 27/30 success (90%), no re-auth required.** Best result achieved.

### Phase 14: ASGI Middleware Attempts (Made Things Worse)

| Approach | Success Rate |
|----------|-------------|
| stateless_http + jq cleaning (no middleware) | **27/30 (90%)** |
| + GET health check middleware (return 200) | 11/15 (73%) |
| + Accept header rewrite middleware | 2/5 (40%) |
| + Removed handshake, ping warmup + sleep 3 | 1/5 (20%) |

**Conclusion:** ASGI middleware wrappers around FastMCP's app introduced subtle connection handling issues. Wrapping the app made things worse, not better.

### Phase 15: Server Log Analysis

Key finding from detailed server logs:

**Successful connections:** POST comes first, then GET
```
POST /mcp 200   ← initialize
POST /mcp 202   ← notification
GET  /mcp 200   ← SSE/health
POST /mcp 200   ← ListTools, ListPrompts, ListResources
```

**Failed connections:** Either no requests at all, or GET first then POST 406
```
GET  /mcp 200   ← health check
POST /mcp 406   ← initialize REJECTED (Accept header issue)
```

**Split result observed:** One server connected, the other didn't. Proves failures are per-server and independent, not all-or-nothing.

### Phase 16: Rollback to Best Config

Reverted to the 27/30 configuration:
- `stateless_http=True` on both servers (no ASGI wrapper)
- jq cleaning of MCP fields in entrypoint
- Full initialize handshake in entrypoint
- sleep 2 before Claude Code starts

### Phase 17: Automation Research

**No programmatic way to trigger `/mcp reconnect` exists.** Confirmed by multiple open feature requests with no timeline:
- [#15232](https://github.com/anthropics/claude-code/issues/15232), [#1026](https://github.com/anthropics/claude-code/issues/1026), [#10129](https://github.com/anthropics/claude-code/issues/10129), [#10071](https://github.com/anthropics/claude-code/issues/10071)

**SSE was deprecated, NOT stdio.** The MCP spec says clients SHOULD support stdio. Stdio is tier-1 recommended for local deployments.

---

## Root Causes Identified (Final)

### 1. Stale MCP Session ID Reuse (Server-Side) - FIXED
- **Fix:** `stateless_http=True` on both servers

### 2. 406 Accept Header Rejection (Protocol Mismatch) - PARTIALLY FIXED
- Claude Code sends requests without proper `Accept: application/json, text/event-stream` header
- MCP SDK rejects with 406 on both GET and POST
- ASGI middleware to fix headers made things worse (broke connection handling)
- **Status:** Cannot fix server-side without introducing other issues

### 3. Accumulated Client State - FIXED
- **Fix:** jq surgical cleaning of MCP fields from `.claude.json` in entrypoint

### 4. IPv6/IPv4 Dual-Stack - FIXED
- **Fix:** `NODE_OPTIONS="--dns-result-order=ipv4first"` in entrypoint

### 5. Claude Code Client Intermittent Failure - UNFIXABLE FROM SERVER SIDE
- Claude Code sometimes doesn't even attempt to connect (no server requests)
- Split results prove per-server independent ~10% failure rate
- No programmatic reconnection available
- **Root cause:** Likely internal timeout/race condition in Claude Code's MCP client

---

## Current State of Fixes

| File | Change | Status |
|------|--------|--------|
| `qms-cli/qms_mcp/server.py` | `stateless_http=True` | Applied, no middleware |
| `git_mcp/server.py` | `stateless_http=True` | Applied, no middleware |
| `docker/entrypoint.sh` | IPv4-first DNS, jq MCP cleaning, handshake warmup | Applied |
| `docker/Dockerfile` | Added `jq` package | Applied |

**Best achieved reliability: 90% (27/30) with no re-auth.**

---

## Architectural Decision: Stdio Proxy

The remaining ~10% failure rate cannot be fixed from the server side. HTTP transport in Claude Code has inherent reliability issues in Docker containers. The solution is to **eliminate HTTP transport from Claude Code's perspective entirely**.

### The Plan

Replace direct HTTP connections with a local stdio proxy inside the container:

```
Claude Code <--stdio--> Proxy (container) <--HTTP--> MCP Server (host)
```

- **Stdio connections are near-100% reliable** (local subprocess, no network)
- Proxy handles HTTP connection with retry logic
- Claude Code never sees HTTP failures
- Proxy can reconnect to the host MCP server transparently

See `stdio-proxy-plan.md` for full implementation plan.

---

## Key Insights

1. **`stateless_http=True` is essential** - eliminates server-side session reuse
2. **One bad server can poison all** - independent per-server failures, but correlated
3. **ASGI middleware wrappers hurt more than help** - interfere with FastMCP's connection handling
4. **Docker image rebuild required** for entrypoint changes
5. **`.claude.json` contains both MCP state AND auth** - must use jq for surgical cleaning
6. **No programmatic `/mcp reconnect`** - confirmed limitation, multiple open feature requests
7. **SSE was deprecated, not stdio** - stdio is tier-1 recommended transport
8. **HTTP transport in Docker is inherently unreliable** - architectural solution (stdio proxy) needed

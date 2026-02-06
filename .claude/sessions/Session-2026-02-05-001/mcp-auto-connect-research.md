# MCP Auto-Connect Research Summary

**Date:** 2026-02-05
**Session:** Session-2026-02-05-001
**Topic:** Investigation of MCP auto-connect failures in containerized Claude Code

---

## Problem Statement

Our containerization initiative has a specific issue: manual `/mcp` → Reconnect always works, but auto-connect at container/session startup fails. This is the last 5% blocking full automation.

---

## Root Cause Analysis

### 1. OAuth Discovery Bypass Required (Issue #7290)

Claude Code **always attempts OAuth discovery** for HTTP transports before using configured headers. The workaround requires **dual headers**:

```json
{
  "headers": {
    "X-API-Key": "any-value",
    "Authorization": "Bearer any-value"
  }
}
```

**Status**: Already implemented in Session-2026-02-04-003. Likely not our blocker.

**Source**: https://github.com/anthropics/claude-code/issues/7290

### 2. Startup Timing/Race Conditions

- Environment variables are read **once at startup** and cached
- MCP servers need to be **fully ready** before Claude Code's 30-second timeout
- Server being *reachable* doesn't mean it's *ready to handle MCP protocol handshakes*

**Source**: https://deepwiki.com/FlorianBruniaux/claude-code-ultimate-guide/17.4-environment-variables

### 3. Protocol Version Header Missing (Issue #11633)

Claude Code's **health check differs from actual connection**:
- Manual test with `curl` includes `Mcp-Protocol-Version: 2024-11-05` header
- Auto-connect health check may not send required headers
- This causes "Failed to connect" despite working manual tests

**Source**: https://github.com/anthropics/claude-code/issues/11633

### 4. HTTP Keep-Alive / Connection Drops (Issue #4598)

- Connections drop **5-10 minutes** after session start
- Claude Code lacks reconnection/heartbeat logic for HTTP transports
- **Status**: Closed as "not planned" — known limitation

**Source**: https://github.com/anthropics/claude-code/issues/4598

### 5. Project vs User Scope Conflict

Having MCP configured at **both** project scope (`.mcp.json`) **and** user scope (`$CLAUDE_CONFIG_DIR/.claude.json`) can cause conflicts. Previous sessions had both configured.

---

## Container-Specific Issues

| Issue | Description | Source |
|-------|-------------|--------|
| **Transport mismatch** | Container expects HTTP but client sends stdio | [Issue #526](https://github.com/upstash/context7/issues/526) |
| **WSL2 quirks** | Docker MCP gateway fails on WSL2 but works on Windows | [Issue #14867](https://github.com/docker/for-win/issues/14867) |
| **Tool registration failure** | Connection succeeds but tools don't register | [Issue #5241](https://github.com/anthropics/claude-code/issues/5241) |
| **30-second timeout** | If handshake isn't complete in 30s, connection fails | [Issue #336](https://github.com/docker/mcp-gateway/issues/336) |

---

## Why Manual Reconnect Works

The manual `/mcp` → Reconnect flow likely:

1. Uses a **different code path** than startup initialization
2. Sends the correct protocol headers
3. Has the user-scope config already loaded
4. Benefits from the environment being fully initialized

---

## Recommended Next Steps

### Option A: Investigate Startup Sequence

1. Run Claude Code with `claude --mcp-debug` in the container
2. Compare logs from startup vs manual reconnect
3. Look for missing headers or timing differences

### Option B: Delay Claude Code Start

```bash
# In entrypoint.sh, add actual MCP handshake test
until curl -s -X POST http://host.docker.internal:8000/mcp \
  -H "Content-Type: application/json" \
  -H "Mcp-Protocol-Version: 2024-11-05" \
  -d '{"jsonrpc":"2.0","method":"initialize","id":1}' | grep -q "result"; do
  sleep 1
done
```

### Option C: Simplify to Project Scope Only

1. Remove all user-scope MCP configuration
2. Rely solely on `/pipe-dream/.mcp.json`
3. This eliminates scope conflict as a variable

### Option D: Accept the Limitation

- Document that manual reconnect is required on first launch
- This is a known Claude Code limitation for HTTP transports
- Focus efforts elsewhere

---

## Key GitHub Issues Referenced

| Issue | Title | Status |
|-------|-------|--------|
| [#1611](https://github.com/anthropics/claude-code/issues/1611) | MCP servers fail to connect despite correct configuration | Reopened |
| [#4598](https://github.com/anthropics/claude-code/issues/4598) | HTTP-Based MCP Connection Drops Mid-Session | Closed (not planned) |
| [#7290](https://github.com/anthropics/claude-code/issues/7290) | HTTP/SSE MCP Transport Ignores Authentication Headers | Open |
| [#11633](https://github.com/anthropics/claude-code/issues/11633) | HTTP MCP Server "Failed to connect" Despite Manual Testing | Closed (duplicate) |
| [#5241](https://github.com/anthropics/claude-code/issues/5241) | MCP Tools Not Registering Despite Successful Connection | Open |
| [#336](https://github.com/docker/mcp-gateway/issues/336) | Claude Code to MCP Toolkit is timing out | Open |

---

## Additional Resources

- [MCP Configuration and Debugging Guide](https://deepwiki.com/FlorianBruniaux/claude-code-ultimate-guide/6.7-mcp-configuration-and-debugging)
- [Claude Code MCP Official Docs](https://code.claude.com/docs/en/mcp)
- [Docker MCP Toolkit Blog Post](https://www.docker.com/blog/add-mcp-servers-to-claude-code-with-mcp-toolkit/)

---

## Conclusion

The MCP auto-connect issue appears to be a **known limitation** in Claude Code's HTTP transport handling, not a configuration error on our part. The most promising paths forward are:

1. **Debug mode investigation** (`--mcp-debug`) to confirm the exact failure point
2. **Proper MCP handshake verification** in entrypoint before starting Claude
3. **Scope simplification** to eliminate configuration conflicts

Given that Issue #4598 was closed as "not planned," Anthropic may not prioritize fixing HTTP transport reliability. We should consider whether the manual reconnect workaround is acceptable for our use case.

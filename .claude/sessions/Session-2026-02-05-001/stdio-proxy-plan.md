# MCP Stdio Proxy: Implementation Plan

## Problem Statement

Claude Code's HTTP MCP client is unreliable in Docker containers (~10% failure rate). The failures are client-side - Claude Code sometimes doesn't even attempt to connect. No programmatic reconnection exists. This blocks multi-agent container automation.

## Solution

Replace direct HTTP connections with a local stdio proxy inside the container.

### Current Architecture (Unreliable)

```
Claude Code --(HTTP)--> host.docker.internal:8000 --> QMS MCP Server
Claude Code --(HTTP)--> host.docker.internal:8001 --> Git MCP Server
```

Failure point: Claude Code's HTTP MCP client intermittently fails to connect through Docker's virtual network.

### Proposed Architecture (Reliable)

```
Claude Code --(stdio)--> mcp_proxy.py --(HTTP)--> host.docker.internal:8000 --> QMS MCP Server
Claude Code --(stdio)--> mcp_proxy.py --(HTTP)--> host.docker.internal:8001 --> Git MCP Server
```

- **Claude Code -> Proxy:** stdio (local subprocess, near-100% reliable)
- **Proxy -> Host MCP Server:** HTTP with retry logic (proxy handles failures transparently)

## How It Works

1. Claude Code spawns the proxy as a local subprocess (stdio transport)
2. Claude Code sends MCP JSON-RPC messages to the proxy via stdin
3. The proxy forwards each request to the remote HTTP MCP server
4. The proxy returns the response to Claude Code via stdout
5. If the HTTP connection fails, the proxy retries before returning an error

Claude Code never sees HTTP. It only sees a local stdio MCP server that always responds.

## Implementation

### 1. The Proxy Script (`docker/scripts/mcp_proxy.py`)

A single Python script that:
- Reads JSON-RPC messages from stdin
- Forwards them to the remote HTTP MCP server via `httpx` or `requests`
- Returns responses to stdout
- Handles connection failures with configurable retry logic
- Logs to stderr (critical: stdout is reserved for MCP protocol)

```python
#!/usr/bin/env python3
"""
MCP Stdio-to-HTTP Proxy

Bridges Claude Code's stdio MCP client to a remote HTTP MCP server.
Handles connection retries transparently.

Usage:
    python mcp_proxy.py <remote_url> [--retries N] [--timeout MS]

Example:
    python mcp_proxy.py http://host.docker.internal:8000/mcp --retries 3
"""
```

Key behaviors:
- **Initialize:** On `initialize` request, establish HTTP connection to remote server
- **Forward:** All subsequent requests forwarded via HTTP POST
- **Retry:** On HTTP failure, retry N times with exponential backoff
- **Headers:** Forward any configured headers (API keys, auth tokens)
- **Stateless:** Each request is an independent HTTP POST (matches `stateless_http=True` on server)

### 2. Container MCP Config (`docker/.mcp.json`)

Change from HTTP to command (stdio):

```json
{
  "mcpServers": {
    "qms": {
      "type": "command",
      "command": "python3",
      "args": [
        "/proxy/mcp_proxy.py",
        "http://host.docker.internal:8000/mcp",
        "--retries", "3",
        "--timeout", "10000",
        "--header", "X-API-Key=qms-internal",
        "--header", "Authorization=Bearer internal-trusted"
      ]
    },
    "git": {
      "type": "command",
      "command": "python3",
      "args": [
        "/proxy/mcp_proxy.py",
        "http://host.docker.internal:8001/mcp",
        "--retries", "3",
        "--timeout", "10000",
        "--header", "X-API-Key=git-internal",
        "--header", "Authorization=Bearer internal-trusted"
      ]
    }
  }
}
```

### 3. Dockerfile Changes

```dockerfile
# Copy proxy script into container
COPY scripts/mcp_proxy.py /proxy/mcp_proxy.py

# Install HTTP client library (if not using stdlib)
RUN pip install httpx
```

### 4. Entrypoint Changes

The entrypoint can be simplified:
- **Remove:** MCP health check loops (proxy handles retries)
- **Remove:** MCP handshake warm-up (not needed for stdio)
- **Remove:** sleep delay (stdio connection is instant)
- **Keep:** jq MCP state cleaning (belt and suspenders)
- **Keep:** IPv4-first DNS (proxy still uses HTTP to host)
- **Keep:** GitHub CLI configuration

### 5. Host MCP Servers

No changes needed. The servers continue to run with `stateless_http=True` on the host. The proxy connects to them over HTTP exactly as Claude Code did before.

## Protocol Flow

### Startup

```
1. Claude Code starts
2. Claude Code spawns: python3 /proxy/mcp_proxy.py http://host.docker.internal:8000/mcp
3. Proxy starts, reads from stdin
4. Claude Code sends:  {"jsonrpc":"2.0","method":"initialize",...}  (via stdin)
5. Proxy forwards:     POST http://host.docker.internal:8000/mcp  (via HTTP)
6. Server responds:    {"jsonrpc":"2.0","result":{...}}            (via HTTP)
7. Proxy returns:      {"jsonrpc":"2.0","result":{...}}            (via stdout)
8. Claude Code sends:  {"jsonrpc":"2.0","method":"notifications/initialized"}
9. Proxy forwards, returns response
10. Connection established. Claude Code sees a working stdio MCP server.
```

### Tool Call

```
1. Claude Code sends:  {"jsonrpc":"2.0","method":"tools/call","params":{"name":"qms_inbox",...}}
2. Proxy forwards via HTTP POST
3. If HTTP fails: retry up to 3 times with backoff
4. Server responds with tool result
5. Proxy returns result via stdout
```

### Error Handling

```
1. Claude Code sends tool call
2. Proxy attempts HTTP POST -> connection refused
3. Proxy retries (attempt 2) -> connection refused
4. Proxy retries (attempt 3) -> success
5. Proxy returns result (Claude Code never saw the failure)

OR if all retries fail:

4. Proxy returns JSON-RPC error: {"jsonrpc":"2.0","error":{"code":-32000,"message":"Remote server unreachable after 3 retries"}}
5. Claude Code sees a clean MCP error (not a connection failure)
```

## Advantages Over Current Approach

| Aspect | HTTP (Current) | Stdio Proxy (Proposed) |
|--------|---------------|----------------------|
| Connection reliability | ~90% | ~100% (stdio) |
| Retry on failure | None (client gives up) | Configurable (proxy retries) |
| Reconnection | Manual `/mcp` only | Automatic (proxy reconnects) |
| Docker network dependency | Direct (fragile) | Proxy-mediated (resilient) |
| Accept header issues | 406 errors | Proxy sends correct headers |
| Session ID issues | Requires `stateless_http` | Proxy manages its own sessions |
| Entrypoint complexity | Health checks, warm-up, sleep | Minimal |

## Risks and Mitigations

### Risk: Proxy adds latency
- **Mitigation:** Minimal overhead. Proxy is a thin forwarder - adds <1ms per request for local stdin/stdout + existing HTTP latency.

### Risk: Proxy crashes
- **Mitigation:** Claude Code detects stdio process exit and reports MCP server as disconnected. This is the same behavior as any stdio MCP server crashing. User can restart with `/mcp`.

### Risk: Proxy doesn't implement full MCP protocol
- **Mitigation:** The proxy doesn't need to understand MCP semantics. It's a transparent JSON-RPC forwarder - reads JSON from stdin, POSTs it to the remote server, returns the response. Protocol compliance is handled by the real MCP server.

### Risk: SSE/streaming responses
- **Mitigation:** For `stateless_http=True` servers, all responses are single HTTP responses (no streaming). The proxy just forwards the response body. If we ever need streaming, the proxy can be extended.

## Implementation Order

1. Write `mcp_proxy.py` (the proxy script)
2. Test it standalone: `echo '{"jsonrpc":"2.0","method":"initialize",...}' | python mcp_proxy.py http://localhost:8000/mcp`
3. Update `docker/.mcp.json` to use command/stdio transport
4. Update `docker/Dockerfile` to copy proxy and install dependencies
5. Simplify `docker/entrypoint.sh`
6. Rebuild and test: run container 30+ times, expect 100% connection rate
7. Create CR to formalize the change

## Dependencies

- Python 3.11 (already in container)
- `httpx` or `requests` (need to install) or `urllib.request` (stdlib, no install needed)
- Host MCP servers with `stateless_http=True` (already applied)

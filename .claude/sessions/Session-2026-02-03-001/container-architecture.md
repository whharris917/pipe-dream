# Container Session Architecture

This document describes the technical architecture that enables zero-friction Claude Code sessions in Docker containers with remote MCP server connectivity.

## Overview

Claude Code runs inside a Docker container with read-only access to the QMS repository. The QMS MCP server runs on the host machine and exposes tools via HTTP transport. The container connects to the host's MCP server through Docker's `host.docker.internal` networking.

```
+------------------+          +------------------+
|   Docker Host    |          |    Container     |
|                  |          |                  |
|  QMS MCP Server  |<-------->|   Claude Code    |
|  (port 8000)     |   HTTP   |                  |
|                  |          |                  |
|  /pipe-dream/    |--------->| /pipe-dream/:ro  |
|  (source)        |  mount   | (read-only)      |
+------------------+          +------------------+
```

## Authentication Persistence

Claude Code stores authentication state in its configuration directory. By default, this is `~/.claude/` but can be overridden with the `CLAUDE_CONFIG_DIR` environment variable.

**Solution:** Point `CLAUDE_CONFIG_DIR` to a Docker named volume that persists across container restarts.

```yaml
# docker-compose.yml
services:
  claude-agent:
    environment:
      - CLAUDE_CONFIG_DIR=/claude-config
    volumes:
      - claude-config:/claude-config

volumes:
  claude-config:
```

**Behavior:**
- First run: User authenticates via browser OAuth flow
- Subsequent runs: Credentials loaded from persistent volume, no authentication required

## MCP Server Auto-Connection

Claude Code supports two MCP transport types:
- **stdio**: Claude spawns the MCP server as a subprocess
- **HTTP**: Claude connects to an external MCP server

For HTTP transport, Claude Code attempts OAuth 2.0 discovery before using configured authentication headers. This is a known behavior documented in [GitHub issue #7290](https://github.com/anthropics/claude-code/issues/7290).

**Problem:** When OAuth discovery endpoints return 404, Claude Code fails to connect even when valid authentication headers are configured.

**Solution:** Configure multiple authentication headers. This triggers a code path that bypasses OAuth discovery.

```json
{
  "mcpServers": {
    "qms": {
      "type": "http",
      "url": "http://host.docker.internal:8000/mcp",
      "headers": {
        "X-API-Key": "qms-internal",
        "Authorization": "Bearer internal-trusted"
      }
    }
  }
}
```

Both headers must be present. The specific values are not validated by our MCP server - they serve only to trigger the OAuth bypass in Claude Code.

## Container Configuration Files

### docker-compose.yml

Key configuration elements:

```yaml
services:
  claude-agent:
    working_dir: /pipe-dream                    # Claude finds .mcp.json here
    volumes:
      - ../:/pipe-dream:ro                      # Read-only QMS access
      - ./.mcp.json:/pipe-dream/.mcp.json:ro    # HTTP MCP config overlay
      - ./.claude-settings.json:/pipe-dream/.claude/settings.local.json:ro
      - claude-config:/claude-config            # Persistent auth storage
    environment:
      - HOME=/
      - CLAUDE_CONFIG_DIR=/claude-config        # Auth persistence
      - MCP_TIMEOUT=60000                       # Extended timeout for startup
    extra_hosts:
      - "host.docker.internal:host-gateway"    # Linux host access
```

### .mcp.json (Container-specific)

Overlays the host's stdio-based `.mcp.json` with HTTP transport configuration:

```json
{
  "mcpServers": {
    "qms": {
      "type": "http",
      "url": "http://host.docker.internal:8000/mcp",
      "headers": {
        "X-API-Key": "qms-internal",
        "Authorization": "Bearer internal-trusted"
      }
    }
  }
}
```

### .claude-settings.json

Enables the project-scoped MCP server without requiring interactive approval:

```json
{
  "enabledMcpjsonServers": ["qms"]
}
```

### entrypoint.sh

Handles first-run initialization:

1. Waits for MCP server to be reachable (up to 30 seconds)
2. On first run, registers MCP server at user scope with dual headers
3. Creates marker file to skip registration on subsequent runs
4. Executes Claude Code

## Startup Sequence

**Host (Terminal 1):**
```bash
cd qms-cli
python -m qms_mcp --transport streamable-http --host 0.0.0.0 --port 8000 --project-root ..
```

**Host (Terminal 2):**
```bash
cd docker
docker-compose up -d
docker-compose exec claude-agent bash
# Inside container:
claude
```

**What happens:**
1. MCP server listens on port 8000
2. Container starts, entrypoint waits for MCP reachability
3. First run: entrypoint registers MCP at user scope with dual headers
4. Claude Code starts in `/pipe-dream/` working directory
5. Claude loads `.mcp.json` (HTTP config with dual headers)
6. Multiple headers bypass OAuth discovery
7. Claude connects to MCP server
8. MCP tools available immediately

**Note:** The `claude-session.sh` script at repo root automates these steps but was not verified in final testing. The manual path above is the verified approach.

## Resetting State

To reset authentication and start fresh:

```bash
docker-compose down
docker volume rm docker_claude-config
docker-compose up -d
```

## References

- [GitHub #1736](https://github.com/anthropics/claude-code/issues/1736) - CLAUDE_CONFIG_DIR for container auth
- [GitHub #7290](https://github.com/anthropics/claude-code/issues/7290) - HTTP transport OAuth bypass with multiple headers
- [Claude Code MCP Documentation](https://code.claude.com/docs/en/mcp)

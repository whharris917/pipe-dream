#!/bin/bash
# Entrypoint script for Claude container
# Initializes config directory and MCP server, then starts Claude

CONFIG_DIR="${CLAUDE_CONFIG_DIR:-/claude-config}"
MCP_URL="http://host.docker.internal:8000/mcp"
MCP_MARKER="$CONFIG_DIR/.mcp-configured"

# Wait for MCP server to be reachable (up to 30 seconds)
echo "Waiting for MCP server..."
for i in $(seq 1 30); do
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 2 "$MCP_URL" 2>/dev/null)
    if echo "$HTTP_CODE" | grep -qE "^[0-9]+$" && [ "$HTTP_CODE" -gt 0 ]; then
        echo "MCP server reachable (HTTP $HTTP_CODE)"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "Warning: MCP server not reachable after 30 seconds"
    fi
    sleep 1
done

# First run: configure MCP server using claude mcp add
# This ensures proper registration with all internal state
if [ ! -f "$MCP_MARKER" ]; then
    echo "First run detected - configuring MCP server..."
    # Add MCP server at user scope with auth header (persists in CLAUDE_CONFIG_DIR)
    # The header tells Claude Code auth is already handled
    # Per GitHub issue #7290: Multiple headers bypass OAuth discovery
    claude mcp add --transport http --scope user \
        --header "X-API-Key: qms-internal" \
        --header "Authorization: Bearer internal-trusted" \
        qms "$MCP_URL" 2>/dev/null || true
    touch "$MCP_MARKER"
    echo "MCP server configured"
fi

# Start Claude Code
exec claude "$@"

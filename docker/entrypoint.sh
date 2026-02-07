#!/bin/bash
# Entrypoint script for Claude container
# Verifies mounts, configures GitHub CLI, cleans stale state, then starts Claude.
#
# MCP servers are configured via PROJECT-LEVEL config only:
#   /pipe-dream/.mcp.json - defines servers (mounted from docker/.mcp.json)
#   /pipe-dream/.claude/settings.local.json - enables servers (mounted from docker/.claude-settings.json)
#
# MCP connections use the stdio proxy (mcp_proxy.py) which handles HTTP
# forwarding with retry logic. No direct HTTP health checks needed here.

# --- Verify volume mounts are ready ---
echo "Verifying volume mounts..."

# Wait for .mcp.json to be available (up to 10 seconds)
for i in $(seq 1 10); do
    if [ -f "/pipe-dream/.mcp.json" ]; then
        echo "MCP config file mounted: /pipe-dream/.mcp.json"
        break
    fi
    if [ $i -eq 10 ]; then
        echo "ERROR: /pipe-dream/.mcp.json not found after 10 seconds"
        exit 1
    fi
    echo "Waiting for mounts... ($i/10)"
    sleep 1
done

# Verify settings file
if [ -f "/pipe-dream/.claude/settings.local.json" ]; then
    echo "Settings file mounted: /pipe-dream/.claude/settings.local.json"
else
    echo "WARNING: /pipe-dream/.claude/settings.local.json not found"
fi

# Show MCP config for debugging
echo "MCP config contents:"
cat /pipe-dream/.mcp.json

# MCP connections are handled by the stdio proxy (mcp_proxy.py).
# The proxy forwards JSON-RPC over HTTP with retry logic, so no
# health checks, handshake warm-up, or sleep delays are needed here.
echo "MCP configured via stdio proxy (see .mcp.json)"

# Configure GitHub CLI if token provided (per CR-053)
if [ -n "$GH_TOKEN" ]; then
    echo "Configuring GitHub CLI..."
    echo "$GH_TOKEN" | gh auth login --with-token 2>/dev/null
    gh auth setup-git 2>/dev/null
    GH_USER=$(gh api user --jq '.login' 2>/dev/null || echo "claude-agent")
    GH_EMAIL=$(gh api user --jq '.email // empty' 2>/dev/null)
    if [ -z "$GH_EMAIL" ]; then
        GH_EMAIL="${GH_USER}@users.noreply.github.com"
    fi
    git config --global user.name "$GH_USER"
    git config --global user.email "$GH_EMAIL"
    echo "GitHub CLI configured (user: $GH_USER)"
else
    echo "Note: GH_TOKEN not set - git push will not work"
fi

# Fix IPv6 issue: Node.js fetch fails when IPv6 is unreachable but listed in /etc/hosts
# Force Node.js to prefer IPv4 addresses over IPv6
export NODE_OPTIONS="${NODE_OPTIONS:+$NODE_OPTIONS }--dns-result-order=ipv4first"
echo "Node.js configured for IPv4-first DNS resolution"

# Clear ephemeral state while preserving auth, project memory, and history.
# Two-part strategy:
#   1. Delete ephemeral files (caches, debug logs, telemetry)
#   2. Surgically remove MCP-related fields from .claude.json (preserve auth)
# Note: projects/ and history.jsonl are intentionally preserved (CR-059) to allow
# agents to accumulate per-project memory and command history across sessions.
if [ -d "/claude-config" ]; then
    echo "Clearing ephemeral state (preserving auth, projects, history)..."
    rm -rf /claude-config/cache 2>/dev/null
    rm -rf /claude-config/session-env 2>/dev/null
    rm -rf /claude-config/debug 2>/dev/null
    rm -rf /claude-config/telemetry 2>/dev/null
    rm -f /claude-config/.claude.json.backup.* 2>/dev/null
    rm -f /claude-config/.update.lock 2>/dev/null

    # Surgically clean MCP state from .claude.json while preserving auth
    if [ -f /claude-config/.claude.json ] && command -v jq >/dev/null 2>&1; then
        echo "Cleaning MCP state from .claude.json..."
        jq 'walk(if type == "object" and has("mcpServers") then .mcpServers = {} else . end)
            | walk(if type == "object" and has("enabledMcpjsonServers") then .enabledMcpjsonServers = [] else . end)
            | walk(if type == "object" and has("disabledMcpjsonServers") then .disabledMcpjsonServers = [] else . end)' \
            /claude-config/.claude.json > /claude-config/.claude.json.tmp \
            && mv /claude-config/.claude.json.tmp /claude-config/.claude.json
        echo "MCP state cleaned from .claude.json"
    fi

    echo "Ephemeral state cleared (auth, projects, history preserved)"
fi

# If SETUP_ONLY mode, sleep instead of starting Claude
# Used by launch.sh: "docker run -d -e SETUP_ONLY=1" does setup, then
# "docker exec -it claude" attaches the interactive session separately.
if [ "${SETUP_ONLY:-}" = "1" ]; then
    echo "Setup complete. Waiting for docker exec..."
    exec sleep infinity
fi

# Start Claude Code
exec claude "$@"

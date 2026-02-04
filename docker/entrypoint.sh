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

# Configure GitHub CLI if token provided (per CR-053)
if [ -n "$GH_TOKEN" ]; then
    echo "Configuring GitHub CLI..."
    echo "$GH_TOKEN" | gh auth login --with-token 2>/dev/null
    gh auth setup-git 2>/dev/null
    # Configure git user for commits (use GitHub-provided values or defaults)
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

# Start Claude Code
exec claude "$@"

#!/bin/bash
# Entrypoint script for Claude container
# Initializes config directory and MCP servers, then starts Claude

CONFIG_DIR="${CLAUDE_CONFIG_DIR:-/claude-config}"
QMS_MCP_URL="http://host.docker.internal:8000/mcp"
GIT_MCP_URL="http://host.docker.internal:8001/mcp"
MCP_MARKER="$CONFIG_DIR/.mcp-configured"
GIT_MCP_MARKER="$CONFIG_DIR/.git-mcp-configured"

# Wait for QMS MCP server to be reachable (up to 30 seconds)
echo "Waiting for QMS MCP server..."
for i in $(seq 1 30); do
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 2 "$QMS_MCP_URL" 2>/dev/null)
    if echo "$HTTP_CODE" | grep -qE "^[0-9]+$" && [ "$HTTP_CODE" -gt 0 ]; then
        echo "QMS MCP server reachable (HTTP $HTTP_CODE)"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "Warning: QMS MCP server not reachable after 30 seconds"
    fi
    sleep 1
done

# First run: configure QMS MCP server using claude mcp add
# This ensures proper registration with all internal state
if [ ! -f "$MCP_MARKER" ]; then
    echo "First run detected - configuring QMS MCP server..."
    # Add MCP server at user scope with auth header (persists in CLAUDE_CONFIG_DIR)
    # The header tells Claude Code auth is already handled
    # Per GitHub issue #7290: Multiple headers bypass OAuth discovery
    claude mcp add --transport http --scope user \
        --header "X-API-Key: qms-internal" \
        --header "Authorization: Bearer internal-trusted" \
        qms "$QMS_MCP_URL" 2>/dev/null || true
    touch "$MCP_MARKER"
    echo "QMS MCP server configured"
fi

# Check for Git MCP server and configure if available (CR-054)
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 2 "$GIT_MCP_URL" 2>/dev/null)
if echo "$HTTP_CODE" | grep -qE "^[0-9]+$" && [ "$HTTP_CODE" -gt 0 ]; then
    echo "Git MCP server reachable (HTTP $HTTP_CODE)"
    if [ ! -f "$GIT_MCP_MARKER" ]; then
        echo "Configuring Git MCP server..."
        claude mcp add --transport http --scope user \
            git "$GIT_MCP_URL" 2>/dev/null || true
        touch "$GIT_MCP_MARKER"
        echo "Git MCP server configured"
    fi
else
    echo "Note: Git MCP server not available on port 8001"
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

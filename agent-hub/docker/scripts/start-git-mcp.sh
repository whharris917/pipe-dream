#!/bin/bash
# Start the Git MCP server for container git operations
#
# Usage: ./start-git-mcp.sh [--background]
#
# CR-054: Git MCP Server for Container Operations
# CR-069: Moved to agent-hub/docker/scripts/

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$(dirname "$SCRIPT_DIR")")")"
LOG_DIR="$PROJECT_ROOT/agent-hub/logs"
MCP_DIR="$PROJECT_ROOT/agent-hub/mcp-servers"

# Check if running in background mode
BACKGROUND=false
if [ "$1" = "--background" ]; then
    BACKGROUND=true
fi

# Check if already running via port probe
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/mcp 2>/dev/null | grep -qE "200|40[0-9]"; then
    echo "Git MCP server already running on port 8001"
    exit 1
fi

mkdir -p "$LOG_DIR"

echo "Starting Git MCP server on port 8001..."
echo "Project root: $PROJECT_ROOT"

cd "$MCP_DIR"

if [ "$BACKGROUND" = true ]; then
    # Run in background
    nohup python -m git_mcp --transport streamable-http --host 0.0.0.0 --port 8001 --project-root "$PROJECT_ROOT" > "$LOG_DIR/git-mcp-server.log" 2>&1 &
    echo "Server started in background (PID: $!)"
    echo "Log file: $LOG_DIR/git-mcp-server.log"
else
    # Run in foreground
    python -m git_mcp --transport streamable-http --host 0.0.0.0 --port 8001 --project-root "$PROJECT_ROOT"
fi

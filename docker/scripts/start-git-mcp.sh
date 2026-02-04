#!/bin/bash
# Start the Git MCP server for container git operations
#
# Usage: ./start-git-mcp.sh [--background]
#
# CR-054: Git MCP Server for Container Operations

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

# Check if running in background mode
BACKGROUND=false
if [ "$1" = "--background" ]; then
    BACKGROUND=true
fi

# Check for existing server
PID_FILE="$PROJECT_ROOT/.git-mcp-server.pid"
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if kill -0 "$OLD_PID" 2>/dev/null; then
        echo "Git MCP server already running (PID: $OLD_PID)"
        echo "Stop it first with: kill $OLD_PID"
        exit 1
    else
        rm -f "$PID_FILE"
    fi
fi

cd "$PROJECT_ROOT"

echo "Starting Git MCP server on port 8001..."
echo "Project root: $PROJECT_ROOT"

if [ "$BACKGROUND" = true ]; then
    # Run in background
    nohup python -m git_mcp --transport streamable-http --host 0.0.0.0 --port 8001 --project-root "$PROJECT_ROOT" > "$PROJECT_ROOT/.git-mcp-server.log" 2>&1 &
    echo $! > "$PID_FILE"
    echo "Server started in background (PID: $(cat $PID_FILE))"
    echo "Log file: $PROJECT_ROOT/.git-mcp-server.log"
else
    # Run in foreground
    python -m git_mcp --transport streamable-http --host 0.0.0.0 --port 8001 --project-root "$PROJECT_ROOT"
fi

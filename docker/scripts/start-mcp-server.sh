#!/bin/bash
# Start QMS MCP server with streamable-http transport for container connectivity
# Run this on the HOST before starting the container
#
# Usage: ./start-mcp-server.sh [--background]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Check if running in background mode
BACKGROUND=false
if [ "$1" = "--background" ]; then
    BACKGROUND=true
fi

# Check for existing server
PID_FILE="$PROJECT_ROOT/.qms-mcp-server.pid"
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if kill -0 "$OLD_PID" 2>/dev/null; then
        echo "QMS MCP server already running (PID: $OLD_PID)"
        echo "Stop it first with: kill $OLD_PID"
        exit 1
    else
        rm -f "$PID_FILE"
    fi
fi

echo "Starting QMS MCP server on port 8000..."
echo "Project root: $PROJECT_ROOT"

cd "$PROJECT_ROOT/qms-cli"

if [ "$BACKGROUND" = true ]; then
    # Run in background
    nohup python -m qms_mcp --transport streamable-http --host 0.0.0.0 --port 8000 --project-root "$PROJECT_ROOT" > "$PROJECT_ROOT/.qms-mcp-server.log" 2>&1 &
    echo $! > "$PID_FILE"
    echo "Server started in background (PID: $(cat $PID_FILE))"
    echo "Log file: $PROJECT_ROOT/.qms-mcp-server.log"
else
    # Run in foreground
    python -m qms_mcp --transport streamable-http --host 0.0.0.0 --port 8000 --project-root "$PROJECT_ROOT"
fi

#!/bin/bash
# Start QMS MCP server with streamable-http transport for container connectivity
# Run this on the HOST before starting the container
#
# Usage: ./start-mcp-server.sh [--background]
# CR-069: Moved to agent-hub/docker/scripts/

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$(dirname "$SCRIPT_DIR")")")"
LOG_DIR="$PROJECT_ROOT/agent-hub/logs"

# Check if running in background mode
BACKGROUND=false
if [ "$1" = "--background" ]; then
    BACKGROUND=true
fi

# Check if already running via port probe
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/mcp 2>/dev/null | grep -qE "200|40[0-9]"; then
    echo "QMS MCP server already running on port 8000"
    exit 1
fi

mkdir -p "$LOG_DIR"

echo "Starting QMS MCP server on port 8000..."
echo "Project root: $PROJECT_ROOT"

cd "$PROJECT_ROOT/qms-cli"

if [ "$BACKGROUND" = true ]; then
    # Run in background
    nohup python -m qms_mcp --transport streamable-http --host 0.0.0.0 --port 8000 --project-root "$PROJECT_ROOT" > "$LOG_DIR/qms-mcp-server.log" 2>&1 &
    echo "Server started in background (PID: $!)"
    echo "Log file: $LOG_DIR/qms-mcp-server.log"
else
    # Run in foreground
    python -m qms_mcp --transport streamable-http --host 0.0.0.0 --port 8000 --project-root "$PROJECT_ROOT"
fi

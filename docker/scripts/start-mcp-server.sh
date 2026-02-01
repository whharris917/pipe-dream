#!/bin/bash
# Start QMS MCP server with SSE transport for container connectivity
# Run this on the HOST before starting the container

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "Starting QMS MCP server..."
echo "Project root: $PROJECT_ROOT"
echo "Listening on: http://localhost:8000"

cd "$PROJECT_ROOT"
python -m qms_mcp --transport sse --port 8000 --project-root "$PROJECT_ROOT"

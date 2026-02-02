#!/bin/bash
# Start QMS MCP server with streamable-http transport for container connectivity
# Run this on the HOST before starting the container

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "Starting QMS MCP server..."
echo "Project root: $PROJECT_ROOT"
echo "Listening on: http://0.0.0.0:8000/mcp"

cd "$PROJECT_ROOT"
python -m qms_mcp --transport streamable-http --host 0.0.0.0 --port 8000 --project-root "$PROJECT_ROOT"

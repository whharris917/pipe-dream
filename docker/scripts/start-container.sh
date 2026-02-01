#!/bin/bash
# Start the Claude agent container
# Ensure MCP server is running on host before starting

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCKER_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Check if MCP server is reachable
echo "Checking MCP server connectivity..."
if ! curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/sse 2>/dev/null | grep -q "200\|405"; then
    echo "WARNING: MCP server may not be running on localhost:8000"
    echo "Start it with: ./scripts/start-mcp-server.sh"
    echo ""
    read -p "Continue anyway? [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

cd "$DOCKER_DIR"

# Build if needed and start container
docker-compose up -d --build
docker-compose exec claude-agent bash

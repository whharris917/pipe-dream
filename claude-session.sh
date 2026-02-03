#!/bin/bash
# claude-session.sh - Single-command Claude container session
#
# Usage: ./claude-session.sh
#
# This script:
# 1. Starts the MCP server on the host (if not running)
# 2. Starts the Claude agent container
# 3. Verifies MCP connectivity from inside the container
# 4. Launches Claude Code inside the container with MCP auto-configured
#
# The MCP server runs in the background. To stop it: kill $(cat .mcp-server.pid)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}════════════════════════════════════════${NC}"
echo -e "${GREEN}  Claude Container Session${NC}"
echo -e "${GREEN}════════════════════════════════════════${NC}"
echo ""

# --- Step 1: Ensure MCP server is running ---
echo -e "${YELLOW}[1/4]${NC} Checking MCP server..."

MCP_RUNNING=false
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/mcp 2>/dev/null | grep -qE "200|40[0-9]"; then
    MCP_RUNNING=true
    echo -e "      ${GREEN}✓${NC} MCP server already running on port 8000"
fi

if [ "$MCP_RUNNING" = false ]; then
    echo -e "      Starting MCP server in background..."

    # Find Python executable (don't activate venv - it breaks Git Bash PATH)
    if [ -f ".venv/Scripts/python.exe" ]; then
        # Windows
        PYTHON_EXE="$SCRIPT_DIR/.venv/Scripts/python.exe"
    elif [ -f ".venv/bin/python" ]; then
        # Linux/Mac
        PYTHON_EXE="$SCRIPT_DIR/.venv/bin/python"
    else
        echo -e "      ${RED}✗${NC} No Python venv found at .venv/"
        echo -e "      Please create a venv and install requirements first."
        exit 1
    fi

    cd qms-cli
    "$PYTHON_EXE" -m qms_mcp --transport streamable-http --host 0.0.0.0 --port 8000 \
        --project-root "$SCRIPT_DIR" > "$SCRIPT_DIR/.mcp-server.log" 2>&1 &
    MCP_PID=$!
    echo $MCP_PID > "$SCRIPT_DIR/.mcp-server.pid"
    cd "$SCRIPT_DIR"

    # Wait for server to start
    echo -e "      Waiting for MCP server to initialize..."
    for i in {1..10}; do
        if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/mcp 2>/dev/null | grep -qE "200|40[0-9]"; then
            echo -e "      ${GREEN}✓${NC} MCP server started (PID: $MCP_PID)"
            break
        fi
        if [ $i -eq 10 ]; then
            echo -e "      ${RED}✗${NC} MCP server failed to start"
            echo -e "      Check .mcp-server.log for details"
            exit 1
        fi
        sleep 1
    done
fi

# --- Step 2: Start container ---
echo -e "${YELLOW}[2/4]${NC} Starting container..."

cd docker

# Build if needed and start container
if docker-compose up -d --build claude-agent 2>/dev/null; then
    echo -e "      ${GREEN}✓${NC} Container running"
else
    echo -e "      ${RED}✗${NC} Failed to start container"
    exit 1
fi

cd "$SCRIPT_DIR"

# --- Step 3: Verify MCP connectivity from container ---
echo -e "${YELLOW}[3/4]${NC} Verifying MCP connectivity from container..."

cd docker
for i in {1..5}; do
    # Check if container can reach MCP server (any HTTP response = success)
    HTTP_CODE=$(docker-compose exec -T claude-agent curl -s -o /dev/null --max-time 3 -w "%{http_code}" http://host.docker.internal:8000/mcp 2>/dev/null | tail -1)
    if echo "$HTTP_CODE" | grep -qE "^[0-9]+$" && [ "$HTTP_CODE" -gt 0 ]; then
        echo -e "      ${GREEN}✓${NC} Container can reach MCP server (HTTP $HTTP_CODE)"
        break
    fi
    if [ $i -eq 5 ]; then
        echo -e "      ${RED}✗${NC} Container cannot reach MCP server at host.docker.internal:8000"
        echo -e "      Check that the MCP server is running and accessible"
        exit 1
    fi
    sleep 1
done
cd "$SCRIPT_DIR"

# --- Step 4: Launch Claude ---
echo -e "${YELLOW}[4/4]${NC} Launching Claude Code..."
echo ""
echo -e "${GREEN}════════════════════════════════════════${NC}"
echo -e "  You are now in a containerized Claude session."
echo -e "  MCP tools (qms_inbox, etc.) should work automatically."
echo -e "  Type ${YELLOW}exit${NC} to leave the session."
echo -e "${GREEN}════════════════════════════════════════${NC}"
echo ""

# Exec into container and run claude
cd docker
docker-compose exec claude-agent claude
cd "$SCRIPT_DIR"

# Post-session message
echo ""
echo -e "${GREEN}Session ended.${NC}"
if [ -f ".mcp-server.pid" ]; then
    echo -e "MCP server still running (PID: $(cat .mcp-server.pid))"
    echo -e "To stop it: ${YELLOW}kill \$(cat .mcp-server.pid)${NC}"
fi

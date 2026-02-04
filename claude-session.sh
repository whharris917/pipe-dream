#!/bin/bash
# claude-session.sh - Single-command Claude container session
#
# Usage: ./claude-session.sh
#
# This script:
# 1. Starts the QMS MCP server on the host (if not running)
# 2. Starts the Git MCP server on the host (if not running)
# 3. Starts the Claude agent container
# 4. Verifies MCP connectivity from inside the container
# 5. Launches Claude Code inside the container with MCP auto-configured
#
# MCP servers run in the background. To stop them:
#   kill $(cat .qms-mcp-server.pid) $(cat .git-mcp-server.pid)

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

# --- Find Python executable (shared by both MCP servers) ---
if [ -f ".venv/Scripts/python.exe" ]; then
    # Windows
    PYTHON_EXE="$SCRIPT_DIR/.venv/Scripts/python.exe"
elif [ -f ".venv/bin/python" ]; then
    # Linux/Mac
    PYTHON_EXE="$SCRIPT_DIR/.venv/bin/python"
else
    echo -e "${RED}✗${NC} No Python venv found at .venv/"
    echo -e "  Please create a venv and install requirements first."
    exit 1
fi

# --- Step 1: Ensure QMS MCP server is running ---
echo -e "${YELLOW}[1/5]${NC} Checking QMS MCP server..."

QMS_MCP_RUNNING=false
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/mcp 2>/dev/null | grep -qE "200|40[0-9]"; then
    QMS_MCP_RUNNING=true
    echo -e "      ${GREEN}✓${NC} QMS MCP server already running on port 8000"
fi

if [ "$QMS_MCP_RUNNING" = false ]; then
    echo -e "      Starting QMS MCP server in background..."

    cd qms-cli
    "$PYTHON_EXE" -m qms_mcp --transport streamable-http --host 0.0.0.0 --port 8000 \
        --project-root "$SCRIPT_DIR" > "$SCRIPT_DIR/.qms-mcp-server.log" 2>&1 &
    QMS_MCP_PID=$!
    echo $QMS_MCP_PID > "$SCRIPT_DIR/.qms-mcp-server.pid"
    cd "$SCRIPT_DIR"

    # Wait for server to start
    echo -e "      Waiting for QMS MCP server to initialize..."
    for i in {1..10}; do
        if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/mcp 2>/dev/null | grep -qE "200|40[0-9]"; then
            echo -e "      ${GREEN}✓${NC} QMS MCP server started (PID: $QMS_MCP_PID)"
            break
        fi
        if [ $i -eq 10 ]; then
            echo -e "      ${RED}✗${NC} QMS MCP server failed to start"
            echo -e "      Check .qms-mcp-server.log for details"
            exit 1
        fi
        sleep 1
    done
fi

# --- Step 2: Ensure Git MCP server is running ---
echo -e "${YELLOW}[2/5]${NC} Checking Git MCP server..."

GIT_MCP_RUNNING=false
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/mcp 2>/dev/null | grep -qE "200|40[0-9]"; then
    GIT_MCP_RUNNING=true
    echo -e "      ${GREEN}✓${NC} Git MCP server already running on port 8001"
fi

if [ "$GIT_MCP_RUNNING" = false ]; then
    echo -e "      Starting Git MCP server in background..."

    "$PYTHON_EXE" -m git_mcp --transport streamable-http --host 0.0.0.0 --port 8001 \
        --project-root "$SCRIPT_DIR" > "$SCRIPT_DIR/.git-mcp-server.log" 2>&1 &
    GIT_MCP_PID=$!
    echo $GIT_MCP_PID > "$SCRIPT_DIR/.git-mcp-server.pid"

    # Wait for server to start
    echo -e "      Waiting for Git MCP server to initialize..."
    for i in {1..10}; do
        if curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/mcp 2>/dev/null | grep -qE "200|40[0-9]"; then
            echo -e "      ${GREEN}✓${NC} Git MCP server started (PID: $GIT_MCP_PID)"
            break
        fi
        if [ $i -eq 10 ]; then
            echo -e "      ${RED}✗${NC} Git MCP server failed to start"
            echo -e "      Check .git-mcp-server.log for details"
            exit 1
        fi
        sleep 1
    done
fi

# --- Step 3: Start container ---
echo -e "${YELLOW}[3/5]${NC} Starting container..."

cd docker

# Build if needed and start container
if docker-compose up -d --build claude-agent 2>/dev/null; then
    echo -e "      ${GREEN}✓${NC} Container running"
else
    echo -e "      ${RED}✗${NC} Failed to start container"
    exit 1
fi

cd "$SCRIPT_DIR"

# --- Step 4: Verify MCP connectivity from container ---
echo -e "${YELLOW}[4/5]${NC} Verifying MCP connectivity from container..."

cd docker

# Check QMS MCP server
for i in {1..5}; do
    HTTP_CODE=$(docker-compose exec -T claude-agent curl -s -o /dev/null --max-time 3 -w "%{http_code}" http://host.docker.internal:8000/mcp 2>/dev/null | tail -1)
    if echo "$HTTP_CODE" | grep -qE "^[0-9]+$" && [ "$HTTP_CODE" -gt 0 ]; then
        echo -e "      ${GREEN}✓${NC} Container can reach QMS MCP server (HTTP $HTTP_CODE)"
        break
    fi
    if [ $i -eq 5 ]; then
        echo -e "      ${RED}✗${NC} Container cannot reach QMS MCP server at host.docker.internal:8000"
        exit 1
    fi
    sleep 1
done

# Check Git MCP server
for i in {1..5}; do
    HTTP_CODE=$(docker-compose exec -T claude-agent curl -s -o /dev/null --max-time 3 -w "%{http_code}" http://host.docker.internal:8001/mcp 2>/dev/null | tail -1)
    if echo "$HTTP_CODE" | grep -qE "^[0-9]+$" && [ "$HTTP_CODE" -gt 0 ]; then
        echo -e "      ${GREEN}✓${NC} Container can reach Git MCP server (HTTP $HTTP_CODE)"
        break
    fi
    if [ $i -eq 5 ]; then
        echo -e "      ${RED}✗${NC} Container cannot reach Git MCP server at host.docker.internal:8001"
        exit 1
    fi
    sleep 1
done

cd "$SCRIPT_DIR"

# --- Step 5: Launch Claude ---
echo -e "${YELLOW}[5/5]${NC} Launching Claude Code..."
echo ""
echo -e "${GREEN}════════════════════════════════════════${NC}"
echo -e "  You are now in a containerized Claude session."
echo -e "  MCP tools (qms_inbox, git_exec, etc.) work automatically."
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
if [ -f ".qms-mcp-server.pid" ] || [ -f ".git-mcp-server.pid" ]; then
    echo -e "MCP servers still running:"
    [ -f ".qms-mcp-server.pid" ] && echo -e "  QMS: PID $(cat .qms-mcp-server.pid)"
    [ -f ".git-mcp-server.pid" ] && echo -e "  Git: PID $(cat .git-mcp-server.pid)"
    echo -e "To stop them: ${YELLOW}kill \$(cat .qms-mcp-server.pid) \$(cat .git-mcp-server.pid)${NC}"
fi

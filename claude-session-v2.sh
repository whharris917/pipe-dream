#!/bin/bash
# claude-session-v2.sh - Multi-agent container session (preserves entrypoint)
#
# Usage: ./claude-session-v2.sh [agent_name]
# Example: ./claude-session-v2.sh qa
#
# This script uses docker-compose with project names to support multiple agents
# while preserving the entrypoint that handles MCP configuration.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# --- Agent Configuration ---
QMS_USER="${1:-claude}"
export QMS_USER

# Validate agent name
VALID_AGENTS=("claude" "qa" "tu_ui" "tu_scene" "tu_sketch" "tu_sim" "bu")
VALID=false
for agent in "${VALID_AGENTS[@]}"; do
    if [ "$agent" = "$QMS_USER" ]; then
        VALID=true
        break
    fi
done

if [ "$VALID" = false ]; then
    echo "Error: Invalid agent name '$QMS_USER'"
    echo "Valid agents: ${VALID_AGENTS[*]}"
    exit 1
fi

# Ensure agent directories exist
mkdir -p "$SCRIPT_DIR/.claude/users/$QMS_USER/container"
mkdir -p "$SCRIPT_DIR/.claude/users/$QMS_USER/workspace"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}════════════════════════════════════════${NC}"
echo -e "${GREEN}  Agent Container Session: ${YELLOW}$QMS_USER${GREEN}${NC}"
echo -e "${GREEN}════════════════════════════════════════${NC}"
echo ""

# --- Find Python executable ---
if [ -f ".venv/Scripts/python.exe" ]; then
    PYTHON_EXE="$SCRIPT_DIR/.venv/Scripts/python.exe"
elif [ -f ".venv/bin/python" ]; then
    PYTHON_EXE="$SCRIPT_DIR/.venv/bin/python"
else
    echo -e "${RED}✗${NC} No Python venv found at .venv/"
    exit 1
fi

# --- Step 1: Ensure QMS MCP server is running ---
echo -e "${YELLOW}[1/5]${NC} Checking QMS MCP server..."

if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/mcp 2>/dev/null | grep -qE "200|40[0-9]"; then
    echo -e "      ${GREEN}✓${NC} QMS MCP server already running"
else
    echo -e "      Starting QMS MCP server..."
    cd qms-cli
    "$PYTHON_EXE" -m qms_mcp --transport streamable-http --host 0.0.0.0 --port 8000 \
        --project-root "$SCRIPT_DIR" > "$SCRIPT_DIR/.qms-mcp-server.log" 2>&1 &
    echo $! > "$SCRIPT_DIR/.qms-mcp-server.pid"
    cd "$SCRIPT_DIR"
    for i in {1..10}; do
        if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/mcp 2>/dev/null | grep -qE "200|40[0-9]"; then
            echo -e "      ${GREEN}✓${NC} QMS MCP server started"
            break
        fi
        [ $i -eq 10 ] && echo -e "      ${RED}✗${NC} QMS MCP server failed to start" && exit 1
        sleep 1
    done
fi

# --- Step 2: Ensure Git MCP server is running ---
echo -e "${YELLOW}[2/5]${NC} Checking Git MCP server..."

if curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/mcp 2>/dev/null | grep -qE "200|40[0-9]"; then
    echo -e "      ${GREEN}✓${NC} Git MCP server already running"
else
    echo -e "      Starting Git MCP server..."
    "$PYTHON_EXE" -m git_mcp --transport streamable-http --host 0.0.0.0 --port 8001 \
        --project-root "$SCRIPT_DIR" > "$SCRIPT_DIR/.git-mcp-server.log" 2>&1 &
    echo $! > "$SCRIPT_DIR/.git-mcp-server.pid"
    for i in {1..10}; do
        if curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/mcp 2>/dev/null | grep -qE "200|40[0-9]"; then
            echo -e "      ${GREEN}✓${NC} Git MCP server started"
            break
        fi
        [ $i -eq 10 ] && echo -e "      ${RED}✗${NC} Git MCP server failed to start" && exit 1
        sleep 1
    done
fi

# --- Step 3: Start container ---
echo -e "${YELLOW}[3/5]${NC} Starting container for $QMS_USER..."

cd docker

# Use project name to create unique container: agent-claude, agent-qa, etc.
PROJECT_NAME="agent-${QMS_USER}"

# Stop any existing container for this agent
docker-compose -p "$PROJECT_NAME" down 2>/dev/null || true

# Start container (uses entrypoint which configures MCP)
if docker-compose -p "$PROJECT_NAME" up -d --build claude-agent 2>/dev/null; then
    echo -e "      ${GREEN}✓${NC} Container running"
else
    echo -e "      ${RED}✗${NC} Failed to start container"
    exit 1
fi

cd "$SCRIPT_DIR"

# --- Step 4: Verify MCP connectivity ---
echo -e "${YELLOW}[4/5]${NC} Verifying MCP connectivity..."

cd docker

for i in {1..5}; do
    HTTP_CODE=$(docker-compose -p "$PROJECT_NAME" exec -T claude-agent curl -s -o /dev/null --max-time 3 -w "%{http_code}" http://host.docker.internal:8000/mcp 2>/dev/null | tail -1)
    if echo "$HTTP_CODE" | grep -qE "^[0-9]+$" && [ "$HTTP_CODE" -gt 0 ]; then
        echo -e "      ${GREEN}✓${NC} Container can reach QMS MCP (HTTP $HTTP_CODE)"
        break
    fi
    [ $i -eq 5 ] && echo -e "      ${RED}✗${NC} Cannot reach QMS MCP" && exit 1
    sleep 1
done

for i in {1..5}; do
    HTTP_CODE=$(docker-compose -p "$PROJECT_NAME" exec -T claude-agent curl -s -o /dev/null --max-time 3 -w "%{http_code}" http://host.docker.internal:8001/mcp 2>/dev/null | tail -1)
    if echo "$HTTP_CODE" | grep -qE "^[0-9]+$" && [ "$HTTP_CODE" -gt 0 ]; then
        echo -e "      ${GREEN}✓${NC} Container can reach Git MCP (HTTP $HTTP_CODE)"
        break
    fi
    [ $i -eq 5 ] && echo -e "      ${RED}✗${NC} Cannot reach Git MCP" && exit 1
    sleep 1
done

cd "$SCRIPT_DIR"

# --- Step 5: Launch Claude ---
echo -e "${YELLOW}[5/5]${NC} Launching Claude Code as $QMS_USER..."
echo ""
echo -e "${GREEN}════════════════════════════════════════${NC}"
echo -e "  Agent: ${YELLOW}$QMS_USER${NC}"
echo -e "  MCP tools available. Type ${YELLOW}exit${NC} to leave."
echo -e "${GREEN}════════════════════════════════════════${NC}"
echo ""

cd docker
docker-compose -p "$PROJECT_NAME" exec claude-agent claude
cd "$SCRIPT_DIR"

# Post-session
echo ""
echo -e "${GREEN}Session ended for $QMS_USER.${NC}"

# Optionally stop container (comment out to keep running)
# cd docker && docker-compose -p "$PROJECT_NAME" down && cd "$SCRIPT_DIR"

if [ -f ".qms-mcp-server.pid" ] || [ -f ".git-mcp-server.pid" ]; then
    echo -e "MCP servers still running. To stop: ${YELLOW}kill \$(cat .qms-mcp-server.pid) \$(cat .git-mcp-server.pid)${NC}"
fi

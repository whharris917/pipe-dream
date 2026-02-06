#!/bin/bash
# claude-session-v3.sh - Multi-agent session with proper agent identity
#
# Usage: ./claude-session-v3.sh [agent_name]
# Example: ./claude-session-v3.sh qa
#
# Uses docker run with entrypoint preserved (not bypassed).
# For non-claude agents, mounts their definition file as CLAUDE.md.

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

# For non-claude agents, verify definition file exists
if [ "$QMS_USER" != "claude" ]; then
    if [ ! -f "$SCRIPT_DIR/.claude/agents/${QMS_USER}.md" ]; then
        echo "Error: Agent definition file not found: .claude/agents/${QMS_USER}.md"
        exit 1
    fi
fi

# Colors
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
        [ $i -eq 10 ] && echo -e "      ${RED}✗${NC} QMS MCP server failed" && exit 1
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
        [ $i -eq 10 ] && echo -e "      ${RED}✗${NC} Git MCP server failed" && exit 1
        sleep 1
    done
fi

# --- Step 3: Build image if needed ---
echo -e "${YELLOW}[3/5]${NC} Checking Docker image..."

if docker image inspect docker-claude-agent:latest >/dev/null 2>&1; then
    echo -e "      ${GREEN}✓${NC} Image exists"
else
    echo -e "      Building image..."
    cd docker
    docker-compose build claude-agent
    cd "$SCRIPT_DIR"
    echo -e "      ${GREEN}✓${NC} Image built"
fi

# --- Step 4: Start container with docker run (preserving entrypoint) ---
echo -e "${YELLOW}[4/5]${NC} Starting container for $QMS_USER..."

CONTAINER_NAME="agent-${QMS_USER}"

# Remove existing container
docker rm -f "$CONTAINER_NAME" 2>/dev/null || true

# Convert paths for Windows/Git Bash (MSYS path translation fix)
WIN_SCRIPT_DIR=$(cygpath -w "$SCRIPT_DIR" 2>/dev/null || echo "$SCRIPT_DIR")
WIN_HOME=$(cygpath -w "$HOME" 2>/dev/null || echo "$HOME")

# Build docker run command as a string to use with MSYS_NO_PATHCONV
DOCKER_CMD="docker run -it --rm"
DOCKER_CMD+=" --name $CONTAINER_NAME"
DOCKER_CMD+=" --hostname $QMS_USER"
DOCKER_CMD+=" -w /pipe-dream"
DOCKER_CMD+=" -e HOME=/"
DOCKER_CMD+=" -e CLAUDE_CONFIG_DIR=/claude-config"
DOCKER_CMD+=" -e MCP_TIMEOUT=60000"
DOCKER_CMD+=" -e QMS_USER=$QMS_USER"
[ -n "${GH_TOKEN:-}" ] && DOCKER_CMD+=" -e GH_TOKEN=$GH_TOKEN"
DOCKER_CMD+=" --add-host=host.docker.internal:host-gateway"

# Volume mounts (using Windows paths)
DOCKER_CMD+=" -v \"${WIN_SCRIPT_DIR}:/pipe-dream:ro\""
DOCKER_CMD+=" -v \"${WIN_SCRIPT_DIR}/.claude/users/${QMS_USER}/workspace:/pipe-dream/.claude/users/${QMS_USER}/workspace:rw\""
DOCKER_CMD+=" -v \"${WIN_SCRIPT_DIR}/.claude/sessions:/pipe-dream/.claude/sessions:rw\""
DOCKER_CMD+=" -v \"${WIN_SCRIPT_DIR}/docker/.mcp.json:/pipe-dream/.mcp.json:ro\""
DOCKER_CMD+=" -v \"${WIN_SCRIPT_DIR}/docker/.claude-settings.json:/pipe-dream/.claude/settings.local.json:ro\""
DOCKER_CMD+=" -v \"${WIN_HOME}/.ssh:/.ssh:ro\""
DOCKER_CMD+=" -v \"${WIN_SCRIPT_DIR}/.claude/users/${QMS_USER}/container:/claude-config:rw\""

# For non-claude agents, mount their definition as CLAUDE.md
if [ "$QMS_USER" != "claude" ]; then
    DOCKER_CMD+=" -v \"${WIN_SCRIPT_DIR}/.claude/agents/${QMS_USER}.md:/pipe-dream/CLAUDE.md:ro\""
fi

DOCKER_CMD+=" docker-claude-agent"

# Start container DETACHED first (like docker-compose up -d)
# This lets entrypoint configure MCP before we attach
# Remove -it and --rm, add -d for detached mode
DOCKER_CMD_DETACHED="${DOCKER_CMD/-it --rm/-d}"
echo -e "      Starting container..."
MSYS_NO_PATHCONV=1 eval "$DOCKER_CMD_DETACHED"

# Wait for entrypoint to complete MCP configuration
echo -e "      Waiting for MCP configuration..."
sleep 3

# Now exec into the container (like docker-compose exec)
echo -e "      ${GREEN}✓${NC} Container ready"
echo ""
echo -e "${GREEN}════════════════════════════════════════${NC}"
echo -e "  Agent: ${YELLOW}$QMS_USER${NC}"
echo -e "  MCP tools available. Type ${YELLOW}exit${NC} to leave."
echo -e "${GREEN}════════════════════════════════════════${NC}"
echo ""

MSYS_NO_PATHCONV=1 docker exec -it "$CONTAINER_NAME" claude

# Stop container after session
docker stop "$CONTAINER_NAME" >/dev/null 2>&1 || true
docker rm "$CONTAINER_NAME" >/dev/null 2>&1 || true

# Post-session
echo ""
echo -e "${GREEN}Session ended for $QMS_USER.${NC}"

if [ -f ".qms-mcp-server.pid" ] || [ -f ".git-mcp-server.pid" ]; then
    echo -e "MCP servers still running. To stop: ${YELLOW}kill \$(cat .qms-mcp-server.pid) \$(cat .git-mcp-server.pid)${NC}"
fi

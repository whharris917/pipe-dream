#!/bin/bash
# claude-session.sh - Single-command Claude container session
#
# Usage: ./claude-session.sh [agent_name]
# Example: ./claude-session.sh qa
#
# This script:
# 1. Starts the QMS MCP server on the host (if not running)
# 2. Starts the Git MCP server on the host (if not running)
# 3. Starts the Claude agent container for the specified agent
# 4. Verifies MCP connectivity from inside the container
# 5. Launches Claude Code inside the container with MCP auto-configured
#
# For non-claude agents, the agent definition file (.claude/agents/{agent}.md)
# is mounted as CLAUDE.md so the agent loads its specific context.
#
# MCP servers run in the background. To stop them:
#   kill $(cat .qms-mcp-server.pid) $(cat .git-mcp-server.pid)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# --- Agent Configuration ---
QMS_USER="${1:-claude}"

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
    echo -e "${RED}Error:${NC} Invalid agent name '$QMS_USER'"
    echo "Valid agents: ${VALID_AGENTS[*]}"
    exit 1
fi

# Ensure agent container directory exists
AGENT_CONFIG_DIR="$SCRIPT_DIR/.claude/users/$QMS_USER/container"
if [ ! -d "$AGENT_CONFIG_DIR" ]; then
    echo "Creating config directory for $QMS_USER..."
    mkdir -p "$AGENT_CONFIG_DIR"
fi

# For non-claude agents, verify agent definition file exists
if [ "$QMS_USER" != "claude" ]; then
    AGENT_DEF_FILE="$SCRIPT_DIR/.claude/agents/${QMS_USER}.md"
    if [ ! -f "$AGENT_DEF_FILE" ]; then
        echo -e "${RED}Error:${NC} Agent definition file not found: $AGENT_DEF_FILE"
        exit 1
    fi
fi

export QMS_USER

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}════════════════════════════════════════${NC}"
echo -e "${GREEN}  Agent Container Session: ${YELLOW}$QMS_USER${GREEN}${NC}"
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
echo -e "${YELLOW}[3/5]${NC} Starting container for $QMS_USER..."

cd docker

# Check if image exists, skip build if it does (avoids hangs in subshells)
if ! docker image inspect docker-claude-agent:latest >/dev/null 2>&1; then
    echo -e "      Building image (first time only)..."
    docker-compose build --quiet claude-agent </dev/null 2>/dev/null || true
fi

# Build the docker run command with all necessary mounts
# We use docker run directly (not docker-compose run) to support dynamic CLAUDE.md mounting
# On Windows/Git Bash, we need MSYS_NO_PATHCONV=1 and Windows-style paths for volumes

# Convert Git Bash paths to Windows paths for Docker volume mounts
WIN_SCRIPT_DIR=$(cygpath -w "$SCRIPT_DIR" 2>/dev/null || echo "$SCRIPT_DIR" | sed 's|^/c/|C:/|; s|^/d/|D:/|')
WIN_HOME=$(cygpath -w "$HOME" 2>/dev/null || echo "$HOME" | sed 's|^/c/|C:/|; s|^/d/|D:/|')

DOCKER_RUN_CMD="docker run -d --name agent-${QMS_USER}"
DOCKER_RUN_CMD+=" --hostname ${QMS_USER}"
DOCKER_RUN_CMD+=" -w /pipe-dream"

# Environment variables
DOCKER_RUN_CMD+=" -e HOME=/"
DOCKER_RUN_CMD+=" -e CLAUDE_CONFIG_DIR=/claude-config"
DOCKER_RUN_CMD+=" -e MCP_TIMEOUT=60000"
DOCKER_RUN_CMD+=" -e QMS_USER=${QMS_USER}"
[ -n "${GH_TOKEN:-}" ] && DOCKER_RUN_CMD+=" -e GH_TOKEN=${GH_TOKEN}"

# Volume mounts using Windows paths
DOCKER_RUN_CMD+=" -v \"${WIN_SCRIPT_DIR}:/pipe-dream:ro\""
DOCKER_RUN_CMD+=" -v \"${WIN_SCRIPT_DIR}/.claude/users/${QMS_USER}/workspace:/pipe-dream/.claude/users/${QMS_USER}/workspace:rw\""
DOCKER_RUN_CMD+=" -v \"${WIN_SCRIPT_DIR}/.claude/sessions:/pipe-dream/.claude/sessions:rw\""
DOCKER_RUN_CMD+=" -v \"${WIN_SCRIPT_DIR}/docker/.mcp.json:/pipe-dream/.mcp.json:ro\""
DOCKER_RUN_CMD+=" -v \"${WIN_SCRIPT_DIR}/docker/.claude-settings.json:/pipe-dream/.claude/settings.local.json:ro\""
DOCKER_RUN_CMD+=" -v \"${WIN_HOME}/.ssh:/.ssh:ro\""
DOCKER_RUN_CMD+=" -v \"${WIN_SCRIPT_DIR}/.claude/users/${QMS_USER}/container:/claude-config:rw\""

# For non-claude agents, mount their agent definition as CLAUDE.md
if [ "$QMS_USER" != "claude" ]; then
    DOCKER_RUN_CMD+=" -v \"${WIN_SCRIPT_DIR}/.claude/agents/${QMS_USER}.md:/pipe-dream/CLAUDE.md:ro\""
fi

# Network settings
DOCKER_RUN_CMD+=" --add-host=host.docker.internal:host-gateway"

# Override entrypoint to just keep container running
# The normal entrypoint runs `claude` which needs a TTY
# We'll run the MCP setup and claude manually via docker exec
DOCKER_RUN_CMD+=" --entrypoint /bin/bash"
DOCKER_RUN_CMD+=" docker-claude-agent"
DOCKER_RUN_CMD+=" -c \"sleep infinity\""

# Remove any existing container with this name
docker rm -f "agent-${QMS_USER}" 2>/dev/null || true

# Debug: show the command (uncomment to troubleshoot)
# echo "DEBUG: $DOCKER_RUN_CMD"

# Start the container (MSYS_NO_PATHCONV prevents Git Bash path translation)
if MSYS_NO_PATHCONV=1 eval "$DOCKER_RUN_CMD" >/dev/null 2>&1; then
    echo -e "      ${GREEN}✓${NC} Container running (agent-${QMS_USER})"
else
    echo -e "      ${RED}✗${NC} Failed to start container"
    echo -e "      Try: docker logs agent-${QMS_USER}"
    exit 1
fi

cd "$SCRIPT_DIR"

# --- Step 4: Verify MCP connectivity from container ---
echo -e "${YELLOW}[4/5]${NC} Verifying MCP connectivity from container..."

# Check QMS MCP server
for i in {1..5}; do
    HTTP_CODE=$(docker exec -t "agent-${QMS_USER}" curl -s -o /dev/null --max-time 3 -w "%{http_code}" http://host.docker.internal:8000/mcp 2>/dev/null | tail -1 | tr -d '\r')
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
    HTTP_CODE=$(docker exec -t "agent-${QMS_USER}" curl -s -o /dev/null --max-time 3 -w "%{http_code}" http://host.docker.internal:8001/mcp 2>/dev/null | tail -1 | tr -d '\r')
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

# --- Step 5: Configure MCP servers in container ---
echo -e "${YELLOW}[5/6]${NC} Configuring MCP servers..."

CONTAINER="agent-${QMS_USER}"

# Remove old marker files - we always reconfigure since each container is fresh
# The marker files persist in the mounted volume, but Claude Code's config doesn't
docker exec "$CONTAINER" bash -c "rm -f /claude-config/.mcp-configured /claude-config/.git-mcp-configured" 2>/dev/null || true

# Configure QMS MCP server (same as entrypoint.sh)
echo -e "      Configuring QMS MCP server..."
if docker exec "$CONTAINER" claude mcp add --transport http --scope user \
    --header "X-API-Key: qms-internal" \
    --header "Authorization: Bearer internal-trusted" \
    qms "http://host.docker.internal:8000/mcp"; then
    echo -e "      ${GREEN}✓${NC} QMS MCP server configured"
else
    echo -e "      ${YELLOW}!${NC} QMS MCP config returned non-zero (may already exist)"
fi

# Configure Git MCP server
echo -e "      Configuring Git MCP server..."
if docker exec "$CONTAINER" claude mcp add --transport http --scope user \
    git "http://host.docker.internal:8001/mcp"; then
    echo -e "      ${GREEN}✓${NC} Git MCP server configured"
else
    echo -e "      ${YELLOW}!${NC} Git MCP config returned non-zero (may already exist)"
fi

# Configure GitHub CLI if token provided
if [ -n "${GH_TOKEN:-}" ]; then
    echo -e "      Configuring GitHub CLI..."
    docker exec "$CONTAINER" bash -c "echo '$GH_TOKEN' | gh auth login --with-token 2>/dev/null" || true
    docker exec "$CONTAINER" gh auth setup-git 2>/dev/null || true
    echo -e "      ${GREEN}✓${NC} GitHub CLI configured"
fi

# --- Step 6: Launch Claude ---
echo -e "${YELLOW}[6/6]${NC} Launching Claude Code as $QMS_USER..."
echo ""
echo -e "${GREEN}════════════════════════════════════════${NC}"
echo -e "  Agent: ${YELLOW}$QMS_USER${NC}"
echo -e "  MCP tools (qms_inbox, git_exec, etc.) work automatically."
echo -e "  Type ${YELLOW}exit${NC} to leave the session."
echo -e "${GREEN}════════════════════════════════════════${NC}"
echo ""

# Exec into container and run claude
docker exec -it "agent-${QMS_USER}" claude

# Post-session cleanup: stop and remove the container
echo ""
echo -e "${GREEN}Session ended for $QMS_USER.${NC}"
docker stop "agent-${QMS_USER}" >/dev/null 2>&1 || true
docker rm "agent-${QMS_USER}" >/dev/null 2>&1 || true

if [ -f ".qms-mcp-server.pid" ] || [ -f ".git-mcp-server.pid" ]; then
    echo -e "MCP servers still running:"
    [ -f ".qms-mcp-server.pid" ] && echo -e "  QMS: PID $(cat .qms-mcp-server.pid)"
    [ -f ".git-mcp-server.pid" ] && echo -e "  Git: PID $(cat .git-mcp-server.pid)"
    echo -e "To stop them: ${YELLOW}kill \$(cat .qms-mcp-server.pid) \$(cat .git-mcp-server.pid)${NC}"
fi

#!/bin/bash
# launch.sh - Unified container launcher for Pipe Dream agents
#
# Usage:
#   ./launch.sh              # Launch claude in current terminal
#   ./launch.sh qa           # Launch qa in current terminal
#   ./launch.sh claude qa    # Launch both in separate terminals + Agent Hub
#
# Replaces: claude-session.sh, claude-session-v2/v3.sh, multi-agent-session.sh
#
# Design: Uses "docker run -d -e SETUP_ONLY=1" to start a detached container
# where the entrypoint does setup then sleeps. Then "docker exec -it" attaches
# the interactive Claude session. This avoids the race condition where the
# entrypoint's "exec claude" exits immediately in detached mode.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# --- Colors ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# --- Constants ---
VALID_AGENTS=("claude" "qa" "tu_ui" "tu_scene" "tu_sketch" "tu_sim" "bu")
IMAGE_NAME="docker-claude-agent"

# ============================================================================
# Functions
# ============================================================================

validate_agent() {
    local agent="$1"
    for valid in "${VALID_AGENTS[@]}"; do
        [ "$agent" = "$valid" ] && return 0
    done
    echo -e "${RED}Error:${NC} Invalid agent name '$agent'"
    echo "Valid agents: ${VALID_AGENTS[*]}"
    exit 1
}

find_python() {
    if [ -f "$SCRIPT_DIR/.venv/Scripts/python.exe" ]; then
        echo "$SCRIPT_DIR/.venv/Scripts/python.exe"
    elif [ -f "$SCRIPT_DIR/.venv/bin/python" ]; then
        echo "$SCRIPT_DIR/.venv/bin/python"
    else
        echo -e "${RED}Error:${NC} No Python venv found at .venv/" >&2
        exit 1
    fi
}

ensure_mcp_servers() {
    local python_exe
    python_exe=$(find_python)

    # QMS MCP server (port 8000)
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/mcp 2>/dev/null | grep -qE "200|40[0-9]"; then
        echo -e "  ${GREEN}✓${NC} QMS MCP server already running"
    else
        echo -e "  Starting QMS MCP server..."
        cd "$SCRIPT_DIR/qms-cli"
        "$python_exe" -m qms_mcp --transport streamable-http --host 0.0.0.0 --port 8000 \
            --project-root "$SCRIPT_DIR" > "$SCRIPT_DIR/.qms-mcp-server.log" 2>&1 &
        echo $! > "$SCRIPT_DIR/.qms-mcp-server.pid"
        cd "$SCRIPT_DIR"
        for i in {1..10}; do
            if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/mcp 2>/dev/null | grep -qE "200|40[0-9]"; then
                echo -e "  ${GREEN}✓${NC} QMS MCP server started"
                break
            fi
            [ $i -eq 10 ] && echo -e "  ${RED}✗${NC} QMS MCP server failed to start" && exit 1
            sleep 1
        done
    fi

    # Git MCP server (port 8001)
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/mcp 2>/dev/null | grep -qE "200|40[0-9]"; then
        echo -e "  ${GREEN}✓${NC} Git MCP server already running"
    else
        echo -e "  Starting Git MCP server..."
        cd "$SCRIPT_DIR"
        "$python_exe" -m git_mcp --transport streamable-http --host 0.0.0.0 --port 8001 \
            --project-root "$SCRIPT_DIR" > "$SCRIPT_DIR/.git-mcp-server.log" 2>&1 &
        echo $! > "$SCRIPT_DIR/.git-mcp-server.pid"
        for i in {1..10}; do
            if curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/mcp 2>/dev/null | grep -qE "200|40[0-9]"; then
                echo -e "  ${GREEN}✓${NC} Git MCP server started"
                break
            fi
            [ $i -eq 10 ] && echo -e "  ${RED}✗${NC} Git MCP server failed to start" && exit 1
            sleep 1
        done
    fi
}

ensure_image() {
    if docker image inspect "$IMAGE_NAME:latest" >/dev/null 2>&1; then
        echo -e "  ${GREEN}✓${NC} Docker image exists"
    else
        echo -e "  Building Docker image..."
        cd "$SCRIPT_DIR/docker"
        docker-compose build claude-agent
        cd "$SCRIPT_DIR"
        echo -e "  ${GREEN}✓${NC} Docker image built"
    fi
}

start_container() {
    local agent="$1"
    local container_name="agent-${agent}"

    # Ensure agent directories exist
    mkdir -p "$SCRIPT_DIR/.claude/users/$agent/container"
    mkdir -p "$SCRIPT_DIR/.claude/users/$agent/workspace"

    # For non-claude agents, verify definition file exists
    if [ "$agent" != "claude" ]; then
        if [ ! -f "$SCRIPT_DIR/.claude/agents/${agent}.md" ]; then
            echo -e "${RED}Error:${NC} Agent definition file not found: .claude/agents/${agent}.md"
            exit 1
        fi
    fi

    # Remove any existing container with this name
    docker rm -f "$container_name" 2>/dev/null || true

    # Convert paths for Windows/Git Bash (MSYS path translation fix)
    local win_script_dir win_home
    win_script_dir=$(cygpath -w "$SCRIPT_DIR" 2>/dev/null || echo "$SCRIPT_DIR")
    win_home=$(cygpath -w "$HOME" 2>/dev/null || echo "$HOME")

    # Load GH_TOKEN from docker/.env if not already set
    if [ -z "${GH_TOKEN:-}" ] && [ -f "$SCRIPT_DIR/docker/.env" ]; then
        GH_TOKEN=$(grep -E '^GH_TOKEN=' "$SCRIPT_DIR/docker/.env" 2>/dev/null | cut -d= -f2-)
    fi

    # Build docker run command
    local cmd="docker run -d"
    cmd+=" --name $container_name"
    cmd+=" --hostname $agent"
    cmd+=" -w /pipe-dream"
    cmd+=" -e HOME=/"
    cmd+=" -e CLAUDE_CONFIG_DIR=/claude-config"
    cmd+=" -e MCP_TIMEOUT=60000"
    cmd+=" -e QMS_USER=$agent"
    cmd+=" -e SETUP_ONLY=1"
    [ -n "${GH_TOKEN:-}" ] && cmd+=" -e GH_TOKEN=$GH_TOKEN"
    cmd+=" --add-host=host.docker.internal:host-gateway"

    # Volume mounts
    cmd+=" -v \"${win_script_dir}:/pipe-dream:ro\""
    cmd+=" -v \"${win_script_dir}/.claude/users/${agent}/workspace:/pipe-dream/.claude/users/${agent}/workspace:rw\""
    cmd+=" -v \"${win_script_dir}/.claude/sessions:/pipe-dream/.claude/sessions:rw\""
    cmd+=" -v \"${win_script_dir}/docker/.mcp.json:/pipe-dream/.mcp.json:ro\""
    cmd+=" -v \"${win_script_dir}/docker/.claude-settings.json:/pipe-dream/.claude/settings.local.json:ro\""
    cmd+=" -v \"${win_home}/.ssh:/.ssh:ro\""
    cmd+=" -v \"${win_script_dir}/.claude/users/${agent}/container:/claude-config:rw\""

    # For non-claude agents, mount their definition as CLAUDE.md
    if [ "$agent" != "claude" ]; then
        cmd+=" -v \"${win_script_dir}/.claude/agents/${agent}.md:/pipe-dream/CLAUDE.md:ro\""
    fi

    cmd+=" $IMAGE_NAME"

    # Start container detached with SETUP_ONLY=1
    MSYS_NO_PATHCONV=1 eval "$cmd"

    # Wait for entrypoint setup to complete
    local max_wait=15
    for i in $(seq 1 $max_wait); do
        if docker logs "$container_name" 2>&1 | grep -q "Setup complete. Waiting for docker exec"; then
            return 0
        fi
        if ! docker inspect -f '{{.State.Running}}' "$container_name" 2>/dev/null | grep -q true; then
            echo -e "  ${RED}✗${NC} Container $container_name exited unexpectedly"
            docker logs "$container_name" 2>&1 | tail -5
            return 1
        fi
        sleep 1
    done

    # If we didn't see the message but container is running, proceed anyway
    if docker inspect -f '{{.State.Running}}' "$container_name" 2>/dev/null | grep -q true; then
        return 0
    fi

    echo -e "  ${RED}✗${NC} Container $container_name failed to start"
    return 1
}

stop_container() {
    local agent="$1"
    local container_name="agent-${agent}"
    docker stop "$container_name" >/dev/null 2>&1 || true
    docker rm "$container_name" >/dev/null 2>&1 || true
}

launch_claude() {
    local agent="$1"
    local container_name="agent-${agent}"

    echo ""
    echo -e "${GREEN}════════════════════════════════════════${NC}"
    echo -e "  Agent: ${YELLOW}$agent${NC}"
    echo -e "  MCP tools available. Type ${YELLOW}exit${NC} to leave."
    echo -e "${GREEN}════════════════════════════════════════${NC}"
    echo ""

    MSYS_NO_PATHCONV=1 docker exec -it "$container_name" tmux new-session -s agent "claude"

    # Cleanup after session ends
    stop_container "$agent"
    echo ""
    echo -e "${GREEN}Session ended for $agent.${NC}"
}

launch_in_terminal() {
    local agent="$1"
    local script_path
    script_path=$(cygpath -w "$SCRIPT_DIR/launch.sh" 2>/dev/null || echo "$SCRIPT_DIR/launch.sh")

    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "mingw"* || "$OSTYPE" == "cygwin" ]]; then
        start "" mintty -t "Agent: $agent" -e bash -l -c "cd '$SCRIPT_DIR' && ./launch.sh '$agent'; read -p 'Press Enter to close...'"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        osascript -e "tell application \"Terminal\" to do script \"cd '$SCRIPT_DIR' && ./launch.sh '$agent'\""
    elif command -v gnome-terminal &> /dev/null; then
        gnome-terminal --title="Agent: $agent" -- bash -c "cd '$SCRIPT_DIR' && ./launch.sh '$agent'; read -p 'Press Enter to close...'" &
    elif command -v xterm &> /dev/null; then
        xterm -title "Agent: $agent" -e bash -c "cd '$SCRIPT_DIR' && ./launch.sh '$agent'; read -p 'Press Enter to close...'" &
    elif command -v konsole &> /dev/null; then
        konsole --new-tab -e bash -c "cd '$SCRIPT_DIR' && ./launch.sh '$agent'; read -p 'Press Enter to close...'" &
    else
        echo -e "${RED}Error:${NC} No supported terminal emulator found"
        exit 1
    fi
}

ensure_hub() {
    # Check if Hub is already running
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:9000/api/health 2>/dev/null | grep -q "200"; then
        echo -e "  ${GREEN}✓${NC} Agent Hub already running"
        return 0
    fi

    echo -e "  Starting Agent Hub..."
    local python_exe
    python_exe=$(find_python)

    cd "$SCRIPT_DIR"
    "$python_exe" -m agent_hub.cli start --project-root "$SCRIPT_DIR" \
        > "$SCRIPT_DIR/.agent-hub.log" 2>&1 &
    echo $! > "$SCRIPT_DIR/.agent-hub.pid"

    for i in {1..10}; do
        if curl -s -o /dev/null -w "%{http_code}" http://localhost:9000/api/health 2>/dev/null | grep -q "200"; then
            echo -e "  ${GREEN}✓${NC} Agent Hub started"
            return 0
        fi
        [ $i -eq 10 ] && echo -e "  ${RED}✗${NC} Agent Hub failed to start" && exit 1
        sleep 1
    done
}

# ============================================================================
# Main
# ============================================================================

# Parse arguments
AGENTS=()
for arg in "$@"; do
    validate_agent "$arg"
    AGENTS+=("$arg")
done

# Default to claude if no args
if [ ${#AGENTS[@]} -eq 0 ]; then
    AGENTS=("claude")
fi

# Determine mode: single-agent (1 arg) vs multi-agent (2+ args)
MULTI_MODE=false
if [ ${#AGENTS[@]} -gt 1 ]; then
    MULTI_MODE=true
fi

echo -e "${GREEN}════════════════════════════════════════════════${NC}"
if [ "$MULTI_MODE" = true ]; then
    echo -e "${GREEN}  Multi-Agent Session${NC}"
    echo -e "  Agents: ${CYAN}${AGENTS[*]}${NC}"
else
    echo -e "${GREEN}  Agent Container Session: ${YELLOW}${AGENTS[0]}${NC}"
fi
echo -e "${GREEN}════════════════════════════════════════════════${NC}"
echo ""

# Step 1: MCP servers
echo -e "${YELLOW}[1/4]${NC} Ensuring MCP servers..."
ensure_mcp_servers

# Step 2: Docker image
echo -e "${YELLOW}[2/4]${NC} Checking Docker image..."
ensure_image

# Step 3: Agent Hub
echo -e "${YELLOW}[3/4]${NC} Ensuring Agent Hub..."
ensure_hub

# Step 4: Launch
echo -e "${YELLOW}[4/4]${NC} Launching containers..."

if [ "$MULTI_MODE" = true ]; then
    # Multi-agent: launch each agent in its own terminal
    for agent in "${AGENTS[@]}"; do
        echo -e "  Launching ${CYAN}$agent${NC} in new terminal..."
        launch_in_terminal "$agent"
        sleep 3  # Stagger to avoid Docker race conditions
    done

    echo ""
    echo -e "${GREEN}════════════════════════════════════════════════${NC}"
    echo -e "  All agents launched!"
    echo -e ""
    echo -e "  Terminal windows:"
    for agent in "${AGENTS[@]}"; do
        echo -e "    - ${CYAN}Agent: $agent${NC}"
    done
    echo -e ""
    echo -e "  ${YELLOW}Agent Hub:${NC} http://localhost:9000/api/status"
    echo -e "  ${YELLOW}To stop services:${NC}"
    echo -e "    kill \$(cat .agent-hub.pid) \$(cat .qms-mcp-server.pid) \$(cat .git-mcp-server.pid)"
    echo -e "${GREEN}════════════════════════════════════════════════${NC}"
else
    # Single-agent: start container in this terminal, exec into it
    agent="${AGENTS[0]}"
    echo -e "  Starting container for ${CYAN}$agent${NC}..."
    start_container "$agent"
    echo -e "  ${GREEN}✓${NC} Container ready"
    launch_claude "$agent"

    # Post-session info
    echo -e "Services still running. To stop: ${YELLOW}kill \$(cat .agent-hub.pid) \$(cat .qms-mcp-server.pid) \$(cat .git-mcp-server.pid) 2>/dev/null${NC}"
fi

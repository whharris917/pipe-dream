#!/bin/bash
# multi-agent-session.sh - Launch multiple QMS agents in separate terminals
#
# Usage: ./multi-agent-session.sh [agent1] [agent2] ...
# Default: claude qa
#
# Example: ./multi-agent-session.sh claude qa tu_ui
#
# This script:
# 1. Starts the QMS MCP server on the host (if not running)
# 2. Starts the Git MCP server on the host (if not running)
# 3. Starts the inbox watcher in the background
# 4. Launches each agent in a separate terminal window
#
# On Windows (Git Bash): Uses 'start' to open new Git Bash windows
# On Linux: Uses gnome-terminal, xterm, or konsole
# On macOS: Uses Terminal.app via osascript
#
# To stop MCP servers and inbox watcher:
#   kill $(cat .qms-mcp-server.pid) $(cat .git-mcp-server.pid) $(cat .inbox-watcher.pid)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Default agents if none specified
if [ $# -eq 0 ]; then
    AGENTS=("claude" "qa")
else
    AGENTS=("$@")
fi

# Validate agent names
VALID_AGENTS=("claude" "qa" "tu_ui" "tu_scene" "tu_sketch" "tu_sim" "bu")
for agent in "${AGENTS[@]}"; do
    VALID=false
    for valid in "${VALID_AGENTS[@]}"; do
        if [ "$agent" = "$valid" ]; then
            VALID=true
            break
        fi
    done
    if [ "$VALID" = false ]; then
        echo -e "${RED}Error:${NC} Invalid agent name '$agent'"
        echo "Valid agents: ${VALID_AGENTS[*]}"
        exit 1
    fi
done

echo -e "${GREEN}════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  Multi-Agent Session${NC}"
echo -e "${GREEN}════════════════════════════════════════════════${NC}"
echo -e "  Agents: ${CYAN}${AGENTS[*]}${NC}"
echo ""

# --- Find Python executable ---
if [ -f ".venv/Scripts/python.exe" ]; then
    PYTHON_EXE="$SCRIPT_DIR/.venv/Scripts/python.exe"
elif [ -f ".venv/bin/python" ]; then
    PYTHON_EXE="$SCRIPT_DIR/.venv/bin/python"
else
    echo -e "${RED}Error:${NC} No Python venv found at .venv/"
    exit 1
fi

# --- Step 1: Start MCP servers ---
echo -e "${YELLOW}[1/4]${NC} Starting MCP servers..."

# QMS MCP server
if ! curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/mcp 2>/dev/null | grep -qE "200|40[0-9]"; then
    echo -e "      Starting QMS MCP server..."
    cd qms-cli
    "$PYTHON_EXE" -m qms_mcp --transport streamable-http --host 0.0.0.0 --port 8000 \
        --project-root "$SCRIPT_DIR" > "$SCRIPT_DIR/.qms-mcp-server.log" 2>&1 &
    echo $! > "$SCRIPT_DIR/.qms-mcp-server.pid"
    cd "$SCRIPT_DIR"
    sleep 2
    echo -e "      ${GREEN}✓${NC} QMS MCP server started"
else
    echo -e "      ${GREEN}✓${NC} QMS MCP server already running"
fi

# Git MCP server
if ! curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/mcp 2>/dev/null | grep -qE "200|40[0-9]"; then
    echo -e "      Starting Git MCP server..."
    "$PYTHON_EXE" -m git_mcp --transport streamable-http --host 0.0.0.0 --port 8001 \
        --project-root "$SCRIPT_DIR" > "$SCRIPT_DIR/.git-mcp-server.log" 2>&1 &
    echo $! > "$SCRIPT_DIR/.git-mcp-server.pid"
    sleep 2
    echo -e "      ${GREEN}✓${NC} Git MCP server started"
else
    echo -e "      ${GREEN}✓${NC} Git MCP server already running"
fi

# --- Step 2: Start inbox watcher in visible terminal ---
echo -e "${YELLOW}[2/4]${NC} Starting inbox watcher..."

# Kill any existing inbox watcher
if [ -f ".inbox-watcher.pid" ]; then
    OLD_PID=$(cat .inbox-watcher.pid)
    kill "$OLD_PID" 2>/dev/null || true
    rm -f ".inbox-watcher.pid"
fi

# Launch inbox watcher in its own terminal window so notifications are visible
WATCHER_CMD="cd '$SCRIPT_DIR' && '$PYTHON_EXE' -u docker/scripts/inbox-watcher.py ${AGENTS[*]}; read -p 'Press Enter to close...'"

if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "mingw"* || "$OSTYPE" == "cygwin" ]]; then
    # Windows: open in mintty
    start "" mintty -t "Inbox Watcher" -e bash -c "$WATCHER_CMD" &
elif [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    osascript -e "tell application \"Terminal\" to do script \"$WATCHER_CMD\""
elif command -v gnome-terminal &> /dev/null; then
    gnome-terminal --title="Inbox Watcher" -- bash -c "$WATCHER_CMD" &
elif command -v xterm &> /dev/null; then
    xterm -title "Inbox Watcher" -e bash -c "$WATCHER_CMD" &
fi

echo -e "      ${GREEN}✓${NC} Inbox watcher launched in separate terminal"

# --- Step 3: Detect terminal launcher ---
echo -e "${YELLOW}[3/4]${NC} Detecting terminal..."

launch_terminal() {
    local agent="$1"
    local cmd="cd '$SCRIPT_DIR' && ./claude-session.sh '$agent'"

    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "mingw"* || "$OSTYPE" == "cygwin" ]]; then
        # Windows (Git Bash, MSYS, Cygwin)
        # Use 'start' with mintty (Git Bash's terminal)
        # -l flag ensures login shell with proper PATH and environment
        start "" mintty -t "Agent: $agent" -e bash -l -c "$cmd; read -p 'Press Enter to close...'"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        osascript -e "tell application \"Terminal\" to do script \"$cmd\""
    elif command -v gnome-terminal &> /dev/null; then
        # Linux with GNOME
        gnome-terminal --title="Agent: $agent" -- bash -c "$cmd; read -p 'Press Enter to close...'"
    elif command -v xterm &> /dev/null; then
        # Linux with xterm
        xterm -title "Agent: $agent" -e bash -c "$cmd; read -p 'Press Enter to close...'" &
    elif command -v konsole &> /dev/null; then
        # KDE
        konsole --new-tab -e bash -c "$cmd; read -p 'Press Enter to close...'" &
    else
        echo -e "${RED}Error:${NC} No supported terminal emulator found"
        exit 1
    fi
}

# --- Step 4: Launch agent terminals ---
echo -e "${YELLOW}[4/4]${NC} Launching agent terminals..."

for agent in "${AGENTS[@]}"; do
    echo -e "      Launching ${CYAN}$agent${NC}..."
    launch_terminal "$agent"
    sleep 3  # Stagger launches to avoid race conditions with Docker/MCP
done

echo ""
echo -e "${GREEN}════════════════════════════════════════════════${NC}"
echo -e "  All agents launched!"
echo -e "  "
echo -e "  Terminal windows:"
echo -e "    - ${CYAN}Inbox Watcher${NC}: Shows notifications when tasks arrive"
echo -e "    - ${CYAN}Agent: <name>${NC}: Each agent's Claude Code session"
echo -e "  "
echo -e "  When a task is routed to an agent, the Inbox Watcher will"
echo -e "  display a notification. Switch to that agent's terminal"
echo -e "  and run ${YELLOW}qms inbox${NC} to process the task."
echo -e "  "
echo -e "  ${YELLOW}To stop MCP servers:${NC}"
echo -e "    kill \$(cat .qms-mcp-server.pid) \$(cat .git-mcp-server.pid)"
echo -e "${GREEN}════════════════════════════════════════════════${NC}"

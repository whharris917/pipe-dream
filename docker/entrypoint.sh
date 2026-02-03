#!/bin/bash
# Entrypoint script for Claude container
# Initializes config directory on first run, then starts Claude

CONFIG_DIR="${CLAUDE_CONFIG_DIR:-/claude-config}"
INIT_CONFIG="/init-config/.claude.json"

# First run: copy initial MCP config if no config exists yet
if [ ! -f "$CONFIG_DIR/.claude.json" ] && [ -f "$INIT_CONFIG" ]; then
    echo "First run detected - initializing config with MCP server..."
    cp "$INIT_CONFIG" "$CONFIG_DIR/.claude.json"
fi

# Start Claude Code
exec claude "$@"

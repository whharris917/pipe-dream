FROM python:3.11-slim

# Set container root as home
ENV HOME=/
WORKDIR /

# Install system dependencies
# Note: python3-venv added per CR-043-VAR-001 for development environment support
RUN apt-get update && apt-get install -y \
    git \
    curl \
    nodejs \
    npm \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

# Install Claude Code CLI
RUN npm install -g @anthropic-ai/claude-code

# Create directory structure
RUN mkdir -p /projects /pipe-dream /.claude /.ssh /init-config /claude-config

# Copy baked-in MCP configuration (project-scoped, kept for reference)
COPY .mcp.json /.mcp.json

# Copy initial config with user-scoped MCP server (for first-run initialization)
# The entrypoint script copies this to CLAUDE_CONFIG_DIR on first run
COPY .claude-container.json /init-config/.claude.json

# Copy entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Default git config (can be overridden by mount)
RUN git config --global init.defaultBranch main

# Entry point - initialize config and start Claude Code
ENTRYPOINT ["/entrypoint.sh"]
CMD []

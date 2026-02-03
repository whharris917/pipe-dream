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
RUN mkdir -p /projects /pipe-dream /.claude /.ssh

# Copy baked-in MCP configuration (project-scoped, kept for reference)
COPY .mcp.json /.mcp.json

# Copy user-scoped MCP configuration (auto-connects without approval prompt)
# User-scoped servers bypass the project trust dialog per CR-052
COPY .claude-container.json /.claude.json

# Default git config (can be overridden by mount)
RUN git config --global init.defaultBranch main

# Entry point - start Claude Code
CMD ["claude"]

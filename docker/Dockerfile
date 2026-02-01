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

# Copy baked-in MCP configuration
COPY .mcp.json /.mcp.json

# Default git config (can be overridden by mount)
RUN git config --global init.defaultBranch main

# Entry point - start Claude Code
CMD ["claude"]

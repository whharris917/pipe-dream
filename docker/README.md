# Claude Agent Container Infrastructure

This directory contains Docker infrastructure for running Claude agents in isolated containers with controlled access to the QMS and codebase.

## Overview

The container provides:
- **Isolation**: Claude runs in a container with restricted filesystem access
- **Read-only QMS access**: Production QMS files are mounted read-only
- **Controlled write access**: Only workspace and /projects/ are writable
- **MCP connectivity**: All QMS operations flow through the host MCP server

## Quick Start

### 1. Start the MCP Server (on host)

```bash
cd docker/scripts
./start-mcp-server.sh
```

Or manually:
```bash
python -m qms_mcp --transport streamable-http --host 0.0.0.0 --port 8000 --project-root /path/to/pipe-dream
```

### 2. Start the Container

```bash
cd docker
docker-compose up -d
docker-compose exec claude-agent bash
```

Or use the convenience script:
```bash
./scripts/start-container.sh
```

## Filesystem Structure

```
/                                      # Container root (HOME=/)
├── .mcp.json                          # MCP connection config (baked in)
├── .claude/
│   └── .credentials.json              # Auth credentials (mounted from host)
├── .ssh/                              # Deploy keys (mounted from host)
│
├── projects/                          # [READ-WRITE] Development workspace
│   └── {repo}/                        # Cloned repositories
│       └── .venv/                     # Python virtual environments
│
└── pipe-dream/                        # Production QMS mount
    ├── CLAUDE.md                      # [READ-ONLY]
    ├── QMS/                           # [READ-ONLY]
    ├── flow-state/                    # [READ-ONLY]
    ├── qms-cli/                       # [READ-ONLY]
    └── .claude/users/claude/
        ├── inbox/                     # [READ-ONLY]
        └── workspace/                 # [READ-WRITE] QMS document checkout
```

## Access Control

| Path | Access | Purpose |
|------|--------|---------|
| `/` (root dotfiles) | R/W | Agent configuration |
| `/projects/` | R/W | Code development and testing |
| `/pipe-dream/` | Read-only | Production QMS reference |
| `/pipe-dream/.claude/users/claude/workspace/` | R/W | QMS document checkout |

## Development Workflows

### Working on Code

1. Clone repository into `/projects/`:
   ```bash
   cd /projects
   git clone https://github.com/whharris917/flow-state.git
   cd flow-state
   ```

2. Create feature branch:
   ```bash
   git checkout -b cr-XXX-feature
   ```

3. Set up Python environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

4. Develop, test, commit, push

### Working on QMS Documents

QMS operations flow through the MCP server:

1. Check inbox: Use `qms_inbox()` MCP tool
2. Checkout document: Use `qms_checkout("CR-XXX")` MCP tool
3. Edit in workspace: `/pipe-dream/.claude/users/claude/workspace/`
4. Check in: Use `qms_checkin("CR-XXX")` MCP tool

## Prerequisites

- Docker Desktop (Mac/Windows) or Docker Engine (Linux)
- Claude Code credentials (`~/.claude/.credentials.json` on host)
- SSH keys for GitHub (`~/.ssh/` on host)

## Troubleshooting

### Container cannot reach MCP server

1. Verify MCP server is running on host:
   ```bash
   curl http://localhost:8000/mcp
   ```

2. On Linux, ensure `host.docker.internal` is configured:
   ```bash
   # docker-compose.yml already includes:
   extra_hosts:
     - "host.docker.internal:host-gateway"
   ```

### Permission denied on workspace

The workspace directory must exist on the host:
```bash
mkdir -p .claude/users/claude/workspace
```

### Claude Code authentication fails

Verify credentials are mounted:
```bash
ls -la /.claude/.credentials.json
```

If missing, ensure `~/.claude/.credentials.json` exists on host.

## Building the Image

```bash
cd docker
docker-compose build
```

Or:
```bash
docker build -t claude-agent .
```

## References

- CR-042: Add Remote Transport Support to QMS MCP Server
- CR-043: Implement Containerized Claude Agent Infrastructure

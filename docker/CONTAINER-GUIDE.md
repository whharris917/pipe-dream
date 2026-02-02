# Containerized Claude Agent Guide

This guide explains how to run Claude Code inside a Docker container with full QMS access via MCP.

## Overview

The containerized architecture provides:
- **Isolation:** Claude operates in a sandboxed environment
- **Read-only production access:** Cannot directly modify QMS files or qualified code
- **MCP-mediated writes:** All QMS operations flow through the host MCP server
- **Session persistence:** Session data survives container restarts

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         HOST                                 │
│  ┌─────────────────┐    ┌─────────────────────────────────┐ │
│  │   MCP Server    │    │      pipe-dream/                │ │
│  │  (streamable-   │◄───│  ├── QMS/        (production)   │ │
│  │    http)        │    │  ├── qms-cli/    (qualified)    │ │
│  │  Port 8000      │    │  ├── flow-state/ (qualified)    │ │
│  └────────┬────────┘    │  └── .claude/    (sessions)     │ │
│           │             └─────────────────────────────────┘ │
│           │ HTTP                                             │
│           │ host.docker.internal:8000                        │
├───────────┼─────────────────────────────────────────────────┤
│           ▼              CONTAINER                           │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  Claude Code                                             ││
│  │  ├── /pipe-dream/           (read-only mount)           ││
│  │  ├── /pipe-dream/.claude/sessions/  (read-write)        ││
│  │  └── /pipe-dream/.claude/users/claude/workspace/ (rw)   ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

## Prerequisites

- Docker Desktop installed and running
- Python environment with `mcp` package installed
- Claude Code CLI installed (will authenticate on first run)

## Quick Start

### Step 1: Start MCP Server (Terminal 1 - Host)

Open a terminal on your host machine:

```bash
cd C:/Users/wilha/projects/pipe-dream/qms-cli
python -m qms_mcp --transport streamable-http --host 0.0.0.0 --port 8000 --project-root "C:/Users/wilha/projects/pipe-dream"
```

You should see:
```
INFO: Started server process [...]
INFO: Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

**Keep this terminal open.** The MCP server must be running for container QMS access.

### Step 2: Start Container (Terminal 2 - Host)

Open another terminal:

```bash
cd C:/Users/wilha/projects/pipe-dream/docker
docker-compose up -d
docker-compose exec claude-agent bash
```

You are now inside the container as root.

### Step 3: Configure MCP (Inside Container)

```bash
claude mcp add --transport http qms http://host.docker.internal:8000/mcp
```

Verify connection:
```bash
claude mcp list
```

Expected output:
```
qms: http://host.docker.internal:8000/mcp (HTTP) - ✓ Connected
```

### Step 4: Start Claude (Inside Container)

```bash
claude
```

On first run, you'll need to authenticate. Follow the prompts.

### Step 5: Verify MCP Tools Work

Inside Claude, try:
```
Check my QMS inbox
```

Or:
```
Use the qms_inbox tool to check for pending tasks
```

If you see a response like `{"result": "Inbox is empty"}`, the setup is complete.

## Detailed Configuration

### docker-compose.yml Mounts

| Mount | Mode | Purpose |
|-------|------|---------|
| `../:/pipe-dream` | ro | Production QMS (read-only) |
| `../.claude/users/claude/workspace:/pipe-dream/.claude/users/claude/workspace` | rw | QMS document checkout |
| `../.claude/sessions:/pipe-dream/.claude/sessions` | rw | Session persistence |
| `./.mcp.json:/pipe-dream/.mcp.json` | ro | Container MCP config |
| `~/.ssh:/.ssh` | ro | SSH keys for git |
| `~/.claude/.credentials.json:/.claude/.credentials.json` | ro | Claude credentials |

### MCP Server Options

| Option | Default | Description |
|--------|---------|-------------|
| `--transport` | stdio | Use `streamable-http` for containers |
| `--host` | 127.0.0.1 | Use `0.0.0.0` for container access |
| `--port` | 8000 | Port to bind |
| `--project-root` | auto-discover | Absolute path to pipe-dream |

### Available MCP Tools

Once connected, these QMS tools are available:

| Tool | Description |
|------|-------------|
| `qms_inbox` | Check pending tasks |
| `qms_workspace` | List checked-out documents |
| `qms_status` | Get document status |
| `qms_read` | Read document content |
| `qms_history` | View audit trail |
| `qms_comments` | View review comments |
| `qms_create` | Create new document |
| `qms_checkout` | Check out document |
| `qms_checkin` | Check in document |
| `qms_route` | Route for review/approval |
| `qms_review` | Submit review |
| `qms_approve` | Approve document |
| `qms_reject` | Reject document |
| `qms_release` | Release for execution |
| `qms_close` | Close document |

## Troubleshooting

### MCP Server Won't Start (Port in Use)

Find and kill the process:
```bash
# On Windows (Git Bash)
netstat -ano | grep 8000
taskkill //F //PID <pid>

# On Linux/Mac
lsof -i :8000
kill <pid>
```

### Container Can't Reach MCP Server

1. Verify MCP server is running on host
2. Ensure `--host 0.0.0.0` was used (not 127.0.0.1)
3. Test from container:
   ```bash
   curl http://host.docker.internal:8000/mcp
   ```

### MCP Shows Connected but Tools Don't Work

1. Inside Claude, run `/mcp`
2. Select the qms server
3. Choose "Reconnect"
4. Watch MCP server logs for connection activity

### Path Resolution Errors

If you see errors like `can't open file 'C:\\...\\qms.py'`:
- Use absolute path for `--project-root`
- Ensure path uses forward slashes or proper escaping

## Convenience Scripts

### docker/scripts/start-mcp-server.sh

Starts the MCP server with correct options:
```bash
./docker/scripts/start-mcp-server.sh
```

### docker/scripts/start-container.sh

Starts container and drops into bash:
```bash
./docker/scripts/start-container.sh
```

## Session Management

Sessions are persisted to the host at `.claude/sessions/`. When starting a new session inside the container:

1. Read CLAUDE.md for session protocol
2. Check `.claude/sessions/CURRENT_SESSION` for active session
3. Create new session folder if needed

## Security Model

| Access | Container | Host MCP |
|--------|-----------|----------|
| Read QMS files | Yes (ro mount) | Yes |
| Write QMS files | No | Yes |
| Read qms-cli | Yes (ro mount) | Yes |
| Modify qms-cli | No | No (requires CR) |
| Execute QMS commands | Via MCP only | Direct |

The container cannot:
- Directly modify any files under `/pipe-dream/` (read-only)
- Bypass MCP for QMS operations
- Access host filesystem outside mounts

The container can:
- Read all project files
- Write to workspace (document checkout)
- Write to sessions (session management)
- Execute QMS operations via MCP tools

## Reference

- **CR-043:** Original containerization infrastructure
- **CR-046:** Operational verification
- **CR-047:** Streamable-HTTP transport support
- **REQ-MCP-014:** Streamable-HTTP transport requirement

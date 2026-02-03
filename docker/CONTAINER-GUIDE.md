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

From the repository root, run:

```bash
./claude-session.sh
```

This single command:
1. Starts the MCP server in background (if not already running)
2. Starts the Docker container
3. Launches Claude Code with MCP auto-configured

You'll be in a Claude session with full QMS access. Verify by asking Claude to check your inbox.

### Stopping the Session

- Type `exit` or press Ctrl+D to leave the Claude session
- The MCP server continues running in background
- To stop the MCP server: `kill $(cat .mcp-server.pid)`

---

## Manual Setup (Reference)

If you prefer manual control or need to troubleshoot, here are the individual steps:

### Step 1: Start MCP Server (Terminal 1)

```bash
cd /path/to/pipe-dream/qms-cli
python -m qms_mcp --transport streamable-http --host 0.0.0.0 --port 8000 --project-root "/path/to/pipe-dream"
```

Keep this terminal open.

### Step 2: Start Container (Terminal 2)

```bash
cd /path/to/pipe-dream/docker
docker-compose up -d
docker-compose exec claude-agent claude
```

MCP is auto-configured via `working_dir: /pipe-dream` in docker-compose.yml, so Claude finds the `.mcp.json` automatically.

### Step 3: Verify MCP Works

Inside Claude, try:
```
Check my QMS inbox
```

If you see a response like `{"result": "Inbox is empty"}`, the setup is complete.

## Detailed Configuration

### docker-compose.yml Mounts

| Mount | Mode | Purpose |
|-------|------|---------|
| `../:/pipe-dream` | ro | Production QMS (read-only) |
| `../.claude/users/claude/workspace:/pipe-dream/.claude/users/claude/workspace` | rw | QMS document checkout |
| `../.claude/sessions:/pipe-dream/.claude/sessions` | rw | Session persistence |
| `./.mcp.json:/pipe-dream/.mcp.json` | ro | Container MCP config (HTTP transport with dual headers) |
| `./.claude-settings.json:/pipe-dream/.claude/settings.local.json` | ro | MCP server enablement |
| `~/.ssh:/.ssh` | ro | SSH keys for git |
| `claude-config:/claude-config` | rw | Named volume for auth persistence (see below) |

### Authentication Persistence

Auth credentials persist across container restarts via the `CLAUDE_CONFIG_DIR` environment variable pointing to a named Docker volume ([GitHub #1736](https://github.com/anthropics/claude-code/issues/1736)):

- **First run:** Browser OAuth required, credentials stored in volume
- **Subsequent runs:** No authentication required

To reset authentication: `docker volume rm docker_claude-config`

### MCP Auto-Connect

MCP auto-connects via dual headers that bypass Claude Code's OAuth discovery ([GitHub #7290](https://github.com/anthropics/claude-code/issues/7290)):

```json
{
  "headers": {
    "X-API-Key": "qms-internal",
    "Authorization": "Bearer internal-trusted"
  }
}
```

Both headers must be present to trigger the OAuth bypass.

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
- **CR-052:** Zero-friction container startup (auth persistence, MCP auto-connect)
- **REQ-MCP-014:** Streamable-HTTP transport requirement
- **GitHub #1736:** CLAUDE_CONFIG_DIR for container auth persistence
- **GitHub #7290:** Multiple headers bypass for MCP auto-connect

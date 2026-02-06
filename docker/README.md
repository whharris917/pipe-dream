# Claude Agent Container Infrastructure

This directory contains Docker infrastructure for running Claude agents in isolated containers with controlled access to the QMS and codebase.

## Overview

The container provides:
- **Isolation**: Claude runs in a container with restricted filesystem access
- **Read-only QMS access**: Production QMS files are mounted read-only
- **Controlled write access**: Only workspace and /projects/ are writable
- **MCP connectivity**: All QMS operations flow through the host MCP server via stdio proxy

## Quick Start

All container sessions use the unified `launch.sh` script in the repository root.

### Single Agent

```bash
./launch.sh              # Launches as 'claude' (default)
./launch.sh qa           # Launches as 'qa' agent
./launch.sh tu_ui        # Launches as 'tu_ui' agent
```

Valid agents: `claude`, `qa`, `tu_ui`, `tu_scene`, `tu_sketch`, `tu_sim`, `bu`

This single command:
1. Starts the MCP servers in background (if not running)
2. Builds the Docker image (if needed)
3. Starts the container with SETUP_ONLY=1 (entrypoint configures, then sleeps)
4. Attaches an interactive Claude session via `docker exec`
5. Mounts the appropriate CLAUDE.md (agent definition for non-claude agents)
6. Cleans up the container on exit

**First run per agent:** Browser OAuth required (credentials persist per-agent)
**Subsequent runs:** No authentication, MCP auto-connects

### Multi-Agent Session

Pass two or more agent names to launch them in separate terminal windows:

```bash
./launch.sh claude qa           # Launches claude + qa (default pair)
./launch.sh claude qa tu_ui     # Launches all three
```

This opens:
- One terminal window per agent
- An inbox watcher that monitors all agent inboxes
- Notifications when new tasks arrive (switch to appropriate terminal)

**Workflow example:**
1. In claude's terminal: route a document for review
2. Inbox watcher shows: `[QA] New task: Review CR-056`
3. Switch to qa's terminal and run `qms inbox` to see the task

### Manual Setup (if needed)

If you prefer manual control:

**Terminal 1 - MCP Server:**
```bash
cd qms-cli
python -m qms_mcp --transport streamable-http --host 0.0.0.0 --port 8000 --project-root ..
```

**Terminal 2 - Container:**
```bash
cd docker
docker-compose up -d
docker-compose exec claude-agent claude
```

## MCP Architecture: Stdio Proxy

Container MCP connections use a **stdio-to-HTTP proxy** rather than direct HTTP transport. This eliminates the ~10% intermittent connection failure that Claude Code's HTTP MCP client exhibited in Docker containers.

```
Claude Code  <--stdio-->  mcp_proxy.py  <--HTTP-->  Host MCP Server
(container)               (container)                (host)
```

**How it works:**
1. Claude Code spawns `mcp_proxy.py` as a local subprocess (stdio transport)
2. The proxy reads JSON-RPC messages from stdin
3. The proxy forwards each request as an HTTP POST to the host MCP server
4. The proxy parses the response (JSON or SSE format) and returns it via stdout
5. On HTTP failure, the proxy retries with exponential backoff before returning an error

**Configuration** (`.mcp.json`):
```json
{
  "mcpServers": {
    "qms": {
      "command": "python3",
      "args": ["/proxy/mcp_proxy.py", "http://host.docker.internal:8000/mcp",
               "--retries", "3", "--timeout", "10000",
               "--header", "X-API-Key=qms-internal",
               "--header", "Authorization=Bearer internal-trusted"]
    }
  }
}
```

**Why not direct HTTP?** Claude Code's HTTP MCP client intermittently fails to connect in Docker (~10% failure rate). The failure is client-side — sometimes no HTTP request is even attempted. Stdio connections are local subprocess spawns with no network dependency, achieving 100% reliability in testing (40/40 across scripted and manual tests).

## Filesystem Structure

```
/                                      # Container root (HOME=/)
├── .ssh/                              # Deploy keys (mounted from host)
├── claude-config/                     # [BIND MOUNT] Per-agent auth + config persistence
│   ├── .claude.json                   # User-scoped MCP config
│   └── .credentials.json              # OAuth credentials
│   # Mounted from: .claude/users/{agent}/container/
│
├── pipe-dream/                        # Production QMS mount (working_dir)
│   ├── CLAUDE.md                      # [READ-ONLY or OVERLAY]
│   │                                  # - claude: uses real CLAUDE.md
│   │                                  # - others: .claude/agents/{agent}.md mounted over
│   ├── .mcp.json                      # [OVERLAY] MCP config (stdio proxy to host servers)
│   ├── QMS/                           # [READ-ONLY]
│   ├── flow-state/                    # [READ-ONLY]
│   ├── qms-cli/                       # [READ-ONLY]
│   └── .claude/
│       ├── settings.local.json        # [OVERLAY] MCP enablement
│       ├── sessions/                  # [READ-WRITE] Session persistence
│       └── users/{agent}/workspace/   # [READ-WRITE] QMS document checkout (per-agent)
│
└── projects/                          # [READ-WRITE] Development workspace
    └── {repo}/                        # Cloned repositories
```

### Per-Agent Configuration (Host-side)

```
.claude/users/
├── claude/
│   ├── container/    # Claude Code auth/config (bind mounted)
│   ├── workspace/    # QMS workspace
│   └── inbox/        # QMS inbox
├── qa/
│   ├── container/    # Separate auth for qa agent
│   ├── workspace/
│   └── inbox/
└── ... (other agents)
```

Each agent has isolated authentication and conversation state via their own `container/` directory.

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

### Git Operations from Containers

Since `/pipe-dream/` is mounted read-only (including `.git/`), git operations cannot execute directly in the container. The Git MCP server provides a controlled proxy for git commands.

**Starting the Git MCP Server (on host):**

```bash
cd docker/scripts
./start-git-mcp.sh            # Foreground
./start-git-mcp.sh --background  # Background
```

**Using git from container:**

```python
# Single commands
git_exec("status")
git_exec("log --oneline -10")

# Chained commands
git_exec("git add .claude/sessions/ && git commit -m 'Session notes' && git push")
```

**Protected Operations:**

The Git MCP server blocks:
- References to submodules: `flow-state`, `qms-cli`
- Destructive commands: `push --force`, `reset --hard`, `clean -f`, `checkout .`, `restore .`

All other git operations pass through normally.

## GitHub Authentication (Required for git push)

Git operations in the container are authenticated via GitHub CLI using a Personal Access Token (PAT).

### Setup

1. **Create a GitHub PAT** at https://github.com/settings/tokens
   - Click "Generate new token" → "Generate new token (classic)"
   - Required scope: `repo` (full control of private repositories)
   - Recommended expiration: 90 days (rotate periodically)

2. **Create `.env` file** in the `docker/` directory:
   ```bash
   cp .env.example .env
   # Edit .env and add your token
   ```

   Or create manually:
   ```
   GH_TOKEN=ghp_your_token_here
   ```

3. **Rebuild and restart** the container:
   ```bash
   docker-compose build
   docker-compose up -d
   ```

### Security Considerations

- **Never commit `.env`** - it's gitignored for a reason
- **Use scoped tokens** - only grant `repo` permission, not full account access
- **Rotate tokens** - set expiration and regenerate periodically
- **Revoke if compromised** - if the container is ever compromised, immediately revoke the token at github.com/settings/tokens

This approach follows [Anthropic's security guidance](https://www.anthropic.com/engineering/claude-code-sandboxing) for keeping credentials minimal, external, and easily revocable.

### Verification

After setup, verify authentication in the container:
```bash
docker-compose exec claude-agent gh auth status
```

## Prerequisites

- Docker Desktop (Mac/Windows) or Docker Engine (Linux)
- Claude Code credentials (`~/.claude/.credentials.json` on host)
- GitHub Personal Access Token (see GitHub Authentication above)

## Troubleshooting

### MCP servers show "failed" in Claude Code

1. Verify the host MCP servers are running:
   ```bash
   curl -s -X POST http://localhost:8000/mcp \
     -H "Content-Type: application/json" \
     -H "Accept: application/json, text/event-stream" \
     -d '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}},"id":1}'
   ```

2. Test the proxy from inside the container:
   ```bash
   echo '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}},"id":1}' \
     | python3 /proxy/mcp_proxy.py http://host.docker.internal:8000/mcp --retries 1 --timeout 5000 \
       --header "X-API-Key=qms-internal" --header "Authorization=Bearer internal-trusted"
   ```

3. On Linux, ensure `host.docker.internal` is configured:
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

Auth is stored per-agent in `.claude/users/{agent}/container/`. To reset for a specific agent:
```bash
rm -rf .claude/users/qa/container/*  # Reset qa agent
```

Then run `./launch.sh qa` again to re-authenticate.

### Inbox watcher not detecting new files (Windows)

The watchdog library uses different backends on different platforms. On Windows, it uses ReadDirectoryChangesW which should work automatically. If notifications aren't appearing:

1. Verify inbox-watcher.py is running: `cat .inbox-watcher.pid`
2. Check logs: `cat .inbox-watcher.log`
3. Ensure the inbox directory exists: `ls .claude/users/qa/inbox/`

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
- CR-052: Zero-friction container startup (auth persistence, MCP auto-connect)
- CR-053: Container git authentication via GitHub CLI
- CR-054: Git MCP Server for Container Operations
- CR-056: Multi-Agent Container Session Infrastructure
- CR-057: MCP Stdio Proxy for Reliable Container MCP Connections
- [GitHub #1736](https://github.com/anthropics/claude-code/issues/1736): CLAUDE_CONFIG_DIR for auth persistence
- [GitHub #7290](https://github.com/anthropics/claude-code/issues/7290): Multiple headers bypass for MCP auto-connect
- [Anthropic - Claude Code Sandboxing](https://www.anthropic.com/engineering/claude-code-sandboxing): Security best practices

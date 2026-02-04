# Claude Agent Container Infrastructure

This directory contains Docker infrastructure for running Claude agents in isolated containers with controlled access to the QMS and codebase.

## Overview

The container provides:
- **Isolation**: Claude runs in a container with restricted filesystem access
- **Read-only QMS access**: Production QMS files are mounted read-only
- **Controlled write access**: Only workspace and /projects/ are writable
- **MCP connectivity**: All QMS operations flow through the host MCP server

## Quick Start

From the repository root, run:

```bash
./claude-session.sh
```

This single command:
1. Starts the MCP server in background (if not running)
2. Starts the Docker container
3. Launches Claude Code with MCP auto-configured

**First run:** Browser OAuth required (credentials persist for future runs)
**Subsequent runs:** No authentication, MCP auto-connects

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

## Filesystem Structure

```
/                                      # Container root (HOME=/)
├── .ssh/                              # Deploy keys (mounted from host)
├── claude-config/                     # [NAMED VOLUME] Auth + MCP config persistence
│   ├── .claude.json                   # User-scoped MCP config
│   └── .credentials.json              # OAuth credentials
│
├── pipe-dream/                        # Production QMS mount (working_dir)
│   ├── CLAUDE.md                      # [READ-ONLY]
│   ├── .mcp.json                      # [OVERLAY] HTTP MCP config with dual headers
│   ├── QMS/                           # [READ-ONLY]
│   ├── flow-state/                    # [READ-ONLY]
│   ├── qms-cli/                       # [READ-ONLY]
│   └── .claude/
│       ├── settings.local.json        # [OVERLAY] MCP enablement
│       ├── sessions/                  # [READ-WRITE] Session persistence
│       └── users/claude/workspace/    # [READ-WRITE] QMS document checkout
│
└── projects/                          # [READ-WRITE] Development workspace
    └── {repo}/                        # Cloned repositories
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

Auth is stored in the `claude-config` named volume. To reset:
```bash
docker volume rm docker_claude-config
```

Then run `./claude-session.sh` again to re-authenticate.

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
- [GitHub #1736](https://github.com/anthropics/claude-code/issues/1736): CLAUDE_CONFIG_DIR for auth persistence
- [GitHub #7290](https://github.com/anthropics/claude-code/issues/7290): Multiple headers bypass for MCP auto-connect
- [Anthropic - Claude Code Sandboxing](https://www.anthropic.com/engineering/claude-code-sandboxing): Security best practices

# Container Architecture Vision

## Overview

This document formalizes the architecture for running Claude agents in Docker containers with controlled access to the QMS and codebase.

## Design Principles

1. **QMS Integrity**: All QMS write operations flow through the MCP server on the host
2. **Isolation**: Container has minimal write access to production files
3. **Workspace as Airlock**: QMS document checkout/checkin is the controlled exchange mechanism
4. **Simplicity**: Flat container structure with no unnecessary hierarchy

## Container Filesystem Structure

```
/                                      # Container root = Claude's home (HOME=/)
├── .mcp.json                          # MCP server connection config (baked in)
├── .gitconfig                         # Git configuration
├── .ssh/
│   └── id_ed25519                     # Deploy key for GitHub
├── .claude/                           # Claude Code configuration
│   └── settings.json
│
├── projects/                          # [READ-WRITE] Development workspace
│   ├── flow-state/                    # Cloned repos for code work
│   │   └── .git/
│   └── qms-cli/                       # If CLI development needed
│       └── .git/
│
└── pipe-dream/                        # Production QMS mount point
    ├── CLAUDE.md                      # [READ-ONLY]
    ├── QMS/                           # [READ-ONLY]
    │   ├── SOP/
    │   ├── CR/
    │   └── ...
    ├── flow-state/                    # [READ-ONLY] Reference copy
    ├── qms-cli/                       # [READ-ONLY] Reference copy
    └── .claude/
        └── users/
            └── claude/
                ├── inbox/             # [READ-ONLY] MCP writes tasks here
                └── workspace/         # [READ-WRITE] QMS docs ONLY
```

## Access Control Matrix

| Path | Access | Purpose |
|------|--------|---------|
| `/` | R/W | Agent's home directory |
| `/.mcp.json` | Read (baked in) | MCP connection configuration |
| `/projects/` | R/W | Clone repos, develop, build, test |
| `/pipe-dream/` | Read-only | Production QMS reference |
| `/pipe-dream/.claude/users/claude/inbox/` | Read-only | Task notifications |
| `/pipe-dream/.claude/users/claude/workspace/` | R/W | QMS document checkout |

## MCP Connection

### Container Configuration (`/.mcp.json` - baked into image)

```json
{
  "mcpServers": {
    "qms": {
      "type": "sse",
      "url": "http://host.docker.internal:8000/sse"
    }
  }
}
```

### Host MCP Server Startup

```bash
python -m qms_mcp --transport sse --port 8000 --project-root /path/to/pipe-dream
```

## Workflows

### QMS Document Editing

1. Claude calls `qms_checkout("CR-043")` via MCP
2. MCP server (on host) copies document to `/pipe-dream/.claude/users/claude/workspace/`
3. Claude edits the document in workspace (the one place with write access)
4. Claude calls `qms_checkin("CR-043")` via MCP
5. MCP server copies from workspace back to QMS and updates metadata

### Code Development

1. Clone repository into `/projects/`:
   ```bash
   cd /projects
   git clone https://github.com/whharris917/flow-state.git
   ```
2. Create feature branch: `git checkout -b cr-043-feature`
3. Develop, test, commit
4. Push to origin (not main - branch protection enforced)
5. Create PR for review and CI verification

### Reading Production State

- Read QMS documents directly from `/pipe-dream/QMS/` (read-only)
- Read current codebase from `/pipe-dream/flow-state/` (read-only reference)
- Check inbox at `/pipe-dream/.claude/users/claude/inbox/`

## Docker Configuration

### Volume Mounts

```bash
docker run \
  -v /path/to/pipe-dream:/pipe-dream:ro \
  -v /path/to/pipe-dream/.claude/users/claude/workspace:/pipe-dream/.claude/users/claude/workspace:rw \
  claude-agent
```

### Network

- Container must be able to reach `host.docker.internal:8000`
- On Linux: add `--add-host=host.docker.internal:host-gateway`

### Environment

```dockerfile
ENV HOME=/
```

## Security Considerations

### Implemented

- QMS writes flow through authenticated MCP server
- Production files are read-only
- Workspace is the only write point for QMS interaction

### Deferred (Future CR)

- Preventing direct pushes to main branch (GitHub branch protection + fine-grained PAT)
- Container identity management (one container = one agent identity)
- MCP server authentication (currently localhost-only binding)

## Related Documents

- **CR-042**: Add Remote Transport Support to QMS MCP Server (completed)
- **CLAUDE.md**: Updated with container MCP configuration section
- **SDLC-QMS-RS v5.0**: REQ-MCP-011 through REQ-MCP-013 (remote transport requirements)

# Session 2026-02-03-003: Multi-Agent Container Architecture

## Objective

Design a framework for running multiple Claude agents in separate containers, coordinating through the QMS.

## Key Discoveries

### Container Filesystem Analysis
- Claude Code config stored in named Docker volume (`claude-config`)
- Host's `settings.local.json` (with permissions) is masked by container overlay
- Container overlay (`docker/.claude-settings.json`) only has MCP enablement, missing deny rules for QMS protection

### Settings Permissions Gap
Host has governance rules that don't apply in container:
```json
"deny": [
  "Edit(QMS/**)",
  "Write(QMS/**)"
]
```
Action needed: Update `docker/.claude-settings.json` to include host permissions.

## Architecture Decisions

### 1. Bind Mounts over Named Volumes
Replace Docker named volumes with bind mounts for transparency:
```
.claude/users/{agent}/
├── container/    # Claude Code config (was named volume)
├── workspace/    # QMS workspace
└── inbox/        # QMS inbox
```

### 2. Agent Context Loading
Fundamental asymmetry between orchestrator and agents:
- `claude` → uses `CLAUDE.md`
- All others → use `.claude/agents/{agent}.md`

Solution: Mount agent definition file as `CLAUDE.md` for non-claude containers.

### 3. Peer Agent Model
Shift from hierarchical to flat architecture:

| Old Model | New Model |
|-----------|-----------|
| claude orchestrates sub-agents | All agents are peers |
| Task tool spawns agents | User launches containers |
| Orchestrator passes context | QMS coordinates |
| "sub-agents" | "agents" |

### 4. Unified GUI Vision
Custom GUI sits on top of all containers:
- Agent switching and conversation view
- QMS dashboard with inbox overview
- Document workflow tracking
- Container lifecycle management

## Files Created

- `.claude/sessions/Session-2026-02-03-003/multi-agent-container-design.md` - Full architecture design

## Next Steps

1. Create CR to implement bind mount architecture
2. Update `docker/.claude-settings.json` with host permissions
3. Create container directories under `.claude/users/*/container/`
4. Update launch script for agent-specific context loading
5. Design GUI communication protocol with containers

## Open Questions

1. How does GUI communicate with containers?
2. Always-running vs on-demand containers?
3. Do agent definition files need shared context duplicated?
4. Git operations from containers - need MCP command to proxy to host

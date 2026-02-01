# Session 2026-01-31-001 Summary

## Claude-in-Container Architecture

Developed and validated an isolation architecture where Claude runs inside a Docker container, separate from the host filesystem:

```
HOST MACHINE (user's environment)
├── QMS/, flow-state/, qms-cli/    ← normal access, normal git
├── MCP Server (localhost:9000)    ← exposes QMS operations
│
└── DOCKER CONTAINER (Claude's sandbox)
    ├── /workspace/                ← only visible directory
    └── MCP client → host:9000     ← controlled access to QMS
```

**Key insight:** Instead of hiding the QMS from Claude, isolate Claude from the QMS. Claude becomes the guest; your data stays in your normal environment.

**Benefits over QMS-in-container:**
- Normal filesystem access for user (git, backups, IDE)
- Claude can only access QMS through the API you define
- Container filesystem is ephemeral (clean slate each session)
- Supports multiple parallel agents in separate containers

---

## Proof of Concept: Claude Code in Docker

Created and tested a minimal Dockerfile:

```dockerfile
FROM node:20-slim
RUN apt-get update && apt-get install -y git curl
RUN npm install -g @anthropic-ai/claude-code
WORKDIR /workspace
CMD ["claude"]
```

**Validated:**
- Container runs successfully
- Claude sees only `/workspace/` (empty)
- No visibility into host filesystem
- Container stops when Claude exits (expected behavior)

Location: `.claude/docker/claude-sandbox/Dockerfile`

---

## Vision: QMS Command Center

Discussed a web-based GUI as the central interface for QMS-enabled projects:

- Spawn/monitor agent containers
- Browse QMS documents and workflow state
- Stream agent terminal output in real-time (WebSocket)
- Visualize active CRs, assignments, branch state

**Decision:** Web-based (not desktop) because:
- Backend server needed anyway (Docker orchestration, WebSockets)
- Faster iteration, cross-platform
- Standard pattern for container dashboards
- Future flexibility (remote access, multi-user)

---

## CR-041: Implement QMS MCP Server

Drafted and checked in CR-041, a comprehensive requalification effort to add MCP server functionality to qms-cli.

**Scope:**
- Expose all QMS CLI operations as native MCP tools
- Enables cleaner agent-QMS interaction (tool calls vs bash commands)
- Full requalification: RS updates, qualification tests, RTM updates

**Key design decisions:**
- Framed as ergonomic improvement (not tied to containerization vision in official docs)
- CLI syntax remains canonical in SOPs; MCP is agent convenience layer
- Development in isolated test environment (`.test-env/test-project/`)
- Version transition: CLI-2.0 → CLI-3.0

**Files affected:**
- `qms-cli/mcp/` — New MCP server package
- `SDLC-QMS-RS` — Add REQ-MCP-* requirements
- `SDLC-QMS-RTM` — Add verification evidence
- `CLAUDE.md` and `.claude/agents/*.md` — Update with MCP syntax
- `.claude/settings.local.json` — MCP server configuration

**23 execution items** following CR-036 best practices:
1. Test environment setup
2. Requirements (RS) before implementation
3. Implementation phases
4. Qualification with CI verification
5. RTM after qualification
6. PR merge after RS/RTM approval
7. Documentation updates

---

## Protective Measures

**qms-cli write protection added:**
```json
"deny": [
  "Edit(qms-cli/**)",
  "Write(qms-cli/**)"
]
```

Development must occur in `.test-env/` isolation, not production submodule.

---

## Next Steps (Next Session)

1. Route CR-041 for pre-review
2. Begin execution after pre-approval
3. Web-based Command Center GUI (future)
4. Multi-agent container orchestration (future)

---

## Artifacts

| Item | Location | Status |
|------|----------|--------|
| Claude sandbox Dockerfile | `.claude/docker/claude-sandbox/Dockerfile` | Created |
| CR-041: QMS MCP Server | `QMS/CR/CR-041/CR-041-draft.md` | DRAFT (v0.1) |
| Write protection | `.claude/settings.local.json` | Active |

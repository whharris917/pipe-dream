# Session 2026-02-04-001: Git MCP Server Implementation & Integration

## Objective

Implement a Git MCP server for container git operations (CR-054), then integrate it into the unified session startup script (CR-055).

## Background

Containers mount pipe-dream as read-only (including `.git/`), preventing all git operations. A host-side MCP server was needed to proxy git commands while enforcing security constraints.

## CR-054: Git MCP Server for Container Operations

**Status:** CLOSED

### Implementation

Created `git_mcp/` package with:
- `server.py` — FastMCP server with `git_exec` tool
- `__main__.py` — Module entry point
- `requirements.txt` — Dependencies (mcp>=1.0.0)

### Protection Mechanisms

| Type | Patterns Blocked |
|------|------------------|
| Submodules | `flow-state`, `qms-cli` |
| Destructive | `push --force`, `reset --hard`, `clean -f`, `checkout .`, `restore .` |

### Container Integration

Updated:
- `docker/scripts/start-git-mcp.sh` — Startup script with `--background` support
- `docker/scripts/start-mcp-server.sh` — Fixed to cd into `qms-cli/`, added `--background` support
- `docker/.claude-settings.json` — Added `"git"` to `enabledMcpjsonServers`
- `docker/.mcp.json` — Added git server endpoint (port 8001)
- `docker/entrypoint.sh` — Added Git MCP server registration
- `docker/README.md` — Documented Git MCP usage
- `CLAUDE.md` — Added Git MCP Server section

### Issues Discovered & Fixed

1. **QMS MCP script path** — Script ran from project root but module is in `qms-cli/`
2. **Background mode** — Neither script had `--background` flag support initially
3. **Container discovery** — Git server not in `enabledMcpjsonServers` array
4. **Entrypoint registration** — Only QMS server was registered via `claude mcp add`
5. **Windows shell** — `bash -c` tried to use WSL; changed to `shell=True`

### Test Results (All Passed)

| Test | Command | Result |
|------|---------|--------|
| 1 | `git_exec("status")` | Returned branch info and modified files |
| 2 | `git_exec("log --oneline -3")` | Returned commits f4b6102, c9086c7, ca83bda |
| 3 | `git_exec("add flow-state/")` | Blocked: submodule protection |
| 4 | `git_exec("push --force")` | Blocked: destructive operation |

## Process Insights

### Deferral Introspection

During execution, EI-7 (container testing) was initially marked as "Deferred" — an invalid status per SOP-002. QA correctly flagged this.

An introspection document was written analyzing why this happened:
- Effort avoidance over direct collaboration
- Momentum preservation over completeness
- Assumption that user would want to verify manually

**Key learning:** When blocked, immediately convert the block into a specific request rather than inventing statuses.

See: `introspection-deferral-decision.md`

## Files Created/Modified

**New files:**
- `git_mcp/__init__.py`
- `git_mcp/__main__.py`
- `git_mcp/server.py`
- `git_mcp/requirements.txt`
- `docker/scripts/start-git-mcp.sh`

**Modified files:**
- `docker/scripts/start-mcp-server.sh`
- `docker/.claude-settings.json`
- `docker/.mcp.json`
- `docker/entrypoint.sh`
- `docker/README.md`
- `CLAUDE.md`
- `claude-session.sh` (CR-055)
- `.claude/IDEA_TRACKER.md`

## CR-055: Add Git MCP Server to claude-session.sh

**Status:** CLOSED

### Implementation

Updated `claude-session.sh` to provide zero-friction container sessions with both MCP servers:

| Step | Description |
|------|-------------|
| 1/5 | Check/start QMS MCP server (port 8000) |
| 2/5 | Check/start Git MCP server (port 8001) |
| 3/5 | Start container |
| 4/5 | Verify MCP connectivity (both servers) |
| 5/5 | Launch Claude Code |

### Changes

- Refactored Python executable detection (shared by both servers)
- Added Git MCP server startup with PID file tracking
- Added dual connectivity verification from container
- Updated post-session message to show both PID files

### UAT Results

User Acceptance Testing performed by Lead (3 runs):
- **Run 1:** All steps passed; Claude exited due to auto-update (not script issue)
- **Run 2:** Full pass — all functionality verified
- **Run 3:** Full pass — confirmation run

## Ideas Captured

- **Formalize UATs as Stage Gates** — The UAT pattern used in CR-055 (user verifies before post-review) could be formalized in the CR workflow. Added to IDEA_TRACKER.md.

## Next Steps

Both MCP servers are now fully integrated. Future enhancements could include:
- User permission checking for git operations
- More granular path restrictions beyond submodules
- Audit logging of git operations
- Formalizing UAT as a stage gate in SOP-002

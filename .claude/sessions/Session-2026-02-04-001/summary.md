# Session 2026-02-04-001: Git MCP Server Implementation

## Objective

Implement a Git MCP server to enable agents in Docker containers to execute git commands on the host repository, with protection against submodule modifications and destructive operations.

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

## Next Steps

The Git MCP server is operational. Future enhancements could include:
- User permission checking (currently any container user can execute)
- More granular path restrictions beyond submodules
- Audit logging of git operations

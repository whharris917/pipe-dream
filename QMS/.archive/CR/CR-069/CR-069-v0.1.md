---
title: Agent Hub Consolidation — Unify orchestration tools under agent-hub/
revision_summary: Initial draft
---

# CR-069: Agent Hub Consolidation — Unify orchestration tools under agent-hub/

## 1. Purpose

Consolidate all agent orchestration tools — currently scattered across the top level of the pipe-dream repository — into the `agent-hub/` package as a unified, professional package. Absorb the functionality of `launch.sh` and `pd-status` shell scripts into Python CLI subcommands. Eliminate PID files in favor of port-based service detection. Centralize runtime logs.

---

## 2. Scope

### 2.1 Context

User-requested enhancement. The pipe-dream repo has grown organically and orchestration tools are scattered across the top level: `git_mcp/`, `agent-gui/`, `docker/`, `launch.sh`, `pd-status`, plus runtime log/PID files. The `agent-hub/` package already exists as the Hub server but does not yet own all of its sibling infrastructure.

- **Parent Document:** None

### 2.2 Changes Summary

1. Move `git_mcp/`, `agent-gui/`, and `docker/` under `agent-hub/`
2. Absorb `launch.sh` and `pd-status` as Python CLI subcommands (`agent-hub launch`, `agent-hub services`, `agent-hub stop-all`)
3. Create `agent_hub/services.py` module for cross-platform service lifecycle management
4. Eliminate PID files; use port-based detection exclusively
5. Centralize runtime logs in `agent-hub/logs/`
6. Delete obsolete `.claude/docker/` directory
7. Update all path references in configs, scripts, and documentation

### 2.3 Files Affected

**Moved (git mv):**
- `git_mcp/` → `agent-hub/mcp-servers/git_mcp/`
- `agent-gui/` → `agent-hub/gui/`
- `docker/` → `agent-hub/docker/`

**Created:**
- `agent-hub/agent_hub/services.py` — Service lifecycle module
- `agent-hub/logs/.gitkeep` — Log directory

**Modified:**
- `agent-hub/agent_hub/cli.py` — Add `launch`, `services`, `stop-all` subcommands
- `agent-hub/agent_hub/config.py` — Add `docker_dir`, `log_dir`, `mcp_servers_dir` properties and MCP port constants
- `agent-hub/agent_hub/container.py` — Update hardcoded `docker/` paths to use config properties
- `agent-hub/docker/docker-compose.yml` — Update volume mount paths (`../` → `../../`)
- `agent-hub/docker/scripts/start-git-mcp.sh` — Remove PID logic, fix PROJECT_ROOT, update log/module paths
- `agent-hub/docker/scripts/start-mcp-server.sh` — Remove PID logic, fix PROJECT_ROOT, update log path
- `agent-hub/pyproject.toml` — Add `mcp>=1.0.0` dependency
- `agent-hub/.gitignore` — Add `logs/`, `gui/node_modules/`, `gui/dist/`
- `agent-hub/README.md` — Comprehensive rewrite
- `agent-hub/docker/README.md` — Update path references
- `agent-hub/docker/CONTAINER-GUIDE.md` — Update path references
- `.gitignore` — Remove root-level log file patterns
- `requirements.txt` — Remove `watchdog` (now in agent-hub's pyproject.toml)
- `CLAUDE.md` — Update Container Infrastructure section, CLI references, paths

**Deleted:**
- `.claude/docker/` — Obsolete single-file directory
- `.git-mcp-server.pid`, `.qms-mcp-server.pid` — PID files (eliminated)
- `.agent-hub.log`, `.agent-hub-test.log`, `.git-mcp-server.log`, `.qms-mcp-server.log` — Root-level logs (moved to `agent-hub/logs/`)
- `launch.sh` — Absorbed into `agent-hub launch` CLI
- `pd-status` — Absorbed into `agent-hub services` / `agent-hub stop-all` CLI

---

## 3. Current State

Agent orchestration tools are scattered across the pipe-dream repo root:

- `git_mcp/` — Git MCP server package (4 files)
- `agent-gui/` — Tauri + React desktop GUI (38 files)
- `docker/` — Container infrastructure (Dockerfile, compose, entrypoint, scripts, configs, docs)
- `launch.sh` — 345-line bash script for container orchestration
- `pd-status` — 263-line bash script for process status/teardown
- Six dotfiles at repo root: `.agent-hub.log`, `.agent-hub-test.log`, `.git-mcp-server.log`, `.qms-mcp-server.log`, `.git-mcp-server.pid`, `.qms-mcp-server.pid`
- `.claude/docker/claude-sandbox/Dockerfile` — Obsolete single-file artifact

The `docker/scripts/start-git-mcp.sh` and `start-mcp-server.sh` write and check PID files for server management. The `launch.sh` script already uses port-based health probing instead, making the PID files redundant.

---

## 4. Proposed State

All agent orchestration tools live under `agent-hub/` as a unified package:

```
agent-hub/
├── agent_hub/          # Python package (Hub server + CLI)
│   ├── services.py     # NEW: cross-platform service lifecycle
│   └── cli.py          # 9 subcommands (6 existing + 3 new)
├── docker/             # Container infrastructure
├── gui/                # Tauri + React desktop GUI
├── mcp-servers/
│   └── git_mcp/        # Git MCP server
├── logs/               # Runtime logs (gitignored)
└── pyproject.toml
```

The CLI provides three new subcommands:
- `agent-hub launch [agents...]` — Full orchestration replacing `launch.sh`
- `agent-hub services` — Process status replacing `pd-status`
- `agent-hub stop-all` — Service teardown replacing `pd-status --stop-all`

No PID files exist. All service detection uses port-based health probing. Runtime logs are centralized in `agent-hub/logs/`.

---

## 5. Change Description

### 5.1 File Moves

Use `git mv` to preserve history:
- `git_mcp/` → `agent-hub/mcp-servers/git_mcp/` (kept as its own package, not merged into agent_hub)
- `agent-gui/` → `agent-hub/gui/`
- `docker/` → `agent-hub/docker/`

### 5.2 New Module: services.py

Translates battle-tested bash logic from `launch.sh` and `pd-status` into Python. Key functions:

| Function | Source | Purpose |
|----------|--------|---------|
| `find_python(project_root)` | launch.sh:47-55 | Locate venv Python interpreter |
| `find_pid_on_port(port)` | pd-status:42-54 | Cross-platform PID discovery (PowerShell/lsof/ss) |
| `is_port_alive(port, path)` | pd-status:57-63 | HTTP health probe via httpx |
| `ensure_mcp_servers(config)` | launch.sh:57-97 | Start QMS + Git MCP servers if not running |
| `ensure_hub(config)` | launch.sh:242-265 | Start Hub if not running |
| `ensure_docker_image(config)` | launch.sh:99-109 | Build Docker image if missing |
| `stop_service_on_port(port)` | pd-status:136-152 | Kill process by port (taskkill on Windows, kill on Unix) |
| `get_services_status(config)` | pd-status:169-237 | Structured status of all services |
| `stop_all_services(config)` | pd-status:76-165 | Stop all services with confirmation |
| `launch_in_terminal(agent, config)` | launch.sh:221-240 | Spawn agent in new OS terminal window |

### 5.3 New CLI Subcommands

**`agent-hub launch [agents...]`** replaces `launch.sh`:
1. Validate agent names against roster
2. Ensure MCP servers, Docker image, and Hub are running
3. Single agent: start via Hub API, `docker exec -it` into tmux (interactive)
4. Multiple agents: each spawned in a new terminal window with 3-second stagger

**`agent-hub services`** replaces `pd-status`:
- Display table of services (QMS MCP :8000, Git MCP :8001, Hub :9000) with state and PID
- List Docker containers matching `agent-*` with state

**`agent-hub stop-all`** replaces `pd-status --stop-all`:
- Enumerate running services and containers
- Interactive confirmation (skippable with `--yes`)
- Kill services by port, remove Docker containers

### 5.4 Path Fixes After Moves

- `container.py` lines 138, 141, 182: change `self.config.project_root / "docker"` to `self.config.docker_dir`
- `docker-compose.yml`: volume mounts change `../` to `../../`
- `start-git-mcp.sh` and `start-mcp-server.sh`: PROJECT_ROOT goes from 2 to 3 levels up, PID logic removed, log paths redirect to `agent-hub/logs/`

### 5.5 PID File Elimination

Both `docker/scripts/start-git-mcp.sh` and `start-mcp-server.sh` currently write `.pid` files and check them on startup. This logic is removed. Port-based detection (already used by `launch.sh` and `pd-status`) becomes the sole mechanism.

### 5.6 Documentation Updates

- `CLAUDE.md`: Update Container Infrastructure section, all CLI references, all path references
- `agent-hub/docker/README.md` and `CONTAINER-GUIDE.md`: Update path and command references
- `agent-hub/README.md`: Comprehensive rewrite as the single reference for the package

---

## 6. Justification

- **Organization:** Six top-level items (`git_mcp/`, `agent-gui/`, `docker/`, `launch.sh`, `pd-status`, log/PID files) clutter the repo root. They all serve agent orchestration and belong together.
- **Unified interface:** Two bash scripts and a Python CLI providing overlapping functionality creates confusion. A single `agent-hub` CLI with clear subcommands is more professional and maintainable.
- **Cross-platform:** Python CLI subcommands work consistently across platforms; bash scripts depend on Git Bash on Windows.
- **Testability:** Python functions can be unit-tested; bash functions cannot.
- **PID files are unreliable:** PIDs can be stale after crashes. Port-based detection is more robust and is already the approach used by `launch.sh`.
- **Impact of not making this change:** The repo continues to accumulate top-level orchestration artifacts as the agent infrastructure grows, making onboarding and maintenance progressively harder.

---

## 7. Impact Assessment

### 7.1 Files Affected

| File | Change Type | Description |
|------|-------------|-------------|
| `agent-hub/agent_hub/services.py` | Create | Service lifecycle module |
| `agent-hub/logs/.gitkeep` | Create | Log directory placeholder |
| `agent-hub/agent_hub/cli.py` | Modify | Add 3 CLI subcommands |
| `agent-hub/agent_hub/config.py` | Modify | Add path properties, port constants |
| `agent-hub/agent_hub/container.py` | Modify | Fix docker path references |
| `agent-hub/docker/docker-compose.yml` | Modify | Volume mount paths |
| `agent-hub/docker/scripts/start-git-mcp.sh` | Modify | Remove PID logic, fix paths |
| `agent-hub/docker/scripts/start-mcp-server.sh` | Modify | Remove PID logic, fix paths |
| `agent-hub/pyproject.toml` | Modify | Add mcp dependency |
| `agent-hub/.gitignore` | Modify | Add logs/, gui/ patterns |
| `agent-hub/README.md` | Modify | Comprehensive rewrite |
| `agent-hub/docker/README.md` | Modify | Path references |
| `agent-hub/docker/CONTAINER-GUIDE.md` | Modify | Path references |
| `.gitignore` | Modify | Remove root-level log patterns |
| `requirements.txt` | Modify | Remove watchdog |
| `CLAUDE.md` | Modify | Path and CLI references |
| `launch.sh` | Delete | Absorbed into CLI |
| `pd-status` | Delete | Absorbed into CLI |
| `.claude/docker/` | Delete | Obsolete |
| `git_mcp/` | Move | → `agent-hub/mcp-servers/git_mcp/` |
| `agent-gui/` | Move | → `agent-hub/gui/` |
| `docker/` | Move | → `agent-hub/docker/` |

### 7.2 Documents Affected

| Document | Change Type | Description |
|----------|-------------|-------------|
| CLAUDE.md | Modify | Update Container Infrastructure section, CLI references, paths |

### 7.3 Other Impacts

- Users who have muscle memory for `./launch.sh` or `./pd-status` must switch to `agent-hub launch` and `agent-hub services`/`agent-hub stop-all`
- Docker image rebuild required after docker-compose.yml path changes (`docker-compose build --no-cache`)
- `pip install -e agent-hub/` may need to be re-run after pyproject.toml changes

---

## 8. Testing Summary

- Validate docker-compose.yml after move: `docker-compose -f agent-hub/docker/docker-compose.yml config`
- Verify CLI entry point: `agent-hub --help` shows all 9 subcommands
- `agent-hub services` — displays service status (equivalent to old `pd-status`)
- `agent-hub launch claude` — full integration test: starts MCP servers, Docker image, Hub, container
- `agent-hub stop-all` — clean teardown of all services
- `python -m git_mcp --help` from `agent-hub/mcp-servers/` — standalone server still works
- Shell scripts: `agent-hub/docker/scripts/start-git-mcp.sh` and `start-mcp-server.sh` run without PID errors

---

## 9. Implementation Plan

### 9.1 Phase 1: File Moves and Cleanup

1. Create target directories (`agent-hub/mcp-servers/`, `agent-hub/logs/`)
2. `git mv git_mcp agent-hub/mcp-servers/git_mcp`
3. `git mv agent-gui agent-hub/gui`
4. `git mv docker agent-hub/docker`
5. Create `agent-hub/logs/.gitkeep`
6. Delete `.claude/docker/`, PID files, root-level log files

### 9.2 Phase 2: Path Fixes

1. Update `container.py` to use `self.config.docker_dir` instead of hardcoded `"docker"` path
2. Add `docker_dir`, `log_dir`, `mcp_servers_dir` properties and MCP port constants to `config.py`
3. Update `docker-compose.yml` volume mounts from `../` to `../../`
4. Update `start-git-mcp.sh`: remove PID logic, fix PROJECT_ROOT (3 levels up), update log and module paths
5. Update `start-mcp-server.sh`: remove PID logic, fix PROJECT_ROOT (3 levels up), update log path

### 9.3 Phase 3: services.py and CLI Subcommands

1. Create `agent_hub/services.py` with cross-platform service lifecycle functions
2. Add `launch`, `services`, and `stop-all` subcommands to `cli.py`
3. Test each subcommand

### 9.4 Phase 4: Config, Dependency, and Gitignore Updates

1. Add `mcp>=1.0.0` to `agent-hub/pyproject.toml`
2. Update `agent-hub/.gitignore` (add `logs/`, `gui/node_modules/`, `gui/dist/`)
3. Update top-level `.gitignore` (remove root-level log patterns)
4. Remove `watchdog` from top-level `requirements.txt`
5. Re-install: `pip install -e agent-hub/`

### 9.5 Phase 5: Documentation

1. Update `CLAUDE.md` with new paths and CLI commands
2. Update `agent-hub/docker/README.md` and `CONTAINER-GUIDE.md`
3. Rewrite `agent-hub/README.md` as comprehensive package reference

### 9.6 Phase 6: Final Cleanup

1. Delete `launch.sh` and `pd-status` from repo root
2. Verify no remaining references to old paths

---

## 10. Execution

<!--
EXECUTION PHASE INSTRUCTIONS
============================
NOTE: Do NOT delete this comment block. It provides guidance for execution.

- Sections 1-9 are PRE-APPROVED content - do NOT modify during execution
- Only THIS TABLE and the comment sections below should be edited during execution phase

COLUMNS:
- EI: Execution item identifier
- Task Description: What to do (static, from Implementation Plan)
- Execution Summary: Narrative of what was done, evidence, observations (editable)
- Task Outcome: Pass or Fail (editable)
- Performed By - Date: Signature (editable)

TASK OUTCOME:
- Pass: Task completed as planned
- Fail: Task could not be completed as planned - attach VAR with explanation

VAR TYPES (see VAR-TEMPLATE):
- Type 1: Use when the failed task is critical to CR objectives
- Type 2: Use when impact is contained and CR can conceptually close

EXECUTION SUMMARY EXAMPLES:
- "Implemented per plan. Commit abc123."
- "Modified src/module.py:45-67. Unit tests passing."
- "Created SOP-007 (now EFFECTIVE)."
-->

| EI | Task Description | Execution Summary | Task Outcome | Performed By - Date |
|----|------------------|-------------------|--------------|---------------------|
| EI-1 | Phase 1: File moves (git mv) and delete obsolete files | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-2 | Phase 2: Path fixes (container.py, config.py, docker-compose.yml, shell scripts) | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-3 | Phase 3: Create services.py and add CLI subcommands | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-4 | Phase 4: Config, dependency, and gitignore updates | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-5 | Phase 5: Documentation updates (CLAUDE.md, READMEs) | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-6 | Phase 6: Final cleanup — remove launch.sh, pd-status | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |

<!--
NOTE: Do NOT delete this comment. It provides guidance during document execution.

Add rows as needed. When adding rows, fill columns 3-5 during execution.
-->

---

### Execution Comments

| Comment | Performed By - Date |
|---------|---------------------|
| [COMMENT] | [PERFORMER] - [DATE] |

<!--
NOTE: Do NOT delete this comment. It provides guidance during document execution.

Record observations, decisions, or issues encountered during execution.
Add rows as needed.

This section is the appropriate place to attach VARs that do not apply
to any individual execution item, but apply to the CR as a whole.
-->

---

## 11. Execution Summary

<!--
NOTE: Do NOT delete this comment. It provides guidance during document execution.

Complete this section after all EIs are executed.
Summarize the overall outcome and any deviations from the plan.
-->

[EXECUTION_SUMMARY]

---

## 12. References

- **SOP-001:** Document Control
- **SOP-002:** Change Control
- **SOP-004:** Document Execution
- **SOP-005:** Code Governance
- **CR-062:** pd-status utility (being absorbed)
- **CR-063:** PID file removal (completing the elimination)
- **CR-068:** Agent Hub GUI scaffold (being moved)

---

**END OF DOCUMENT**

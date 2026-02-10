# Session 2026-02-09-005 Summary

## CR-072: Demand-Driven Bootstrap and Terminal Fix — CLOSED

### What Was Done

Implemented demand-driven bootstrapping for the Agent Hub stack so each layer
ensures its dependencies are running before proceeding, plus fixed a terminal
escape sequence bug and updated READMEs.

### Key Changes (12 files)

**Hub auto-start (Python):**
- `agent-hub/agent_hub/cli.py` — Added `ensure_mcp_servers(config)` call in `start()` command
- `agent-hub/agent_hub/config.py` — Added `_find_project_root()` that walks up from cwd looking for `QMS/` + `.claude/` markers (discovered during UAT when Tauri spawned Hub from gui subdirectory)

**GUI auto-bootstrap (TypeScript + Rust):**
- `agent-hub/gui/src/ensureHub.ts` — New file: `isHubAlive()` health check + `ensureHub()` spawn-and-poll logic using `invoke("spawn_hub")`
- `agent-hub/gui/src-tauri/src/lib.rs` — Added Rust `spawn_hub` Tauri command with `CREATE_NEW_PROCESS_GROUP | CREATE_NO_WINDOW` (Windows) / `setsid` (Unix) for detached spawning (discovered during UAT when GUI close killed Hub)
- `agent-hub/gui/src/types.ts` — Added `"bootstrapping"` to `ConnectionStatus` union
- `agent-hub/gui/src/App.tsx` — Replaced `useHubConnection()` hook with `ensureHub().then(hubConnection.connect)` lifecycle
- `agent-hub/gui/src/components/StatusBar.tsx` — Added "Starting Hub..." label for bootstrapping state
- `agent-hub/gui/src/styles/global.css` — Added `.bootstrapping` dot style (yellow, pulsing)

**Terminal DA escape fix:**
- `agent-hub/gui/src/hooks/useHubConnection.ts` — Added `muteInput` Set to suppress input during buffer replay + regex filter for DA response sequences as defense-in-depth

**Documentation:**
- `agent-hub/README.md` — Fixed stale `services` -> `status` refs, documented MCP auto-start
- `agent-hub/gui/README.md` — Updated prerequisites, added Auto-Bootstrap section
- `agent-hub/gui/src-tauri/capabilities/default.json` — Unchanged (shell:allow-spawn added then reverted)

### UAT Results (all 6 scenarios passed)

1. Clean-state GUI launch — bootstrapped Hub from scratch
2. Hub survives GUI close — detached process, immediate reconnect on relaunch
3. No DA escape text on tab open/re-open
4. `agent-hub start` auto-starts MCP servers
5. `agent-hub launch claude` full stack from clean state
6. Venv deactivated — graceful fallback, no crash

### Deviations from Plan

Two issues discovered during UAT, both resolved in-session:

1. **Project root detection**: `HubConfig` defaulted to `Path.cwd()`, breaking when spawned from subdirectories. Fixed with `_find_project_root()` in `config.py`.
2. **Process lifecycle**: Tauri shell plugin creates child processes that die with the GUI. Replaced with Rust `spawn_hub` command using OS-level process detachment.

### QMS Workflow

CR-072: CREATE -> PRE_REVIEW (recommend) -> PRE_APPROVE (v1.0) -> RELEASE ->
IN_EXECUTION (4 checkout/checkin cycles, v1.1-v1.4) -> POST_REVIEW (recommend) ->
POST_APPROVE (v2.0) -> CLOSED

# Session 2026-02-09-002 Summary

## CR-070: Agent Session Health Detection — CLOSED

Addressed the orphaned container gap identified during UAT in Session 2026-02-09-001. The Hub previously equated "container running" with "agent active," but when a user exits Claude Code (instead of detaching from tmux), the container persists while the session is dead.

### Changes

**New state: STALE**
- Added `STALE = "stale"` to `AgentState` enum in `models.py`
- Added `session_alive: bool` field to `Agent` model

**Session health checking**
- `container.py`: `is_session_alive()` — lightweight `docker exec tmux has-session -t agent` check
- `container.py`: `restart_session()` — reuses `_exec_claude()` + `_wait_for_ready()` for recovery
- `hub.py`: `_container_sync_loop` checks session health every 10s, transitions RUNNING → STALE when session dies
- `hub.py`: `_discover_running_containers` detects stale on Hub startup
- `hub.py`: `restart_agent_session()` — recovers STALE → RUNNING

**CLI recovery**
- `attach` command: when agent is stale, presents R/T/C menu (Restart session, Teardown container, Cancel)
- `services` command: enriches container display with Hub session state, shows "stale" distinctly
- `services` command: shows "session state unknown (Hub down)" when Hub unavailable
- `status` command: yellow color for stale state

**API**
- `POST /agents/{id}/restart-session` endpoint for session recovery
- `session_alive` field in all agent responses via Pydantic serialization

**Services display fix**
- `services.py`: stale agents now included in Hub info count (e.g., "1 stale, 6 stopped")

### UAT Results (performed by lead)

All 6 test scenarios passed:
1. Stale detection after Claude Code exit
2. Attach recovery menu (R/T/C)
3. Restart session in existing container
4. Normal flow unaffected after restart
5. Teardown removes container cleanly
6. Hub restart discovers stale containers

### QMS Workflow

- CR-070 drafted, pre-reviewed (QA recommend), pre-approved, released
- Executed: 7 EIs all Pass
- Post-review round 1: QA request-updates (stale commit reference in execution summary)
- Corrected, post-review round 2: QA recommend
- Post-approved, closed

### Key Commits
- `f2c64ec` — CR-070 IN_EXECUTION: implementation (5 files)
- `54da65f` — CR-070 IN_EXECUTION: UAT results and services display fixes
- `46ed016` — CR-070 CLOSED

## Design Discussion: Session Management Tiers

Discussed broader session management strategy beyond the orphaned container fix:

- **Tier 1 (this CR):** Session health detection — STALE state, tmux health check, CLI recovery
- **Tier 2 (future):** Session lifecycle management — automatic recovery, session event logging, session history
- **Tier 3 (future):** Session-first architecture — Hub manages "sessions" as primary entities, containers as implementation details

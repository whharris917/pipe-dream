# Session 2026-02-09-004 Summary

## Purpose
Implement CR-071: Consolidate `services` into `status` command with robustness improvements.

## What Happened

### CR-071 Lifecycle (pre-compaction)
1. **Created** CR-071 from template, authored all sections
2. **First review round** (v0.1) — QA recommended
3. **Revisions** based on Lead feedback:
   - Removed Hub uptime from output
   - Always show three sections (Services, Containers, Agents) regardless of Hub state
   - Authoritative empty-state message: "No containers found (direct Docker query -- does not depend on Hub)."
   - Expanded Agents table: added UPTIME, START POLICY, STOP POLICY columns
   - Added `models.py` and `routes.py` to scope for AgentSummary expansion
4. **Second review round** (v0.2) — QA recommended
5. **Pre-approved** by QA (v1.0)
6. **Released** for execution

### Implementation (EI-1 through EI-7, commit 6a33f1a)
- `hub.py`: `start_agent()` raises RuntimeError when agent already RUNNING
- `container.py`: running-container guard before `_remove_if_exists()`
- `models.py`: expanded `AgentSummary` with `shutdown_policy` and `started_at`
- `routes.py`: populated new fields in `/api/status` and `/api/agents`
- `services.py`: added `classify_container()` helper
- `cli.py`: rewrote `status` with three-section unified output, removed `services`, added 409 handling to `launch`

### UAT (EI-8) — 7 scenarios, all Pass
1. Status with Hub down, no containers — three sections, authoritative message
2. `agent-hub services` returns "No such command"
3. Status with Hub up, all agents stopped — full three-section output
4. API returns new fields (`shutdown_policy`, `started_at`)
5. Container classification (managed vs manual)
6. Duplicate launch prevention (HTTP 409 with helpful message)
7. Per-agent uptime display — initially wrong (timezone bug), fixed and confirmed

### Bugs Found and Fixed
- **Timezone mismatch** (commit 1e05cb0): Hub stores `started_at` as naive local time via `datetime.now()`, but CLI compared against `datetime.now(timezone.utc)`, causing ~5h offset on Windows. Fixed by using naive local time consistently.
- **cp1252 encoding crash** (commit 3ea50db): Unicode checkmark (`\u2713`), cross (`\u2717`), and em-dash (`\u2014`) in `click.echo()` calls crash on Windows cp1252 console. Replaced with ASCII equivalents (`+`, `x`, `--`) in `services.py` and `cli.py`.

### Post-Review and Closure
- First post-review/approval cycle completed, then **withdrawn** to fix cp1252 bug
- Second post-review — QA recommended
- Post-approved by QA (v2.0)
- **CR-071 CLOSED** (commit 256156a)

### Housekeeping (pre-compaction)
- Initialized session (Session-2026-02-09-004)
- Wrote summary for empty Session-2026-02-09-003 (planning session)
- Added `.pytest_cache/` to `.gitignore`
- Reverted phantom diffs in `hub-uat.log` and `Cargo.toml`

## Commits This Session
| Commit | Description |
|--------|-------------|
| `6a33f1a` | CR-071 core implementation (EI-1 through EI-7) |
| `b336b9d` | CR-071 EI table update and mid-session summary |
| `1e05cb0` | Fix timezone mismatch in uptime display |
| `3ea50db` | Fix cp1252 encoding crash (Unicode → ASCII) |
| `256156a` | CR-071 CLOSED |

## Lessons Learned
- Always answer user questions immediately, even mid-workflow. Ignoring a question twice cost an extra review cycle.
- Hub uses naive local time (`datetime.now()`); any consumer must match. Don't assume UTC.
- Windows cp1252 encoding breaks on common Unicode symbols — use ASCII-safe characters for CLI output.

## Current State
- **CR-071:** CLOSED, v2.0
- Hub is running on port 9000 with `agent-claude` container active
- Git MCP started during UAT (port 8001), QMS MCP running (port 8000)

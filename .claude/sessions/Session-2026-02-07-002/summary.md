# Session 2026-02-07-002: Agent Hub Genesis

## Overview

Design discussion and implementation session that created the foundational Agent Hub infrastructure — a Python service for multi-agent container orchestration. The session began with a thought experiment about how orchestration behavior should adapt based on whether agents are running in containers vs. spawned as sub-agents, which led directly into building the Hub as the solution.

## Deliverables

### CR-060: Agent Hub Genesis - Core Infrastructure (CLOSED)

**New `agent-hub/` package (16 files, ~750 lines of Python):**

| Component | File | Purpose |
|-----------|------|---------|
| Models | `agent_hub/models.py` | Agent, AgentState, LaunchPolicy, ShutdownPolicy, AgentPolicy |
| Config | `agent_hub/config.py` | HubConfig with pydantic-settings (paths, Docker, agent roster) |
| Container | `agent_hub/container.py` | Docker SDK lifecycle — SETUP_ONLY two-phase startup from launch.sh |
| Inbox | `agent_hub/inbox.py` | Watchdog-based inbox monitoring with async callbacks |
| Notifier | `agent_hub/notifier.py` | tmux send-keys injection (ported from inbox-watcher.py) |
| Policy | `agent_hub/policy.py` | Launch/shutdown policy evaluation engine |
| Hub | `agent_hub/hub.py` | Core orchestrator wiring all components together |
| API | `agent_hub/api/` | FastAPI REST endpoints on :9000 (8 endpoints) |
| CLI | `agent_hub/cli.py` | 5 commands: start, status, start-agent, stop-agent, set-policy |

**Key commits:**
- `2e1fa10` — Hub code + CR-060 execution state
- `817c5d5` — CR-060 closure

## Design Discussion

The session opened with a key observation: CLAUDE.md and SOP-007 only describe the sub-agent-spawned-with-Task-tool workflow. When agents run autonomously in containers, the orchestrator's behavior should change (just route the document instead of spawning a sub-agent) — but this requires knowing which agents are currently running.

**Decision:** Don't update SOPs yet (current sub-agent model is the effective process; containers are experimental). Instead, use the insight to inform Hub development — the Hub's `GET /api/agents` endpoint is exactly the discovery mechanism that solves this problem.

**Connection to Ouroboros vision:** The Hub is platform-layer infrastructure (engine-agnostic). It manages containers, terminals, inboxes, and agent state without encoding QMS-specific logic.

## Testing Results

All 8 EIs passed. Integration test confirmed:
- Hub starts on :9000, all 7 agents listed as STOPPED
- `start-agent qa` creates Docker container with correct mounts
- `docker ps` confirms container running
- `status` shows qa as RUNNING
- `stop-agent qa` stops and removes container
- Policy set/get works via CLI and API

## Bug Fix During Execution

The idle check loop was evaluating ALL shutdown policies (including ON_INBOX_EMPTY) every 60 seconds. This caused agents with ON_INBOX_EMPTY policy to auto-stop immediately after manual start if their inbox was empty. Fixed by scoping the idle check to only evaluate IDLE_TIMEOUT policy; ON_INBOX_EMPTY is evaluated only in the inbox change handler.

## Process Notes

- QA caught a revision_summary deficiency during post-review (still read "Initial draft" at v1.1). Corrected and re-routed.
- Genesis sandbox model used per SOP-005 Section 7.2 — no SDLC governance yet, formal adoption CR will come later.

## Files Created

- `agent-hub/` — Entire new package (16 source files)
- `agent-hub/.gitignore` — Excludes egg-info, __pycache__, dist, build
- `agent-hub/pyproject.toml` — Project config with `agent-hub` CLI entry point

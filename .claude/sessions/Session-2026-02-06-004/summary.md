# Session 2026-02-06-004: Orchestration Refresh + Ouroboros Reactor Vision

## Overview

Design discussion session with two deliverables: a refreshed multi-agent orchestration design document (grounded in what was actually built over the past three days), and a far-future vision document for the Ouroboros Reactor — an experiment in exogenic AI evolution using the Pipe Dream platform.

## Deliverables

### 1. Multi-Agent Orchestration Refresh (`multi-agent-orchestration-refresh.md`)

Successor to the Session-2026-02-04-002 design documents. Describes the system as it actually exists after CR-056 through CR-058, then charts the path to Hub (Rung 4) and GUI (Rung 5).

Key sections:
- **The Ladder (revised):** We're on Rung 3 (multi-agent sessions). Rungs 1-3 operational, 4-5 in design.
- **What was actually built:** Full inventory of launch.sh, stdio proxy, inbox watcher, per-agent isolation, tmux notification injection, SETUP_ONLY pattern.
- **Architecture that emerged:** Five discoveries that diverged from original design — all made the system simpler or more reliable.
- **Hub design (revised):** Python service absorbing launch.sh's role + Docker SDK lifecycle, integrated inbox watching, PTY multiplexing, policy engine, REST+WebSocket API.
- **GUI design (revised):** Tauri + xterm.js terminal multiplexer with QMS-aware sidebar. Pure terminal passthrough.
- **Development plan:** Hub in 6 phases, GUI in 4 phases.

### 2. Ouroboros Reactor Vision (`ouroboros-reactor-vision.md`)

A far-future vision for Pipe Dream as a general-purpose multi-agent collaboration platform, with the QMS as one pluggable "engine" among many.

Core concepts:
- **Exogenic evolution:** Improving AI effectiveness by evolving the environment (rules, conventions, knowledge), not the model. Hold the model constant; change the world it operates in.
- **The meme as atomic unit:** Not documents with types and workflows, but transmissible ideas — procedures, conventions, templates, warnings — that propagate through a shared commons based on utility.
- **Platform/engine separation:** The container infrastructure, Hub, GUI, commons, messaging, and audit trail are the *platform*. The QMS (SOPs, CRs, workflows) is one *engine*. A different engine — or no engine at all — could run on the same platform.
- **Emergent governance:** The deepest question: what governance structures do agents invent when none are imposed?

## Design Decisions

| Decision | Rationale |
|----------|-----------|
| Hub and GUI are platform-layer work | Should be engine-agnostic, not hardcode QMS assumptions |
| Hub absorbs existing infrastructure | Wraps launch.sh, inbox-watcher.py, MCP health checks in a programmable service |
| Genesis Sandbox for Hub and GUI | Both are new standalone systems; free-form development before QMS adoption |
| Platform/engine separation as north star | Doesn't change immediate work, but guides architectural choices |

## No Code Written

This was a pure design and vision session. No code changes, no QMS document activity.

## Files Created

- `multi-agent-orchestration-refresh.md` — Refreshed orchestration design
- `ouroboros-reactor-vision.md` — Exogenic evolution vision document
- `summary.md` — This file

## Open Items

- Hub implementation: begin with Phase 1 (skeleton + container manager) in a genesis sandbox
- GUI implementation: begins after Hub Phase 4 (WebSocket API exists)
- Open questions from orchestration refresh (Section 7) to be resolved when implementation starts

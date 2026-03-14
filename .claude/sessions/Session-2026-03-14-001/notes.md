# Session-2026-03-14-001

## Current State (last updated: all tasks complete)
- **Active document:** CR-110 (IN_EXECUTION v1.1)
- **Current task:** All three cleanup tasks complete — ready to commit and push
- **Blocking on:** Nothing
- **Next:** Awaiting direction from Lead

## Progress Log

### Session Start
- Read previous session notes (Session-2026-03-12-001)
- Previous session completed: resource-oriented endpoints, 1:1 renderer audit, gap fixes
- Read QMS docs (Policy, START_HERE, Glossary)

### Maze Workflow Removal
- Removed entire maze workflow from `wfe-ui/app.py` (~570 lines):
  - `_MAZE` dict (13 rooms), `_ITEMS` dict (8 items), `_MAX_HP`/`_START_HP` constants
  - `_maze_default_data()`, `_maze_data()`, `_maze_items_here()`
  - `_render_maze_room()` (~200 lines), `_render_death()`
  - `"maze"` entry from `_WORKFLOWS` registry
  - Maze branches in `_render_agent_node()`, `_process_agent_action()`, `agent_resource_post()`
- Removed Map and Terminal renderers from `agent_observer.html` (~403 lines):
  - Map renderer (canvas-based 2D dungeon map)
  - Terminal renderer (CRT phosphor ASCII art)

### Renderer/Mode Terminology Rename
- Renderer distinction: "Workflow" → "Rendered" (id, label, CSS selector `#rc-rendered`)
- Scope toggle: "FoV" → "Full" (button id/label, JS `viewMode`, all toggle logic)
- Variables: `before_fov`/`after_fov` → `before_full`/`after_full` in `_execute_and_feedback()`

### Event Log Removal
- Removed Event Log panel from Observer:
  - HTML: removed `panel-log` div
  - CSS: removed `.panel-log`, `.log-entries`, `.log-entry`, `.log-time`, `.log-type.*`, `.log-detail`, `.view-empty`, `border-right` from `.panel-view`
  - JS: removed `logEl`, `addLog()` function, all `addLog()` calls in SSE handler, history replay
- Server-side cleanup in `app.py`:
  - Removed `_workflow_history` dict and history tracking from `_wf_notify()`
  - Added `_workflow_last_feedback` dict for reconnect feedback recovery
  - SSE init event sends `last_feedback` directly instead of full history array
  - `agent_reset()` clears `_workflow_last_feedback` instead of `_workflow_history`

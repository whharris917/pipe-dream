# Session-2026-03-21-002

## Current State (last updated: unified renderer + agent view toggle complete)
- **Active document:** CR-110 (IN_EXECUTION v1.1)
- **Current task:** Complete. Multi-instance + unified renderer + agent view toggle all implemented.
- **Blocking on:** Nothing
- **Next:** Sub-workflow embedding (plan saved to session folder), extend Agent View to more pages

### Unified Renderer — Agent Portal
- Established design principle: every page is agent-renderable, human UI is one renderer
- `GET /agent` with `Accept: application/json` returns `{state, instructions, affordances}` — workflow types, instances, open/create affordances
- `POST /agent/{wf_id}/new` returns JSON (201) for agents, redirect for browsers
- Portal SSE stream at `/agent/stream` — init event with full portal state, updates on instance create/delete
- `_render_portal()` builds the canonical representation, used by both HTML template and JSON API
- `_wf_notify_portal()` pushes events to portal SSE observers on create/delete
- **Agent View toggle** in `base.html` — button at bottom-left, toggles between Human View and Agent View
  - Connects to page's SSE stream, renders state as formatted JSON in a dark panel
  - Button highlights blue when active
  - Only appears on pages that pass `agent_view_stream` template variable (portal is first)
- Updated PROJECT_STATE with the Unified Renderer Principle and reordered forward plan

## Progress Log

### Session Start
- Read previous session notes (Session-2026-03-21-001)
- Previous session: docs update, builder banner unification, auto-collapse, condition labels

### Sub-Workflow Design Discussion
- Lead wants workflows to embed other workflows as sub-steps (e.g., Create Executable Table inside Create CR)
- Design decisions: isolated state, arbitrary nesting (stack-based), URL schema change, banner replacement
- Full implementation plan written and saved to `Session-2026-03-21-002/subworkflow-plan.md`
- Lead identified prerequisite: multi-instance support needed first

### Multi-Instance Workflow Support — Implemented
- **Problem:** Engine had 1:1 mapping between workflow type and state file. Can't have two CRs in progress.
- **Solution:** Instance IDs (8-char hex UUIDs), per-type directories, instance-aware URLs

**State layer changes (app/app.py):**
- `_wf_state_path(wf_id, inst_id)` → `data/workflows/{wf_id}/{inst_id}.state.json`
- `_wf_load_state`, `_wf_save_state` now take instance_id
- `_wf_list_instances(wf_id)` scans directory, returns summaries
- `_wf_new_instance_id()` returns `uuid.uuid4().hex[:8]`
- `_cache_key(wf_id, inst_id)` for in-memory cache compositing
- Auto-migration: old flat `{wf_id}.state.json` files moved to `{wf_id}/{new_uuid}.state.json`

**URL scheme:**
- Old: `/agent/{wf_id}/{resource}`
- New: `/agent/{wf_id}/{inst_id}/{resource}`
- New route: `POST /agent/{wf_id}/new` → creates instance, redirects to observer

**Runtime threading:**
- `instance_id` parameter added to: `render_page()`, `dispatch()`, `render_node()`, `process_action()`, `get_node_affordances()`
- actions.py uses module-level `_current_instance_id` + wrapper pattern to avoid changing 30+ internal function signatures
- Builder similarly updated with `_current_instance_id` pattern
- `api_base` in affordances now includes instance_id: `/agent/create-cr/a3f7c2d1`

**Dashboard (agent.html):**
- Redesigned from flat card grid to grouped display with instance tables
- Each workflow type shows: title, description, "+ New" button, instance list (ID, node, Observe, Reset)

**Observer (agent_observer.html):**
- Shows instance_id in header

**Verified end-to-end:**
- Import clean
- Migration works (old files → instance directories)
- POST /new creates instance with UUID, redirects to observer
- GET /{inst_id} returns state with instance-scoped affordance URLs
- POST /{inst_id}/{resource} mutates correct instance
- Instances are independent (state isolation confirmed)
- Reset deletes correct instance file

# Session-2026-03-10-001

## Current State (last updated: stage→node refactor planned)
- **Active document:** CR-110 (IN_EXECUTION v1.1)
- **Current task:** Agent Portal — refactoring stages→nodes, field-centric→node-centric ownership
- **Blocking on:** Nothing
- **Next:** Implement node-centric field ownership refactor

## Progress Log

### Agent Portal Refactor: Multi-Workflow Support

**Problem:** Single global `_agent_state` dict — only one workflow active at a time. No dashboard. No state persistence.

**Solution:** Per-workflow state on disk + workflow registry + new route structure.

#### Changes to `wfe-ui/app.py`:
- **Removed:** `_agent_state`, `_agent_notify`, `_observer_queues` (global singletons)
- **Added:** `_WORKFLOW_STATE_DIR` (`data/workflows/`), per-workflow state files (`<id>.state.json`)
- **Added:** `_workflow_observers`, `_workflow_history`, `_workflow_current_path` (per-workflow in-memory)
- **Added:** `_wf_load_state()`, `_wf_save_state()`, `_wf_notify()` — per-workflow state management
- **Added:** `_WORKFLOWS` registry — maps workflow IDs to type + display metadata
- **Updated:** All render/process functions now accept `workflow_id` parameter
- **Updated:** All affordance URLs are now dynamic (`f"/agent/{workflow_id}"`)
- **Updated:** State mutations are saved to disk immediately after each change
- **Added:** Rate limiting is now per-workflow (`_last_action_times` dict)

#### Route changes:
| Old | New | Purpose |
|-----|-----|---------|
| `GET /agent` | `GET /agent` | Dashboard (was empty placeholder) |
| `GET /agent/current` | `GET /agent/<id>/observe` | Observer SPA per workflow |
| `GET /agent/current/stream` | `GET /agent/<id>/stream` | SSE per workflow |
| `GET /agent/<path>` | `GET /agent/<id>` | Agent reads workflow state |
| `POST /agent/<path>` | `POST /agent/<id>` | Agent takes action |
| — | `POST /agent/<id>/reset` | Delete workflow state |

#### Template changes:
- `agent.html`: Now extends `base.html`, shows workflow grid with status, Observe links, Reset buttons
- `agent_observer.html`: SSE URL and title are now template variables (`{{ stream_url }}`, `{{ workflow_title }}`)

#### Key design decisions:
- State persisted to disk as JSON — survives server restart
- No sessions, no instances — each workflow has exactly one state
- Workflows directory auto-created at import time, gitignored via existing `data/*` rule
- Maze and create-cr coexist as independent workflows in the registry

### Explicit Renderer Declarations
- **Problem:** Map and Terminal renderers appeared for create-cr workflow due to heuristic `matches()` functions guessing from JSON data shape
- **Fix:** Each workflow in `_WORKFLOWS` registry now declares its `renderers` list explicitly
  - maze: `["raw", "map", "terminal"]`
  - create-cr: `["raw", "workflow"]`
- Renderer list passed to Observer template as JS array (`allowedRenderers`)
- Buttons shown/hidden at registration time based on list membership — no heuristics
- Removed all `matches()` functions from Map, Terminal, and Workflow renderers
- Default renderer is now the last in the declared list (most specific)

### Observer Init Fix
- **Problem:** Observer showed nothing on fresh connect — SSE init event sent raw state dict, but Observer expected a rendered page with `state` key. No history to replay on fresh workflow.
- **Fix:** SSE init now sends `page: _render_agent_node(workflow_id)` — the fully rendered page — instead of raw state. Observer calls `extractState(ev.page)` immediately on init.

### Focus / Field of View Split
- **Design:** GET returns full Field of View (FoV). POST returns Focus — the subset that changed.
- **Focus shape (final):**
  ```json
  {
    "message": "Set title = \"...\"",
    "changed": {"Document Title": {"value": "...", "instruction": "..."}},
    "new_affordances": [<full affordance objects for newly available actions>]
  }
  ```
- Focus is a strict subset of the FoV — every key in the Focus exists in the FoV at the same path. Bijective mapping preserved.
- `message` key added to FoV as well (persisted in state), always shows the most recent action confirmation. Null on fresh state.
- `_compute_focus(before, after)` diffs fields by value, detects new affordances by label
- Action processors now set `data["message"]` before saving (was `page["message"]` after render)
- POST route handler: captures before-FoV, runs action, captures after-FoV, diffs, returns Focus. Pushes full after-FoV to SSE for Observer.
- Verified: field changes detected, Proceed gate unlock detected, GET still returns full FoV
- **CR workflow only** — maze not yet updated (will follow same pattern)

### Observer Focus Rendering
- **Design:** Focus highlights persist visually (no fade) until the next action replaces them
- **CSS classes:** `.wf-focus` (blue left border + light blue bg) for changed fields, `.wf-aff-focus` (blue left border) for unlocked affordances
- **JS changes:** `currentFocus` variable tracks latest Focus; `broadcastState()` accepts focus parameter; Workflow renderer's `render()` and `renderFields()` apply highlight classes
- **SSE integration:** Result events now carry `focus` alongside `result`; Observer extracts both and passes to renderer
- **Live walkthrough verified by Lead** — walked through full CR initiation flow:
  - Set title → Document Title highlighted
  - Set affects_code → Code Impact + Affects Submodule highlighted
  - Set affects_submodule → cascade: Submodule field appeared, 4 select affordances unlocked with accent
  - Select submodule → SDLC Governed computed field appeared
  - Set purpose → Purpose highlighted, Proceed gate unlocked with accent
  - Proceed to Change Definition → massive cascade: 11 new fields, 11 new affordances all highlighted
- **Result:** Lead confirmed "It looked perfect!"

### FoV/Focus View Toggle in Observer
- **Feature:** Second toggle group (FoV | Focus) added to Observer header, next to renderer toggle
- **Behavior:** Focus mode only affects Raw renderer — shows the focus JSON directly. Workflow renderer always shows full FoV with highlights regardless of toggle.
- **Design discussion:** Considered making Workflow renderer Focus-aware (sparse FoV), but rejected — agent might misinterpret a partial affordance list as the complete set. Focus is a diff receipt, not a replacement view.
- **Focus shape refined:**
  - Dropped `unlocked` key (redundant with `new_affordances`)
  - Renamed `affordances` → `new_affordances` (eliminates ambiguity about complete vs. new list)
  - Final shape: `{message, changed, new_affordances}`
- **Verified by Lead** — full walkthrough: reset → title → code impact → submodule → purpose. Confirmed "Perfect!"

### Select Affordance Collapse
- Collapsed select-type fields from N affordances (one per option) to 1 affordance with pipe-delimited options in placeholder
- Fixed `_compute_focus` — was comparing by ID AND label, but sequential IDs shift when affordances appear/disappear. Now compares by label only.

### Stage → Node Refactor (planned)
- **Problem:** Fields declare `stages: [initiation, definition, preflight, submitted]` — field-centric visibility is clumsy and redundant
- **Solution:** Fields nest under their owning node in the YAML. Visibility = structural nesting.
  - Initiation owns: title, affects_code, affects_submodule, submodule, sdlc_governed, purpose
  - Definition owns: scope_*, current_state, proposed_state, change_description, justification, impact_*, testing_summary
  - Preflight/Submitted: `show_all_fields: true` to aggregate all fields for review
- **Terminology:** "stage" → "node" throughout (YAML keys, Python variables, state keys, API responses, Observer JS)

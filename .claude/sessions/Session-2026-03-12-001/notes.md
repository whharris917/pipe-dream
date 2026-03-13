# Session-2026-03-12-001

## Current State (last updated: all tasks complete)
- **Active document:** CR-110 (IN_EXECUTION v1.1)
- **Current task:** All three tasks complete — committed and pushed
- **Blocking on:** Nothing
- **Next:** Awaiting direction from Lead

## Progress Log

### Session Start
- Read previous session notes (Session-2026-03-10-001, Session-2026-03-11-001)
- Previous session completed: affordance options for boolean/select fields, HATEOAS/agent API research report
- Planned next step from last session: implement resource-oriented endpoint refactor (per-field URLs)
- Read QMS docs (Policy, START_HERE, Glossary)
- MCP server reconnected successfully

### Resource-Oriented Endpoint Refactor
- **Problem:** All agent actions went through single `POST /agent/<workflow_id>` with action discriminator in body (`{"action": "set_field", "field": "title", "value": "..."}`)
- **Fix:** Each affordance is now a literal HTTP instruction with its own URL:
  - CR fields: `POST /agent/create-cr/title` with body `{"value": "..."}`
  - CR navigation: `POST /agent/create-cr/proceed` with body `{}`
  - Maze actions: `POST /agent/maze/move` with body `{"direction": "east"}`
  - Bodyless actions: `POST /agent/create-cr/submit` with `{}`
- **Changes to `wfe-ui/app.py`:**
  - `_compute_feedback()`: signature changed from `action_body: dict` to `acted_field_key: str = None`; `_aff_key()` now uses URL instead of body fields for stable affordance identity
  - `_cr_build_affordances()`: all affordance URLs now `f"{api_url}/{key}"` or `f"{api_url}/{action}"`; bodies contain only parameters, no action discriminator
  - `_render_maze_room()`: all maze affordances use per-action URLs (`/move`, `/pick_up`, `/attack`, etc.)
  - `_render_death()`: restart affordance uses `/restart` URL
  - New `_execute_and_feedback()` helper: extracted shared POST logic (before/after FoV capture, feedback computation, SSE notification)
  - New `POST /agent/<workflow_id>/<resource>` route: translation layer that maps resource + body to internal action format
  - Old `POST /agent/<workflow_id>` preserved as backward-compatible legacy endpoint
  - `_CR_FIELD_KEYS` set computed at import time for O(1) resource-route dispatch
- **Verified:** All affordances across both workflows use resource-oriented URLs with no action discriminator in body. Feedback diff works correctly with URL-based identity. Boolean validation, cascade effects, proceed gate, navigation all functional.

### FoV/Renderer 1:1 Audit + Message Removal
- **Audit:** Reviewed Workflow renderer against actual JSON structure. Found gaps:
  - `message` — redundant with Feedback's `attempted_action`
  - `state.node` — invisible (fallback for node_title, which always exists)
  - `state.completed_nodes` — not rendered (lifecycle banner uses `lifecycle_completed` instead)
  - Field `options` — not rendered by `renderFields()`
  - Affordance `options` — not rendered in affordance block
  - Dead `state.review` code in renderer
- **Message removal (done):**
  - Removed `"message": None` from `_cr_default_data()`
  - Removed `"message": data.get("message")` from `_render_cr_node()` return dict
  - Removed all 5 `data["message"] = ...` lines from `_process_cr_action()`
  - Removed `"attempted_action": after.get("message")` from `_compute_feedback()` return dict
  - Extracted `_build_attempted_action()` — constructs description from request body
  - `_execute_and_feedback()` now sets `feedback["attempted_action"]` from request body for both success and error paths
  - Maze `page["message"]` (ephemeral, not persisted) left intact — used by Terminal/Map renderers
- **Dead code removal:** Removed `state.review` block and `.wf-card-review` CSS from Workflow renderer
- **1:1 gap fixes (done):**
  - `state.node` — rendered as `.wf-node-id` subtitle under section heading
  - `state.completed_nodes` — rendered as `.wf-meta` after lifecycle banner
  - Field `options` — rendered as `.wf-field-options` after value in `renderFields()`
  - Affordance `options` — rendered as `.wf-aff-options` in affordance block
  - New CSS: `.wf-meta`, `.wf-meta-key`, `.wf-meta-val`, `.wf-node-id`, `.wf-field-options`, `.wf-aff-options`
- **Verification:** Comprehensive audit confirmed all JSON keys projected at every level — no missing keys

# Session-2026-03-22-002

## Current State (last updated: push pending)
- **Active document:** CR-110 (IN_EXECUTION v1.1)
- **Blocking on:** Nothing
- **Next:** Browser testing of focus mechanism, list focus support, visual polish

## Progress Log

### Session Start
- Read previous session notes (Session-2026-03-22-001)
- Read PROJECT_STATE.md, SELF.md

### Bug Fix: Generic affordance buttons not wired
- `wfRenderAffordances()` rendered `.wf-aff-go` (parametric) and `.wf-aff-btn` (simple) buttons, but `_wfBindAffordances()` had no event listeners for either class
- Added click handlers for both: `.wf-aff-go` collects params from sibling inputs, `.wf-aff-btn` POSTs directly
- File: `human-renderer.js`

### Improvement: Generic affordance label derivation
- Property affordances (e.g. `set_property` for `sequential_execution`) showed generic "set property" label
- Now derives label from `body.key` when present, falling back to URL-derived name
- File: `human-renderer.js`

### Improvement: Text field single-line layout
- Text fields now render as: **current value** | **text input** (placeholder "New value...") | **Set button**
- Added `.wf-field-row` and `.wf-field-current` CSS classes
- File: `human-renderer.js`

### Improvement: Boolean/option field single-line layout
- Short option fields (including booleans) now render as: **current value** | [option buttons]
- Same `.wf-field-row` pattern as text fields
- File: `human-renderer.js`

### Bug Fix: Boolean fields coerced to False when null
- `renderer.py` line 385: `bool(data.get(key))` turned `None` into `False`
- Fixed to preserve `None` pass-through: `None if raw is None else bool(raw)`
- Removed `default: false` from `affects_code` and `affects_submodule` in `agent_create_cr.yaml` (changed to `null`)
- Files: `renderer.py`, `agent_create_cr.yaml`

### Improvement: Dropdown field single-line layout
- Dropdown (select) fields now show current value separately, matching text/boolean pattern
- Fixed select binding: guard JSON.parse on empty placeholder, scope Set button to parent row
- Files: `human-renderer.js`

### Bug Fix: State save crash from __option_set_ sets
- `renderer.py` injects `__option_set_*` as Python `set` objects for fast evaluator lookups
- `_wf_save_state` didn't filter these, causing `json.dump` TypeError + corrupted state files
- Fixed: added `__option_set_` prefix filter in save function
- Files: `app.py`

### Improvement: Table column affordances with current-value layout
- Column headers now show name + type as current values with rename/set-type controls using `wf-aff-inline` pattern
- Property affordances show current value + option buttons on one line
- Files: `human-renderer.js`

### Design: Focus-Based Rendering Model
- Design discussion leading to plan for server-side focus mechanism
- Focus is persisted engine state (not client-side), ensures agent-human parity
- State zone (read-only) + Focus zone (affordances) + Action bar (always visible)
- Plan saved to `.claude/plans/ancient-wiggling-platypus.md`

### Implementation: Focus/Unfocus Actions (Step 1)
- Added `_focus` and `_unfocus` action handlers in `actions.py`
- `_focus` validates target path (fields, table, table.col.N, exec) against current state
- Registered both in `resolve_resource()` in `__init__.py`
- Focus persisted in state file as `data["focus"]`
- Files: `actions.py`, `__init__.py`

### Implementation: Focus-Aware Affordance Partitioning (Step 2)
- `render_page()` now adds `state.focus`, `state.focusable` to payload
- Unfocused: emits focus affordances (one per focusable target) + action bar; suppresses all object affordances
- Focused: emits focused object's affordances + unfocus + sibling/parent nav + action bar
- Table/column/field affordances only embedded when their parent is the focus target
- Files: `renderer.py`

### Implementation: Renderer Restructure (Steps 3-4)
- Restructured `_humanPage` into three zones: state zone, focus zone, action bar
- New read-only renderers: `_wfRenderFieldsReadOnly`, `_wfRenderTableReadOnly`, `_wfRenderExecTableReadOnly`
- New focus zone: `_wfRenderFocusZone` with breadcrumb, close, sibling nav, nested focusable objects
- `_wfClassifyAffordances` sorts affordances into focus/unfocus/object/action categories
- `_wfRenderFieldAffordances` reuses existing field-row patterns in focus zone
- CSS: `.wf-focus-zone`, `.wf-focus-btn`, `.wf-focus-hint`, nav/close buttons
- Files: `human-renderer.js`

### Refinement: Labels are the renderer's responsibility
- Removed labels from `state.focusable` (now plain list of target strings)
- Removed labels from focus/unfocus affordances
- Removed `state.focus_label` from payload
- Added `_wfFocusLabel(target, s)` and `_wfFocusBreadcrumb(target, s)` in JS renderer
- Files: `renderer.py`, `human-renderer.js`

### Refinement: Focus UX polish
- Focused card gets red left border (`wf-card-focused`), table card highlighted for column focus too
- Focus zone uses matching red accent
- "Edit" buttons renamed to "Focus"
- `focus` and `focusable` added to known state keys (suppressed from extra props cards)
- Files: `human-renderer.js`

### Focus Test Workflow
- Created `data/custom_workflows/focus-test.yaml`: 7 fields (3 text, 2 select, 2 boolean), 1 table, 1 checklist list on a single node
- Engine only supports one table per node; used table + list for two collection types
- Instance `61a1f107` created for testing

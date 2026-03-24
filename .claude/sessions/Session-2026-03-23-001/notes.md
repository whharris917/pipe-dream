# Session-2026-03-23-001

## Current State (last updated: end of session)
- **Active document:** None (no QMS doc open)
- **Current EI:** N/A
- **Blocking on:** Nothing
- **Next:** Forward plan items — LNARF renderers, sub-workflow embedding, etc.

## Progress Log

### Full session: Element type vocabulary + content array + Element Library rebuild

#### Problem 1: Rendering order in Agent Portal
`Affects Submodule` toggle appeared above the `Basic Information` multi-field card
instead of below it, because `fields` and `field_groups` were separate state keys
rendered in fixed type-order. Initial fix using `content_order` metadata rejected by
user as "ontologically inconsistent."

#### Fix: Unified `content` array
Replaced separate `state["fields"]` / `state["field_groups"]` with a single ordered
`state["content"]` array. Element type embedded in each item (`"type": "text"` etc.).
Rendering order now follows YAML definition order exactly.

**Files changed:**
- `engine/runtime/renderer.py` — content building logic
- `engine/runtime/affordances.py` — type string normalization
- `engine/runtime/actions.py` — type string normalization
- `app/static/renderers/human-renderer.js` — `_sectionRenderers['content']`, `_renderContentField`, `_renderContentFieldGroup`

#### Problem 2: Element type vocabulary
Renamed field types from Python-isms (`boolean`, `select`, `computed`) to semantic names
(`toggle`, `choice`, `indicator`). Backward-compat normalization maps in `FieldDef.from_dict`
and `ListItemField.from_dict`. All 11 YAML workflow files updated.

**Files changed:**
- `engine/runtime/schema.py` — `_TYPE_MAP` on FieldDef and ListItemField
- `data/**/*.yaml` — all occurrences replaced

#### Problem 3: Field groups on Change Definition node
Combined all 11 Change Definition fields into a single `field_groups.definition` entry
with a full instruction. Node-level `instruction` retained.

**File changed:** `data/agent_create_cr.yaml`

#### Feature: Runtime instruction enforcement
`FieldGroupDef.from_dict` and `NodeDef.from_dict` now raise `ValueError` at load time
if `instruction` is missing or blank.

**File changed:** `engine/runtime/schema.py`

#### Feature: Element Library workshop rebuild
Deleted three old workshop pages (API Design, Element Library, Workflow Console) — the
old pages were built independently from the engine and did not reflect real types.

Created new `app/templates/workshop_elements.html` documenting all 7 element types
grounded in the actual engine schema and renderer:
- `text`, `toggle`, `choice`, `indicator` (leaf elements)
- `group` (container with single `set_fields` affordance)
- `table`, `list` (structural elements)

Each entry: YAML definition syntax, state JSON shape, static visual preview using
actual `wf-*` CSS classes, notes on special behaviors.

**Files deleted:** `workshop_api.html`, `workshop_console.html`, old `workshop_elements.html`,
`static/workshop/api.js`, `console.js`, `elements.js`

**Files changed:** `app/app.py` (removed 2 routes), `app/templates/workshop.html` (updated card grid)

**File created:** `app/templates/workshop_elements.html`

# Session-2026-03-31-003

## Current State (last updated: end of session)
- **Active document:** CR-110 (IN_EXECUTION v1.1)
- **Current work:** Complete — edit mode for 6 eigenform types, undo/discard, RatingForm deletion
- **Blocking on:** Nothing
- **Next:** Edit mode for remaining eigenform types, CR-110 remaining EIs

## Progress Log

### Edit mode — TextForm
- Label and instruction become inline editable inputs in edit mode
- Inputs use `font: inherit` and match `<h3>`/`<p>` margins so position doesn't shift
- Value display unchanged between modes (same-shape principle)
- Base eigenform: added `effective_instruction` property, `set_instruction` handler, `Set Instruction` edit affordance

### Edit mode — NumberForm
- Config fields (min, max, step, integer) editable via inline inputs and toggle button
- `_effective_config` property reads from `__config` in store, falls back to Python defaults
- Validation uses effective config so runtime edits take effect immediately

### Edit mode — BooleanForm
- Config fields (true_label, false_label) editable via inline inputs
- Same `_effective_config` / `__config` store pattern as NumberForm

### Edit mode — ChoiceForm and CheckboxForm
- Initially hand-coded add/remove/rename UI for options/items
- Refactored: child ListForm manages options/items, visible in edit mode (faithful projection)
- ListForm is a real child eigenform, routable via standard children traversal
- `_effective_options` / `_effective_items` reads from child ListForm's items
- `__config` store pattern eliminated — ListForm owns its own state
- Seeded from Python `options`/`items` on first bind
- Child ListForm handle wrapped to push undo on parent

### Edit mode — ListForm
- Label, instruction editable (base pattern)
- `allow_constraints` toggle via `__config` store
- Fixed items fully editable in edit mode via `relax_fixed` on OrderedCollection
- Pin toggle (📌) per item to mark/unmark as fixed
- Pin toggle per constraint pill to pin (make fixed/irremovable) or unpin (make dynamic/removable)
- Fixed constraint pills shown with amber border/background; dynamic pills in gray
- Static constraints removable in edit mode — demoted via `fixed: false` stored entry
- `effective_must_follow` in OrderedCollection updated to exclude demoted static constraints
- All item mutations (add, edit, remove, move, constraints) push undo in edit mode
- Snapshot includes ListForm value for full undo/discard support

### RatingForm deleted
- Removed from registry, gallery, vendor_assessment, README
- Vendor assessment ratings replaced with NumberForm(min=1, max=5, integer=True)
- Cleared `__structure` from stored page data to avoid load errors

### set_mode replaces toggle_edit
- `{"action": "set_mode", "mode": "edit|execute"}` replaces `{"action": "toggle_edit"}`
- Pencil icon (✏) in execution mode, play icon (▶) in edit mode
- Two distinct affordances instead of a toggle

### Undo and discard
- Base `_snapshot_edit_state()` / `_restore_edit_state()` — extensible by subclasses
- On entering edit mode: initial snapshot stored as `__snapshot`
- `_push_undo()` before each edit mutation → `__undo` stack in store
- Undo pops and restores; discard restores initial snapshot and exits edit mode
- Chrome: undo (↩, conditional on depth > 0) and discard (✕ red) buttons in edit mode
- NumberForm/BooleanForm: snapshot/restore includes `__config`
- ChoiceForm/CheckboxForm: snapshot/restore includes child ListForm state
- ListForm: snapshot/restore includes `__config` and item value

### Style refinements
- Dashed border only on outer eigenform container in edit mode
- Inner editable fields use solid `#ddd` borders (not dashed)
- Removed duplicate Edit button from NumberForm/BooleanForm normal mode (`_rendered` check)

### Commits
- `363ed74` — Edit mode for 5 types, delete RatingForm
- `13d321e` — Undo/discard, set_mode replacing toggle_edit

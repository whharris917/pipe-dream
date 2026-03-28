# Session-2026-03-28-002

## Current State (last updated: end of session)
- **Active document:** CR-110 (IN_EXECUTION v1.1)
- **Current EI:** Pending — CR-110 EI updates still needed
- **Blocking on:** Nothing
- **Next:** CR-110 remaining EIs, SDLC-WFE-RS rewrite

## Progress Log

### README Update
- Added Eigenform Type Registry, Structural Persistence, Structural Mutations, Self-Modifying Pages sections
- Added mutable-demo and survey-builder to Demo Pages table
- Fixed page-5 key to example-table; expanded architecture tree

### Eigenform Gallery Page
- Created pages/eigenform_gallery.py — interactive tutorial for all 29 eigenform types
- 8 tabbed sections covering all categories — Page #16
- Updated instructions to reflect all session changes

### Universal Clear Affordance
- has_data property + Clear button on all data eigenforms
- Overrides: ComputedForm, EntryGroup (False), RepeaterForm (custom clear with sub-scopes)

### Server-Side Validation (faithful projection)
- NumberForm/RangeForm: reject out-of-range with structured errors
- NumberForm: server-side step validation
- MemoForm: reject too-short/too-long with structured errors
- Removed browser-side validation from HTML inputs
- Number input changed to type="text" inputmode="decimal"

### PageForm Feedback Banner
- Multi-message feedback: errors accumulate per-target, success is singular
- Stored in __feedback key (persisted, survives restarts)
- Dismiss affordance in JSON + inline ✕ button; page-level actions clear all

### Store File Sync
- mtime-based cache invalidation on every access

### CheckboxForm Done Confirmation
- Requires explicit Done to complete; Done with nothing checked = "none apply"
- Removed N/A mechanism entirely
- Fixed JS key quoting for item names with spaces; added autocomplete="off"

### RankForm Done Confirmation
- Same Done pattern; removed Set Order affordance/handler/class

### Condensed Move Affordances (ListForm + RankForm)
- Two parameterized affordances (Move Up/Down) listing only valid items

### KeyValueForm Improvements
- Inline edit fields with ✓ submit and x remove in same row
- Add row inline with green + button; duplicate key rejection; condensed affordances

### ListForm UI Improvements
- Add row inline; edit rows get ✓ button; all inline buttons show POST tooltips

### Live Tooltip Updates (codebase-wide)
- All input-with-button forms update tooltip on keystroke to show actual POST body

### Codebase Refactoring (5 items)
- **`_base_state()` on Eigenform**: returns {form, key, label, instruction}. All 25 _serialize_state() implementations now use `self._base_state() | {...}`. EntryGroup special-cased for "form": "entry".
- **`_error()` on Eigenform**: `_error(msg, *, action=None, body=None)`. Removed 5 identical local implementations (listform, table, keyvalue, repeater, page). Replaced ~15 inline 3-line error patterns (number, date, memo, rating, range, rank, dynamic_choice).
- **`render_inline_button()` helper**: generates fetch JS, tooltip, escaping in one call. Used by listform (move+remove), rank (move), keyvalue (remove), page (dismiss), table (remove row/column).
- **Button style constants**: STYLE_CONFIRM, STYLE_REMOVE, STYLE_ARROW in affordances.py. Replace duplicated CSS strings across listform, keyvalue, rank, table.
- **Bonus fix**: weird_experiments.py checkbox reader filters out __confirmed internal key.

### Minor Fixes
- TextForm: is_complete rejects empty string
- NumberForm: constraints rendered in HTML below instruction

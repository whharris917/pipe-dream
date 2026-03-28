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
- Updated instructions to reflect all session changes (removed stale N/A, set_order, clamping references)

### Universal Clear Affordance
- has_data property + Clear button on all data eigenforms
- Overrides: ComputedForm, EntryGroup (False), RepeaterForm (custom clear with sub-scopes)

### Server-Side Validation (faithful projection)
- NumberForm/RangeForm: reject out-of-range with structured errors (no silent clamping)
- NumberForm: server-side step validation
- MemoForm: reject too-short/too-long with structured errors (was silently accepting)
- Removed browser-side validation (min/max/step on number, min/max on date HTML inputs)
- Number input changed to type="text" inputmode="decimal"

### PageForm Feedback Banner
- Multi-message feedback: errors accumulate per-target, success is singular
- Stored in __feedback key (persisted, survives restarts)
- Dismiss affordance in JSON + inline ✕ button (same POST, endpoint tooltip, marked rendered)
- Page-level actions clear all feedback; success clears error for same target

### Store File Sync
- mtime-based cache invalidation on every access
- External file delete → cache cleared; external modify → reload from disk

### CheckboxForm Done Confirmation
- Requires explicit Done to complete (prevents ChainForm premature auto-advance)
- Done with nothing checked = "none apply" (replaced N/A mechanism entirely)
- Toggling after Done clears confirmed state
- Fixed JS key quoting for item names with spaces; added autocomplete="off"

### RankForm Done Confirmation
- Same Done pattern; storage changed to {order, __confirmed} dict
- Removed Set Order affordance/handler/class

### Condensed Move Affordances (ListForm + RankForm)
- Two parameterized affordances (Move Up, Move Down) listing only valid items
- HTML still renders inline ▲/▼ arrows per item
- ListForm: added move_up/move_down actions alongside existing move

### KeyValueForm Improvements
- Condensed per-entry Edit/Remove into one parameterized affordance each
- Inline edit fields (key + value) with ✓ submit and x remove in same horizontal row
- Add row rendered inline with placeholder fields + green + button (matches ListForm pattern)
- Duplicate key rejection on add and edit
- All button tooltips show POST endpoint + body

### ListForm UI Improvements
- Add row inline at bottom of list (text field + green + button)
- Edit rows get green ✓ submit button with live tooltip
- All inline buttons (remove, move, add, edit) show POST endpoint tooltips

### Live Tooltip Updates (codebase-wide)
- All input-with-button forms update tooltip on keystroke to show actual POST body
- Applied to: number, date, range, textarea, text_input_add, parameterized, multi_field,
  kv_add, ListForm edit/add rows, KeyValueForm edit/add rows

### Minor Fixes
- TextForm: is_complete rejects empty string
- NumberForm: constraints rendered in HTML below instruction

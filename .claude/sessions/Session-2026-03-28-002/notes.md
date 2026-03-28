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
- Fixed page-5 key to example-table
- Expanded architecture tree to show key engine modules

### Eigenform Gallery Page
- Created pages/eigenform_gallery.py — interactive tutorial for all 29 eigenform types
- 8 tabbed sections: Simple Values, Selection, Collections, Containers, Conditional, Computed, Actions, Showcase
- Exercises every eigenform type with instructive instructions explaining behavior
- Added to README Demo Pages table — Page #16

### Universal Clear Affordance
- Added `has_data` property and `_clear_data()` method to base Eigenform
- Modified base `serialize()` to append "Clear" affordance when `has_data` is True
- Modified base `handle()` to intercept `{"action": "clear"}` before subclass dispatch
- Overrides: ComputedForm (has_data=False), EntryGroup (has_data=False), RepeaterForm (custom clear)
- Containers that override serialize() naturally unaffected; read-only forms have value=None by default

### NumberForm/RangeForm Validation Fix
- Silently clamping → structured error rejection for out-of-range and invalid step values
- Added server-side step validation to NumberForm

### Faithful Projection Fix
- Removed browser-side validation (min/max/step on number input, min/max on date input)
- Changed number input from type="number" to type="text" inputmode="decimal"
- Server is sole validation authority; humans and agents see the same errors

### PageForm Feedback Banner
- Transient `_feedback` on PageForm — one-shot, consumed after first serialize()
- Captures success/error for both page-level and nested eigenform actions
- Renders colored banner (green/red) between title and children in HTML
- Also in JSON response for agent visibility
- Fixes pre-existing bug: page-level POST errors were silently lost

### Store File Sync
- Store now checks file mtime on every access (get/set/delete/clear_scope)
- File deleted externally → in-memory cache cleared, page shows empty state
- File modified externally → cache reloaded from disk
- _save() records mtime to avoid re-reading own writes

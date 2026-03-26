# Session-2026-03-26-001

## Current State (last updated: late session)
- **Active document:** CR-110 (IN_EXECUTION v1.1)
- **Current EI:** Rebuild continuation
- **Blocking on:** Nothing
- **Next:** Awaiting direction from Lead

## Progress Log

### [Session Start] Initialization
- Read previous session notes (Session-2026-03-25-001)
- Read PROJECT_STATE.md
- Context: Clean-room rebuild of workflow engine on `dev/content-model-unification` branch
- 10 eigenform types built, 6 demo pages running
- Remaining: DisplayForm, flow control, workflow definitions, expression evaluator

### Per-page state isolation
- Changed Store from a singleton (`data/state.json`) to per-PageForm files (`data/{scope}.json`)
- `PageForm.bind()` now takes `data_dir: Path` instead of `store: Store`, creates its own Store
- All child eigenforms unchanged — they inherit the store from PageForm
- Removed global `store` from routes.py, replaced with `DATA_DIR = Path("data")`
- Deleted orphaned `data/state.json`
- Verified: cross-page isolation, page reset, import correctness

### Page definitions extracted to pages/ directory
- Created `pages/` directory with one file per page (`page_1.py` through `page_6.py`)
- Each file exports an unbound `definition` (a PageForm)
- `pages/__init__.py` auto-discovers `page_*.py` modules, binds them, returns dict
- `routes.py` reduced to pure routing — just `from pages import build_pages`
- Adding a new page = creating a new file, no registry to update

### Content negotiation
- Unified GET routes: same URL serves JSON (agents) or HTML (browsers) via Accept header
- Removed `/view` suffix — `GET /pages/page-1` serves both formats
- Updated index.html links

### Eigenform-level GET routes
- `GET /pages/{key}/{ef_key}` returns individual eigenform JSON or HTML
- Added `PageForm.find_eigenform(key)` — recursive lookup traversing all containers
- Useful for viewing eigenforms hidden by their parent (inactive tabs, non-current chain steps)

### PageForm URL cleanup
- Reset button now POSTs to `/pages/{key}` instead of `/pages/{key}/{key}` (was duplicating the page key)
- Page-level POST route added to handle page actions directly
- Removed self-referencing key check from `handle_action`

### URL scheme overhaul
- `/page/{id}` → `/pages/{key}` (plural, key-based)
- Page keys changed from `"1"` to `"page-1"` format
- `pages/__init__.py` derives key from filename: `page_1.py` → `page-1`
- Store files now `data/page-1.json`

### Path-based eigenform URLs
- URLs now mirror containment hierarchy: `/pages/page-2/tabs/title` instead of `/pages/page-2/title`
- Containers (TabForm, ChainForm) pass nested url_prefix to children during bind()
- Route changed to `<path:path>` catch-all
- PageForm.find_eigenform() walks path segments through hierarchy
- PageForm.handle_action() simplified — uses find_eigenform() + handle() directly

### Page registry: key from definition, not filename
- `pages/__init__.py` now discovers all .py files (not just page_*.py)
- Key comes from `definition.key`, filename is independent
- Created `math_test.py` with key `math-test` to demonstrate

### Math Test page (pages/math_test.py)
- Q1: TextForm (free text), Q2: ChoiceForm (radio), Q3: CheckboxForm (select all)
- Q4: TabForm scavenger hunt — 6 tabs with cross-referencing instructions
- Q5: ChainForm clue chain — each answer feeds the next

### ChainForm: Continue button
- Bug: jumping back to a completed step left you stuck (no way to resume)
- Fix: added "Continue" affordance when viewing a completed step with explicit focus
- Clears focus, lets auto-advance resume

### TabForm: label rendering
- TabForm.render_inner() was skipping label/instruction heading
- Fixed to render `<h3>` and instruction like other eigenforms

### Affordance render tracking
- Affordance.render() now sets `_rendered` flag, delegates to render_html()
- All affordance subclasses override render_html() instead of render()
- Eigenform.render() checks all affordances after render_inner() — raises RuntimeError if any missed
- ChainForm uses `if not aff._rendered` to catch remaining affordances instead of matching by body keys
- Verified: all 7 pages pass, and intentionally skipped affordances raise clear errors

### Upgraded Math Test page
- Copied math test, wrapped all questions in outer ChainForm
- Key: `upgraded-math-test`, one question visible at a time
- Added API usage guidance to page instruction

### Index page auto-generated
- index.html now uses Jinja template iterating `pages` list from route
- New pages appear automatically, no hardcoded links

### Render derives from serialize (critical architectural fix)
- Problem: serialize() and render() were independent code paths that could drift
- Fix: render() now calls serialize() first, then render_from_data(data) produces HTML purely from the dict
- All 10 eigenform types migrated from render_inner(affordances) to render_from_data(data)
- Affordances enriched with render_hints in serialize() for HTML rendering
- Standalone render_affordance_html(aff_dict) renders any affordance from its serialized dict
- All 11 affordance subclasses: render_html() replaced with _render_hints()
- _rendered flag and check removed — no longer needed since HTML derives from JSON
- Affordance is now a pure data/serialization class
- Verified: all 8 pages render, functional tests pass

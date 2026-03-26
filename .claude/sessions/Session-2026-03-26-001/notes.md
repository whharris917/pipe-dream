# Session-2026-03-26-001

## Current State (last updated: session start)
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

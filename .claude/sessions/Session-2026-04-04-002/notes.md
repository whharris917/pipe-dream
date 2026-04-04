# Session-2026-04-04-002

## Current State (last updated: 2026-04-04)
- **Active document:** CR-110 (IN_EXECUTION v1.1)
- **Current work:** Stateless server + instance spawning complete
- **Blocking on:** Nothing
- **Next:** Lead direction

## Progress Log

### Stateless server refactor
- **Decision**: Server must not hold eigenforms or pages in memory between requests. Python objects are transient — loaded and discarded per-request. Server becomes a pure function: (seed + store + request) → response.
- **`pages/__init__.py`**: `build_pages()` replaced with `discover_pages()` (returns unbound seed definitions) and `bind_page()` (transient per-request binding)
- **`app/routes.py`**: `seeds` dict holds inert definitions only. New `get_page()` binds on demand per request. SSE subscriber registry kept (connection state, not application state).
- **`tests/test_parity.py`**: Updated imports from `build_pages` to `discover_pages`/`bind_page`
- **Committed and pushed as `0bd7d87`**

### TextForm template fixes
- **Tooltips**: Added POST body tooltips to Set, Clear, and edit-mode buttons (matching NumberForm convention). Lost during HTMX round-trip.
- **Clear button line break**: Clear button now on its own line (in `<div>` block), not inline with Set button.

### Instance spawning architecture
- **Decision**: Page seeds become templates. Users spawn named instances of any seed type. Multiple instances of the same type can coexist.
- **`app/registry.py`**: New `InstanceRegistry` class (~85 lines). Wraps `data/instances.json`. Tracks instance ID, type, label, created_at. Sequential IDs per type (`{type}-{n}`). Mtime-based sync matching Store pattern.
- **`pages/__init__.py`**: `bind_page()` takes `instance_id` param, passes it as `scope` and in `url_prefix`. Decouples storage identity from seed identity.
- **`app/routes.py`**: Resolves instances via registry → seed → bind. New `POST /instances` (create) and `POST /instances/<id>/delete` (remove). Index route passes seeds + instances. Auto-migration: on startup, any `data/{seed_key}.json` not already registered gets adopted as an instance.
- **`app/templates/index.html`**: Launcher UI with seed catalog ("New Page" buttons) + instance list (links + delete buttons). Instance ID is the link text; label shown as secondary context.
- **`app/templates/page.html`**: `page_key` → `instance_id` in SSE/fetch JS.
- **Creating a page returns to the launcher** (not auto-navigate to the new page).
- **20/20 parity tests passing**

### Attempted but reverted: eigenforms → children rename
- Dataclass inheritance conflict: base `Eigenform` has `children` as a `@property` returning `[]`. Subclass dataclass fields can't override parent properties. Would need a more considered approach. Reverted cleanly.

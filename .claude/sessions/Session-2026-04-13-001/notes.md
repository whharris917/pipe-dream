# Session-2026-04-13-001

## Current State (last updated: 2026-04-13)
- **Active work:** UI shell port complete, committed
- **Branch:** dev/content-model-unification (qms-workflow-engine submodule)
- **Status:** All features working, ready for next steps
- **Blocking on:** Nothing
- **Next:** Lead direction — build real QMS workflows as eigenforms, or cleanup demo pages

## Progress Log

### Strategic discussion
- Lead recognized need to refocus from side quests back to main goal: building QMS for Flow State
- Reviewed main branch site to understand current state
- Decision: bring dev branch up to state-of-the-art rather than merging into main (avoids breaking main)
- Dropped: Template Editor, YAML workflows, Workshop pages, Sandbox
- Dev branch preserved until explicit instruction to delete

### Phase 1: Base Layout Template
- Created `app/templates/base.html` — dark sidebar nav with 7 items (Home, Agent Portal, QMS, Workspace, Inbox, Quality Manual, README)
- Refactored `app/templates/page.html` to extend base.html (toolbar, SSE, theme toggle preserved)
- Updated routes.py with active_page kwargs

### Phase 2: Agent Portal + Home Page
- Created `app/templates/portal.html` — card-grid layout grouping instances by seed type
- Created `app/templates/home.html` — landing page with hero + info cards
- Restructured routes: `/` = home, `/portal` = portal, redirects updated

### Phase 3: Quality Manual Viewer
- Created `app/manual.py` — extracted markdown helpers (TOC builder, link rewriter, renderer)
- Created `app/templates/manual_index.html` — 2x2 section grid
- Created `app/templates/manual_page.html` — left TOC sidebar + article content
- Added `/manual` and `/manual/<slug>` routes

### Phase 4: QMS Dashboard, Workspace, Inbox
- Created `app/templates/qms.html` — document table with stage badges
- Created `app/templates/workspace.html` — card-based document list
- Created `app/templates/inbox.html` — placeholder
- Added `/qms`, `/workspace`, `/inbox` routes with `_list_crs()` helper

### Phase 5: Polish + Verification
- All routes verified via Flask test client: 200 status, sidebar present, active nav highlighting
- Removed superseded `index.html`

### README as nav page
- Added `/readme` route rendering README.md as styled HTML
- Added README link to sidebar nav (bottom, with ⓘ icon)
- Rewrote README.md to match current state: 26 eigenform classes, 31 registered names, accurate module paths, site structure table, themes section, all route documentation

### Instance ID cleanup
- Replaced counter-based IDs (`page-1-2`) with 8-char UUID hex (`eeadc32c`) in InstanceRegistry
- Removed `_counters` usage from create_instance

### Debug Mode toggle
- Replaced Supervisor/Operator view toggle + theme selector with single "Debug Mode" checkbox
- Debug Off = operator-view + sleek theme (production look)
- Debug On = supervisor-view + default theme (full borders, chrome, JSON)
- Moved toggle to bottom-right of page (unobtrusive footer position)
- Default for new visitors: sleek theme (debug off)

### Demo page cleanup
- Deleted page definitions: page_1, page_2, page_3, page_4, page_6, math_test, survey_builder, vendor_assessment, weird_experiments, eigenform_reference, page_builder
- Cleaned up associated instance data files and registry entries
- Removed stale legacy-named instances (page-6-2)

### Stateless page discovery
- Made `discover_pages()` truly stateless: reloads modules on every call, purges stale sys.modules entries
- `seeds` in routes.py changed from module-level dict to per-request function call
- Adding/removing page .py files takes effect on next request — no server restart needed

### Sleek theme font fix
- Added `h3` (13px) and `p` (12px) sizing rules inside `.eigenform` for sleek theme
- Fixes large instruction text in data eigenform cards (was inheriting base.html's 1rem)

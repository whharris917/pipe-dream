# Session-2026-04-19-002

## Current State (last updated: all work committed)
- **Active document:** None
- **Current EI:** N/A
- **Blocking on:** Nothing
- **Next:** Browser-verify inspect panel features

## Progress Log

### Right-click inspect panel (full feature)
Built a Chrome DevTools-style component inspector, accessible via right-click context menu on any component. Establishes the general pattern: right-click actions are human-only chrome — no affordances, no parity tests, invisible to agents.

**Files changed:**
- `app/__init__.py` — `app.json.sort_keys = False` (canonical key order in JSON responses)
- `app/routes.py` — new `GET /pages/{id}/_store` route returning raw store JSON
- `app/templates/components/wrapper.html` — added `data-url="{{ url }}"` on outermost div
- `app/templates/components/sleek/wrapper.html` — added `data-url="{{ url }}"` on all 4 branch divs
- `app/static/component.js` — context menu, inspect panel, tree viewer, live refresh (IIFE, self-contained CSS)

**Context menu (3 items):**
- **Inspect** — full page JSON tree with right-clicked component expanded and highlighted (blue left border), path from root auto-expanded, scrolled into view
- **Affordances** — just the component's affordances array
- **Data** — raw store data for the component's scope (via `_store` endpoint)

**Tree viewer:**
- Recursive collapsible JSON tree (Chrome DevTools style)
- Syntax coloring: keys (#9cdcfe), strings (#ce9178), numbers (#b5cea8), booleans/null (#569cd6)
- Inline previews when collapsed, expand/collapse arrows per node
- Target matching via affordance URL propagation

**Panel features:**
- Right-side drawer (480px / 45vw default), resizable via drag handle on left edge (min 240px)
- Toolbar: Expand | Collapse | All Affs | Labels
- **All Affs**: all non-floatable affordances from page, grouped by component label
- **Labels**: indented component hierarchy with completion dots (filled/hollow)
- Close via Escape or × button

**Live refresh:**
- `_cSwap` fires `c-page-updated` CustomEvent after every DOM swap (covers user POSTs and SSE)
- Inspect panel re-fetches and re-renders current view on every page update
- Scroll position preserved across refreshes
- `inspectState` tracks active view type for correct re-render

**Tests:** 79/79 pass throughout

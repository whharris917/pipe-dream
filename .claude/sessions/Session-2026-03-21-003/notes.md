# Session-2026-03-21-003

## Current State (last updated: second commit ready)
- **Active document:** CR-110 (IN_EXECUTION v1.1)
- **Blocking on:** Nothing
- **Next:** Extend LNARF renderer pattern to more pages

## Progress Log

### Session Start
- Read previous session notes (Session-2026-03-21-002)
- Previous session: multi-instance workflows, unified renderer architecture, definition consolidation, agent view toggle

### LNARF Portal Renderer — Implemented
- **Design decision:** page-specific renderers, not a universal renderer
- Created `app/static/renderers/portal.js` — dedicated portal renderer
- Rewrote `app/templates/agent.html` — receives full canonical payload as JSON, loads renderer, JS builds all DOM
- Updated `app/app.py` `agent_portal()` — passes full `_render_portal()` dict to template
- Fixed DOMContentLoaded bug: toggle button outside `{% block content %}`, script inside it

### LNARF Audit + Fixes
- `state.page` changed from `"agent_portal"` to `"agent"` (matches URL path)
- Affordance labels: renderer uses short labels ("Open", "Delete", "+ New Instance") — representational freedom, not loss
- `/observe` URL invention fixed: content negotiation on `GET /agent/{wf_id}/{inst_id}`
- API meta line removed (invented semantic)
- Confirmation dialog removed from delete (parity violation)
- Delete affordance added to `_render_portal()`
- Renamed `/reset` endpoint to `/delete`
- POST `/new` creates only (no navigation), redirects to `/agent`
- Delete affordance now includes `body: {}`
- Affordance tooltips on hover show full request

### Observer + Renderer Simplification
- **Retired:** exp-a, exp-b, exp-c renderers (deleted files), dark theme, verbose mode
- **Simplified registry.js:** removed hierarchical format/verbosity/style system (~170 lines)
- **simple.js:** single `light` renderer remains (~300 lines of CSS removed)
- **_ALL_RENDERERS:** reduced from 8 entries to `["raw", "light"]`
- **Terminology:** Raw→Agent, Simple→Human. Toggle labels are "Human" and "Agent"
- **Observer page:** removed static black header bar, replaced with floating Human/Agent + Full/Feedback buttons
- **Observer extends base.html:** gains sidebar navigation, purple border delineates renderer territory
- **Full/Feedback:** collapsed from two buttons to a single toggle button
- **Layout:** purple bounding box pushed down 2.5rem to avoid overlapping floating controls

### Route changes
- `GET /agent/{wf_id}/{inst_id}` content-negotiates (JSON or HTML observer)
- `POST /agent/{wf_id}/new` redirects to `/agent` (not to instance)
- `POST /agent/{wf_id}/{inst_id}/delete` replaces `/reset`
- `/observe` route retained as backward-compat alias
- Observer route passes `active_page="agent"` for sidebar highlighting

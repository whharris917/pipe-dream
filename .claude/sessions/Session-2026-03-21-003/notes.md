# Session-2026-03-21-003

## Current State (last updated: commit ready)
- **Active document:** CR-110 (IN_EXECUTION v1.1)
- **Blocking on:** Nothing
- **Next:** Extend LNARF renderer pattern to workflow instance pages

## Progress Log

### Session Start
- Read previous session notes (Session-2026-03-21-002)
- Previous session: multi-instance workflows, unified renderer architecture, definition consolidation, agent view toggle

### LNARF Portal Renderer — Implemented
- **Design decision:** page-specific renderers, not a universal renderer. Each page type gets its own renderer that projects the GET payload. Shared conventions (`{state, instructions, affordances}` shape) provide coherence.
- Created `app/static/renderers/portal.js` — dedicated portal renderer
- Rewrote `app/templates/agent.html` — receives full canonical payload as JSON, loads renderer, JS builds all DOM
- Updated `app/app.py` `agent_portal()` — passes full `_render_portal()` dict to template
- **Raw toggle:** "Agent View" button renamed to "Raw" — toggles between rendered human view and raw JSON
- Purple border marks the renderer's territory (content inside = renderer's projection, outside = base template)
- Fixed DOMContentLoaded bug: toggle button is outside `{% block content %}`, script inside it — needed deferred binding

### LNARF Audit + Fixes
Performed full LNARF audit against the principle document. Findings and fixes:

**Losses fixed:**
- `state.page` — changed from `"agent_portal"` to `"agent"` (matches URL, browser address bar is the projection)
- Affordance labels/IDs — renderer now reads from affordance data, not hardcoded strings
  - Reverted to short button labels ("Open", "Delete", "+ New Instance") since surrounding card context carries the workflow/instance info — representational freedom, not loss

**Additions fixed:**
- `/observe` URL invention — renderer was appending `/observe` to affordance URLs. Fixed by adding content negotiation to `GET /agent/{wf_id}/{inst_id}` (JSON for agents, HTML observer for browsers). Same URL, same affordance, both participants.
- API meta line removed (engine didn't produce it)
- Confirmation dialog removed from delete (agent doesn't get one)

**Parity fixes:**
- Delete affordance added to `_render_portal()` (was missing entirely)
- Renamed `/reset` endpoint to `/delete`
- POST `/new` no longer navigates — just creates and returns to portal
- Delete affordance now includes `body: {}` like create affordance
- Affordance tooltips on hover show full request (`POST /agent/.../delete {}`)

### Route changes
- `GET /agent/{wf_id}/{inst_id}` now content-negotiates (JSON or HTML observer)
- `POST /agent/{wf_id}/new` redirects to `/agent` (not to instance)
- `POST /agent/{wf_id}/{inst_id}/delete` replaces `/reset`
- `/observe` route retained as backward-compat alias

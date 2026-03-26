# Session-2026-03-25-001

## Current State (last updated: mid-session, post TabForm)
- **Active document:** None (no CR for this work)
- **Current EI:** N/A
- **Blocking on:** Nothing
- **Next:** Continue clean-room rebuild — more eigenform types or flow control

## Progress Log

### Clean-room rebuild started
- Created dev branch `dev/content-model-unification` in qms-workflow-engine
- Deleted all existing code (engine/, app/, data/, docs/, README.md, run.py)
- Built minimal Flask skeleton: run.py, app/__init__.py, app/routes.py, app/templates/

### Terminology decisions
- **Eigenform** — coined from "eigen" (self) + "form" — the self-contained, self-rendering unit of workflow interaction
- **Forms** — the different types: TextForm, CheckboxForm, TabForm, PageForm, etc.
- The `form` property derives type name from class (TextForm → "text"), no stored type field
- Rejected alternatives: element, cell, valve, gizmo, hapt, prim, terminal

### Architecture established
- **Eigenform protocol**: serialize() → JSON, render() → HTML, handle(body) → mutation + JSON
- **Self-sufficiency via bind()**: eigenforms bound to store/scope/url_prefix, then need no external input
- **bind() returns a copy**: definitions are templates, bind() produces independent bound instances via deepcopy
- **Affordance as first-class object**: Affordance base class with serialize() and render() (NotImplementedError enforced)
- **Affordance body templates**: fillable templates with placeholders (`<value>`, `<true | false>`) + per-affordance instructions
- **Store**: JSON file on disk, scoped by page/eigenform key
- **SSE**: /page/{id}/stream pushes full page state on every POST, browser auto-refreshes
- **Base class render()**: provides border + "See JSON" toggle for free to all eigenforms
- **Purple "See JSON" buttons**: human-only controls exempt from faithful projection

### Eigenform types built
1. **TextForm** — single free-form string input, SetValueAffordance
2. **CheckboxForm** — multi-select with per-item checkboxes, single CheckboxAffordance renders as multiple checkboxes, omitted items unchanged on POST
3. **TabForm** — multiple tabs, only active tab visible in JSON and HTML (faithful projection), tab switching is a persisted affordance (SwitchTabAffordance), active tab shown as bold disabled button
4. **PageForm** — container that delegates to nested eigenforms, routes POSTs to children including through TabForm containers

### Affordance types built
1. **SetValueAffordance** — text input + submit button with live tooltip
2. **CheckboxAffordance** — individual checkboxes per item, no page reload
3. **SwitchTabAffordance** — tab button, disabled when active

### Principles audit (first pass)
- HATEOAS: pass — every eigenform carries affordances, POST returns full page state
- Lossless: pass — JSON contains everything the HTML shows
- Non-additive: pass — HTML doesn't add info beyond JSON (purple buttons explicitly exempt)
- Representationally free: pass — JSON doesn't dictate layout
- Faithful projection: pass — agent and human see same active tab content
- RESTful: pass — GET returns state, POST mutates and returns updated resource
- Agent friendly: pass — fillable body templates with instructions

### Bugs found and fixed
- Shared eigenform instances clobbered by bind() — fixed via deepcopy
- POST response was per-eigenform, not per-page — fixed to return full page state
- `"<value>"` placeholder convention — replaced with fillable body templates + instructions
- DOM ID collisions across pages — scoped uid by scope+key
- SwitchTabAffordance onclick broken by unescaped quotes in HTML attribute — fixed with &quot; escaping

### Commits
- `79971b4` — Clean-room rebuild: Eigenform architecture foundation
- `f033f2e` — CheckboxForm + SSE live updates + affordance body templates
- Pending: TabForm + routing through containers

### Files
- `engine/__init__.py` — empty
- `engine/eigenforms.py` — Eigenform base, TextForm, CheckboxForm
- `engine/affordances.py` — Affordance base, SetValueAffordance, SwitchTabAffordance, CheckboxAffordance
- `engine/store.py` — JSON file store
- `engine/page.py` — PageForm
- `engine/tab.py` — TabForm
- `app/__init__.py` — Flask app factory
- `app/routes.py` — routes with SSE streaming
- `app/templates/index.html` — portal landing page
- `app/templates/page.html` — minimal page shell with SSE client
- `run.py` — entry point

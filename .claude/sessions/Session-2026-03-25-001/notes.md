# Session-2026-03-25-001

## Current State (last updated: mid-session)
- **Active document:** None (no CR for this work)
- **Current EI:** N/A
- **Blocking on:** Nothing
- **Next:** Continue clean-room rebuild — add remaining eigenform types (BooleanForm, ChoiceForm, DisplayForm, MultiForm)

## Progress Log

### Clean-room rebuild started
- Created dev branch `dev/content-model-unification` in qms-workflow-engine
- Deleted all existing code (engine/, app/, data/, docs/, README.md, run.py)
- Built minimal Flask skeleton: run.py, app/__init__.py, app/routes.py, app/templates/

### Terminology decisions
- **Eigenform** — coined from "eigen" (self) + "form" — the self-contained, self-rendering unit of workflow interaction
- **Forms** — the different types: TextForm, BooleanForm, ChoiceForm, DisplayForm, MultiForm, TableForm, ListForm
- **PageForm** — an eigenform that contains and delegates to nested eigenforms
- Rejected alternatives: element, cell, valve, gizmo, hapt, prim, terminal
- The `form` property derives type name from class (TextForm → "text"), no stored type field

### Architecture established
- **Eigenform protocol**: serialize() → JSON, render() → HTML, handle(body) → mutation + JSON
- **Self-sufficiency via bind()**: eigenforms bound to store/scope/url_prefix, then need no external input
- **bind() returns a copy**: definitions are templates, bind() produces independent bound instances
- **Affordance as first-class object**: Affordance base class with serialize() and render() (NotImplementedError enforced)
- **SetValueAffordance**: renders text input + submit button with live tooltip showing endpoint + body
- **Store**: JSON file on disk, scoped by page/eigenform key
- **PageForm**: subclass of Eigenform, delegates rendering to children, POST returns full page state
- **Base class render()**: provides border + "See JSON" toggle for free to all eigenforms
- **Purple "See JSON" buttons**: human-only controls exempt from faithful projection

### Principles audit
- HATEOAS: pass — every eigenform carries affordances, POST returns full page state
- Lossless: pass — JSON contains everything the HTML shows
- Non-additive: pass — HTML doesn't add info beyond JSON (purple buttons explicitly exempt)
- Representationally free: pass — JSON doesn't dictate layout
- Faithful projection: pass — every JSON field visible in HTML, affordances render as interactive controls
- RESTful: pass — GET returns state, POST mutates and returns updated resource
- Agent friendly: pass — agent discovers all actions from GET response

### Bugs found and fixed
- Shared eigenform instances clobbered by bind() — fixed via deepcopy
- POST response was per-eigenform, not per-page — fixed to return full page state
- `"<value>"` placeholder convention — replaced with explicit `parameters` dict with types
- DOM ID collisions across pages — scoped uid by scope+key

### Files created
- `engine/__init__.py` — empty
- `engine/eigenforms.py` — Eigenform base, TextForm
- `engine/affordances.py` — Affordance base, SetValueAffordance
- `engine/store.py` — JSON file store
- `engine/page.py` — PageForm
- `app/__init__.py` — Flask app factory
- `app/routes.py` — routes (3 page definitions with TextForms)
- `app/templates/index.html` — portal landing page
- `app/templates/page.html` — minimal page shell
- `run.py` — entry point

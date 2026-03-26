# Session-2026-03-25-001

## Current State (last updated: end of session)
- **Active document:** None (no CR for this work)
- **Current EI:** N/A
- **Blocking on:** Nothing
- **Next:** Continue rebuild — workflow definitions, flow control (proceed/navigation), expression evaluator

## Progress Log

### Clean-room rebuild started
- Created dev branch `dev/content-model-unification` in qms-workflow-engine
- Deleted all existing code
- Built minimal Flask skeleton

### Terminology decisions
- **Eigenform** — coined from "eigen" (self) + "form" — the self-contained, self-rendering unit of workflow interaction
- **Forms** — the different types: TextForm, CheckboxForm, TabForm, ChainForm, PageForm, RubiksCubeForm
- The `form` property derives type name from class (TextForm → "text"), no stored type field

### Architecture established
- **Eigenform protocol**: serialize() → JSON, render() → HTML, handle(body) → mutation
- **Self-sufficiency via bind()**: eigenforms bound to store/scope/url_prefix, then need no external input
- **bind() returns a copy**: definitions are templates, bind() produces independent instances via deepcopy
- **Affordance as first-class object**: Affordance base class with serialize() and render() (NotImplementedError enforced)
- **Affordance body templates**: fillable templates with placeholders (`<value>`, `<true | false>`) + per-affordance instructions
- **Store**: JSON file on disk, scoped by page/eigenform key, with clear_scope for reset
- **SSE**: /page/{id}/stream pushes full page state on POST (threading issues with Flask dev server noted)
- **Base class render()**: provides border + "See JSON" toggle for all eigenforms, green border when complete, gray when incomplete
- **Purple "See JSON" buttons**: human-only controls exempt from faithful projection
- **is_complete**: required property on all eigenforms (NotImplementedError if not implemented)
- **Conditional affordances**: affordance lists change based on state (Rubik's cube: solved → only Shuffle; CheckboxForm: N/A mode → only Clear N/A)

### Eigenform types built
1. **TextForm** — single free-form string input. Complete when value is not None.
2. **CheckboxForm** — multi-select with per-item checkboxes. Complete when any item checked or N/A selected. N/A is a separate button that clears all items; "Clear N/A" button to return to normal mode.
3. **TabForm** — tabbed container. Only active tab visible in JSON and HTML. Tab switching is a persisted affordance. Complete when all tabs complete.
4. **ChainForm** — sequential wizard. Shows first incomplete step. Completed steps appear as "jump back" affordances. Auto-advances after value change. Progress bar shows completed/active/future steps. Complete when all steps complete.
5. **PageForm** — top-level container. Delegates to nested eigenforms. Routes POSTs through containers. "Reset Page" affordance clears all state recursively. Complete when all children complete.
6. **RubiksCubeForm** — fully functional Rubik's Cube. Demonstrates arbitrary eigenform complexity. Conditional affordances: solved state shows only Shuffle; unsolved shows 12 rotation buttons + Shuffle + Restart. Complete when solved.

### Affordance types built
1. **SetValueAffordance** — text input + submit button with live tooltip
2. **CheckboxAffordance** — individual checkboxes per item, reload after POST
3. **SwitchTabAffordance** — tab/chain navigation button
4. **SimpleButtonAffordance** — fixed-body button with reload (N/A, Shuffle, Restart, Reset)
5. **RotateAffordance** — compact rotation button for Rubik's Cube

### Key design decisions
- **Faithful projection enforced**: TabForm and ChainForm hide non-visible eigenforms from both JSON and HTML
- **Completeness is eigenform-defined**: each type knows its own completion criteria, no external confirm mechanism needed
- **N/A as separate mode**: CheckboxForm switches between checkbox mode and N/A mode, changing available affordances
- **SimpleButtonAffordance moved to affordances.py**: shared across RubiksCubeForm, CheckboxForm, PageForm
- **PageForm reset clears recursively**: walks eigenforms/steps/tabs to clear all nested scopes
- **Flask threaded=True**: required for SSE to work alongside POST handlers

### Bugs found and fixed
- Shared eigenform instances clobbered by bind() — fixed via deepcopy
- POST response was per-eigenform, not per-page — fixed to return full page state
- DOM ID collisions across pages — scoped uid by scope+key
- SwitchTabAffordance onclick broken by unescaped quotes — fixed with &quot; escaping
- N/A mutual exclusion logic checked stale state — fixed by tracking na_was/na_now (then replaced with separate N/A mode)
- Flask single-threaded blocked SSE — fixed with threaded=True
- Stale store data from schema changes — cleared state.json

### Commits
- `79971b4` — Clean-room rebuild: Eigenform architecture foundation
- `f033f2e` — CheckboxForm + SSE live updates + affordance body templates
- `794341e` — TabForm: tabbed container with faithful projection
- Pending: RubiksCubeForm, ChainForm, is_complete, conditional affordances, N/A mode, PageForm reset

### Files
- `engine/__init__.py` — empty
- `engine/eigenforms.py` — Eigenform base, TextForm, CheckboxForm
- `engine/affordances.py` — Affordance base, SetValueAffordance, SwitchTabAffordance, SimpleButtonAffordance, CheckboxAffordance
- `engine/store.py` — JSON file store with clear_scope
- `engine/page.py` — PageForm with reset and recursive clear
- `engine/tab.py` — TabForm
- `engine/chain.py` — ChainForm
- `engine/rubiks.py` — RubiksCubeForm with RotateAffordance
- `app/__init__.py` — Flask app factory
- `app/routes.py` — routes with SSE streaming, 4 demo pages
- `app/templates/index.html` — portal landing page
- `app/templates/page.html` — minimal page shell with SSE client
- `run.py` — entry point (threaded=True)

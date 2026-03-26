# Session-2026-03-25-001

## Current State (last updated: end of session)
- **Active document:** None (no CR for this work)
- **Current EI:** N/A
- **Blocking on:** Nothing
- **Next:** Continue rebuild — workflow definitions, flow control, expression evaluator, or TableForm iteration

## Progress Log

### Clean-room rebuild started
- Created dev branch `dev/content-model-unification` in qms-workflow-engine
- Deleted all existing code, built minimal Flask skeleton

### Terminology decisions
- **Eigenform** — coined from "eigen" (self) + "form"
- **Forms** — TextForm, CheckboxForm, TabForm, ChainForm, PageForm, RubiksCubeForm, TableForm
- The `form` property derives type name from class (TextForm → "text")

### Architecture established
- **Eigenform protocol**: serialize() → JSON, render() → HTML, handle(body) → mutation
- **Self-sufficiency via bind()**: bound to store/scope/url_prefix, zero-argument methods
- **bind() returns a copy**: definitions are templates, deepcopy produces independent instances
- **Affordance as first-class object**: serialize() + render() (NotImplementedError enforced)
- **Affordance body templates**: fillable placeholders + per-affordance instructions
- **Store**: JSON file on disk, scoped by page/key, clear_scope for reset
- **SSE**: /page/{id}/stream pushes on POST
- **Base class render()**: border (green=complete, gray=incomplete) + "See JSON" toggle
- **Purple "See JSON" buttons**: human-only, exempt from faithful projection
- **is_complete**: required property on all eigenforms (NotImplementedError)
- **Conditional affordances**: affordance lists change based on state
- **Error responses**: structured errors with message + failed_action

### Eigenform types built (7)
1. **TextForm** — string input. Complete when value not None.
2. **CheckboxForm** — multi-select + N/A mode. Complete when any item checked or N/A.
3. **TabForm** — tabbed container. Only active tab in JSON/HTML. Complete when all tabs complete.
4. **ChainForm** — sequential wizard. Auto-advances. Complete when all steps complete.
5. **PageForm** — top-level container. Reset Page affordance (recursive clear). Complete when all children complete.
6. **RubiksCubeForm** — full Rubik's Cube. Conditional affordances (solved/unsolved).
7. **TableForm** — dynamic columns + rows with stable IDs. Two agent review iterations.

### TableForm agent review iterations
- **Agent review 1**: Identified 8 issues. Critical: cell-at-a-time population too expensive, placeholder types ambiguous, column key vs label split, missing affordances, no error contract, positional row indices fragile.
- **Implemented**: add_row with initial values, set_row, stable row IDs (row_0, row_1...), rename_column, error responses with valid alternatives, dual key/label column addressing.
- **Agent review 2**: All fixes validated. Remaining: pluralization bug, add_row template ambiguity, no clear_cell semantics, complete field undocumented, error should echo failed action, placeholder notation inconsistent.
- **Implemented**: pluralization fix, simplified add_row template, failed_action in errors.
- **Deferred**: reorder rows/columns, batch endpoint, placeholder standardization, null/empty semantics docs.

### Affordance types built (6)
1. **SetValueAffordance** — text input + submit with live tooltip
2. **CheckboxAffordance** — individual checkboxes, reload after POST
3. **SwitchTabAffordance** — tab/chain navigation button
4. **SimpleButtonAffordance** — fixed-body button with reload
5. **RotateAffordance** — compact rotation button (Rubik's Cube)
6. **AddColumnAffordance** — text input + button for column creation
7. **SetCellAffordance** — inline cell editing (rendered by TableForm, not standalone)

### Commits
- `79971b4` — Clean-room rebuild: Eigenform architecture foundation
- `f033f2e` — CheckboxForm + SSE live updates + affordance body templates
- `794341e` — TabForm: tabbed container with faithful projection
- `2eae6c8` — ChainForm, RubiksCubeForm, is_complete, conditional affordances, PageForm reset
- Pending: TableForm + agent review improvements

### Files
- `engine/__init__.py`, `engine/eigenforms.py`, `engine/affordances.py`, `engine/store.py`
- `engine/page.py`, `engine/tab.py`, `engine/chain.py`, `engine/rubiks.py`, `engine/table.py`
- `app/__init__.py`, `app/routes.py`, `app/templates/index.html`, `app/templates/page.html`
- `run.py`

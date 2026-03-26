# Session-2026-03-25-001

## Current State (last updated: end of session)
- **Active document:** None (no CR for this work)
- **Current EI:** N/A
- **Blocking on:** Nothing
- **Next:** Continue rebuild — DisplayForm, ConfirmForm, flow control, workflow definitions, expression evaluator

## Progress Log

### Clean-room rebuild
- Created dev branch `dev/content-model-unification` in qms-workflow-engine
- Deleted all existing code, built from scratch

### Terminology
- **Eigenform** — from "eigen" (self) — self-contained, self-rendering unit
- **Forms**: TextForm, CheckboxForm, TabForm, ChainForm, PageForm, RubiksCubeForm, TableForm, ChoiceForm, ListForm, MultiForm

### Architecture
- Eigenform protocol: serialize() → JSON, render() → HTML, handle(body) → mutation
- Self-sufficiency via bind(): bound to store/scope/url_prefix, zero-argument methods
- bind() returns deepcopy: definitions are templates, instances are independent
- Affordances: first-class objects with serialize() + render() (NotImplementedError enforced)
- Body templates: fillable placeholders + per-affordance instructions
- Store: JSON file, scoped by page/key, clear_scope for reset
- SSE: /page/{id}/stream pushes on POST
- is_complete: required on all eigenforms, green/gray border
- Conditional affordances: lists change based on state
- Structured errors: message + failed_action + valid alternatives

### Eigenform types (10)
1. **TextForm** — string input. Complete when value not None.
2. **CheckboxForm** — multi-select + N/A mode. Complete when any checked or N/A.
3. **ChoiceForm** — single selection via radio buttons. Complete when valid option selected.
4. **MultiForm** — groups FieldDescriptors under single affordance. Complete when all fields filled. Reduces agent round-trips.
5. **ListForm** — ordered list with add/edit/remove/reorder + N/A. Inline up/down arrows and remove buttons. Complete when items > 0 or N/A.
6. **TabForm** — tabbed container. Only active tab in JSON/HTML. Complete when all tabs complete.
7. **ChainForm** — sequential wizard. Auto-advances. Complete when all steps complete.
8. **PageForm** — top-level container. Reset Page (recursive clear). Complete when all children complete.
9. **RubiksCubeForm** — full Rubik's Cube. Conditional affordances (solved/unsolved).
10. **TableForm** — dynamic table with stable row IDs. Agent-reviewed (2 iterations).

### TableForm agent reviews
- Review 1: 8 issues. Critical: efficiency, placeholder ambiguity, missing affordances.
- Implemented: add_row with values, set_row, stable row IDs, rename_column, dual key/label, error responses.
- Review 2: 8 remaining items. Implemented: pluralization, simplified add_row template, failed_action in errors.

### Affordance types (8)
1. SetValueAffordance — text input + submit with live tooltip
2. CheckboxAffordance — individual checkboxes with reload
3. SwitchTabAffordance — tab/chain navigation button
4. SimpleButtonAffordance — fixed-body button with reload
5. RotateAffordance — compact rotation button (Rubik's Cube)
6. AddColumnAffordance — text input + button for columns
7. SetCellAffordance — inline cell editing (rendered by TableForm)
8. SelectAffordance — radio buttons for ChoiceForm
9. AddItemAffordance — text input + button for ListForm items
10. SetFieldsAffordance — multi-field form for MultiForm

### Demo pages (6)
1. TextForm + TextForm + CheckboxForm
2. TabForm with 3 tabs
3. RubiksCubeForm
4. ChainForm wizard (4 steps)
5. TableForm (dynamic columns/rows)
6. MultiForm + ChoiceForm + CheckboxForm + 2x ListForm (change request form)

### Commits
- `79971b4` — Eigenform architecture foundation
- `f033f2e` — CheckboxForm + SSE + affordance body templates
- `794341e` — TabForm with faithful projection
- `2eae6c8` — ChainForm, RubiksCubeForm, is_complete, conditional affordances, PageForm reset
- `1199338` — TableForm with stable row IDs, agent-reviewed API
- Pending: ChoiceForm, ListForm, MultiForm, Page 6

### Files
- engine/: eigenforms.py, affordances.py, store.py, page.py, tab.py, chain.py, rubiks.py, table.py, choice.py, listform.py, multi.py
- app/: __init__.py, routes.py, templates/index.html, templates/page.html
- run.py

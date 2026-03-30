# Session-2026-03-29-004

## Current State (last updated: end of session)
- **Active document:** CR-110 (IN_EXECUTION v1.1)
- **Current work:** Complete — typed columns, SequenceForm, edit mode, TableRunner, Workflow Builder
- **Blocking on:** Nothing
- **Next:** Extend edit mode to more eigenform types, explore Runner category further

## Progress Log

### SequenceForm (new eigenform type)
- Gated sequential container — like ChainForm but without auto-advance
- Steps unlock progressively (step N+1 accessible when step N complete)
- Manual navigation via Back/Next buttons + jump to completed steps
- Locked steps show lock icon in progress bar
- Registered as type "sequence" (31 types total)
- Added to Eigenform Gallery Container Forms tab

### Edit Mode Infrastructure (base Eigenform)
- `editable: bool = False` on base Eigenform class
- Pencil icon in chrome toggles edit/execution mode (dashed border when editing)
- Label overrides stored in store (`{key}.__label`), effective_label property
- `_get_edit_affordances()` extensible by subclasses
- `_chrome_rendered` flag prevents duplicate rendering of toggle affordance
- TextForm: edit mode shows inline label editor (ListForm-style input + green checkmark)
- Gallery: TextForm demo set to `editable=True`

### TableRunner (new eigenform type — Runner category)
- Reads a sibling TableForm and presents its rows as a gated sequence
- Row ordering constraints become execution gates
- Typed cell eigenforms rendered large, one row at a time
- Text cells rendered as labeled inputs
- Navigation: Back/Next + jump to completed accessible rows
- Locked rows show lock icon; prerequisite enforcement via constraint DAG
- Registered as type "tablerunner" (32 types total)
- Added to Eigenform Gallery Tables tab with dedicated source table

### Workflow Builder Page
- New page at /pages/workflow-builder (17 pages total)
- 6-tab builder: Overview, Stages, Gates, Paths, Acceptance, Review
- Stages tab showcases typed columns (ChoiceForm + BooleanForm cells)
- Gates tab uses RepeaterForm with rich templates
- Paths tab uses AccordionForm with 3 TableForms (parallel, conditional, merge)
- 14 eigenform types composed

### TableForm fixed_rows Cell Seeding
- `fixed_rows` now seeds cell data on first access (previously only seeded row metadata)
- Writes column state + row state + cells to store atomically
- Used in gallery demo: Runner Source Table pre-populated with Design/Build/Test stages

### Edit/Execution Mode Distinction (architectural insight)
- TableForm currently behaves as if always in edit mode (structural + data ops)
- Execution mode = structure frozen, only cell eigenforms are interactive
- Text columns are authoring-only (provide labels); typed columns are executable
- Row ordering constraints become execution gates in the runner

### TableRunner (new eigenform type — Runner category)
- Reads a sibling TableForm and presents its rows as a gated sequential workflow
- Only typed columns appear as interactive eigenforms; text columns provide row labels
- Row ordering constraints enforced as execution gates (prerequisite rows must complete)
- Cell eigenform URLs routed through the runner (distinct from table's inline cells)
- Both share the same store scopes — data is consistent across table and runner
- Radio button name collision fixed by distinct URL prefixes
- Registered as type "tablerunner"
- Gallery demo: Runner Source Table (Design → Build → Test) + TableRunner executing it

### Commits
- Pending: all session work

### ListForm Constraint UI Update
- Replaced plain `<select>` dropdown with TableForm's checkbox-symbol button overlay style
- Replaced flat gray prerequisite spans with monospace rounded pill badges
- Removed "after" label prefix
- Added per-option POST body tooltips

### Typed Columns for TableForm — Complete Implementation

**Architecture** (follows RepeaterForm compound scope pattern):
- `fixed_columns` now accepts `list[str | Eigenform]` — string entries remain text columns, Eigenform entries become typed columns
- Cell eigenforms use compound scopes: `{table_key}/{row_id}`, key = `{col_id}`
- RowGroup class (like EntryGroup) enables path-based routing: `table_key -> row_id -> col_id`
- Cell eigenform URLs are fully addressable: `/pages/{page}/{table}/{row_id}/{col_id}`

**New/modified in `engine/tableform.py`:**
- `RowGroup` class — lightweight routing node with `cell_eigenforms: dict[str, Eigenform]`
- `_typed_column_templates` property — maps col_id to unbound eigenform template
- `_fixed_col_labels` property — extracts string labels from mixed fixed_columns
- `_bind_children` — creates RowGroups with bound cell eigenforms for all rows x typed columns
- `_rebuild_rows` — refreshes row groups after structural mutations
- `_clear_data` — clears compound scopes for all rows, then rebuilds
- `_handle`: add_row/remove_row call `_rebuild_rows()`, set_cell guards typed columns, set_row skips typed columns
- `get_affordances` — excludes typed columns from set_cell/set_row/add_row body templates
- `_serialize_state` — typed columns include cell eigenform's `serialize()` output; columns marked with `typed: true, form: type_name`
- `is_complete` — checks typed cell eigenforms via `.is_complete`
- `render_from_data` — typed cells render eigenform inline in `<td>` instead of text input

**Gallery demo** in `pages/eigenform_gallery.py`:
- "Typed Columns" table added to Tables tab
- 4 fixed columns: Task Name (text), Status (ChoiceForm), Priority (ChoiceForm), Approved (BooleanForm)

**Verified:**
- All 16 pages load and render without errors (backward compatible)
- Cell routing via `find_eigenform` works
- Cell actions via `handle_action` persist correctly
- Typed columns render as radio buttons / toggle buttons in HTML
- set_cell on typed column returns structured error with guidance
- Clear wipes compound scopes and rebuilds correctly
- Flask app serves correct HTML with interactive cell eigenforms

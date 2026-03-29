# Session-2026-03-29-004

## Current State (last updated: in progress)
- **Active document:** CR-110 (IN_EXECUTION v1.1)
- **Current work:** Typed columns for TableForm + ListForm constraint UI
- **Blocking on:** Nothing
- **Next:** Verify in browser, potential UI polish

## Progress Log

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

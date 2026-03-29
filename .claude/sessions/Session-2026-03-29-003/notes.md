# Session-2026-03-29-003

## Current State (last updated: end of session)
- **Active document:** CR-110 (IN_EXECUTION v1.1)
- **Current EI:** Pending — CR-110 EI updates still needed
- **Blocking on:** Nothing
- **Next:** CR-110 remaining EIs, SDLC-WFE-RS rewrite

## Progress Log

### TableForm UI Overhaul

**Alignment fixes (affordances.py):**
- Added `box-sizing: content-box` to STYLE_CONFIRM, STYLE_REMOVE, STYLE_ARROW — fixes button/gap size mismatch causing misaligned arrows, remove buttons, and constraint controls across rows in both TableForm and ListForm

**Add row affordance body (tableform.py):**
- `+ Row` affordance body now includes column key placeholders (e.g., `col_0: "<Name>"`) so agents see the fillable template matching the instruction text

**Column header redesign:**
- Pill badge IDs (matching ListForm id_style) centered between left/right move arrows using 3-column grid (`1fr auto 1fr`)
- Remove button moved to left of column name on label row
- Editable headers: visible border input + green ✓ confirm button, `font-family: inherit; font-size: inherit` to match fixed headers
- Fixed headers: gap placeholders for consistent width across fixed/editable columns
- All `<th>` cells use `vertical-align: top` for consistent arrow alignment

**Row controls redesign:**
- Remove buttons in dedicated bordered column at far left
- Up/down arrows in their own columns between remove and +prereq
- All control cells shaded `#f0f0f0` matching header row
- Row IDs rendered as pill badges (matching ListForm)
- +Row button moved to remove column, styled as green STYLE_CONFIRM button
- Final (+Row) row fully shaded

**Prerequisite UI redesign:**
- `+ Prerequisite` dropdown split into two columns: ☑ button column (custom button-styled select overlay) and "Prerequisites" column (only appears when any row has prereqs)
- Prerequisite pills use ID pill style (monospace, rounded, gray background)
- Prerequisites listed vertically, "after" label removed
- `_render_constraint_inline` refactored into `_render_constraint_dropdown` + `_render_constraint_pills`
- Dropdown option text: shows just ID when value is empty (no redundant `row_0 (row_0)`)
- ☑ button: `font-weight: normal` to prevent bold inheritance from `<th>`

**Table layout:**
- Horizontal scroll via `overflow-x: auto` wrapper + `width: max-content`
- Uniform font sizes: removed per-element font-size overrides from constraint UI
- Flex `gap: 4px` on row controls and column label rows

**Add-column cell:**
- Text field + green "+" button at bottom, aligned with other column labels via spacer divs

**Auto-seed row:**
- Tables with `fixed_columns` seed one empty row on first access
- Tables without fixed columns seed one row when first column is added

**Constraint visibility:**
- `show_row_constraints` threshold changed from `num_rows > 1` to `num_rows > 0`

### Configuration Panel + Auto-Chain
- Configuration panel renders above table when `allow_row_constraints` or `allow_col_constraints` is enabled
- Checkbox toggles for "Auto-chain rows" and "Auto-chain columns"
- `toggle_auto_chain_rows` / `toggle_auto_chain_cols` actions: flip config flag in state, rebuild or clear constraints
- `_apply_auto_chain(state, key, config)` — generic method for both axes: rebuilds constraints as sequential chain
- Auto-chain applied after add/remove/move on the respective axis
- Config stored in `state["config"]` dict alongside columns/rows_meta/cells
- Agent affordance: "Toggle Auto-Chain Rows/Columns" with current state in instruction

### Additional Polish
- Prerequisite dropdown: ☑ button-styled select overlay (18px font, font-weight: normal)
- Per-option tooltips with exact POST body
- Column constraint inline layout: vertical (dropdown on top, pills below)
- Constraint row: `display: flex` to eliminate descender gap
- Column header input `size="12"` for balanced width
- Prerequisite pills use ID badge style (monospace, rounded)
- `_render_constraint_dropdown` redundant label fix (row_0 not row_0 (row_0))
- Full-Featured Table demo populated with 5-row project plan + sequential constraints + column constraint

### Commits
- `74913db` — Fix button/gap alignment, add column placeholders to add_row affordance
- `ccd6310` — Redesign TableForm column headers and row controls
- `140133b` — TableForm layout overhaul: remove column, scrolling, uniform fonts, auto-seed row
- `00d30c7` — Prerequisite UI redesign, control columns, shading, polish
- Final commit pending — config panel, auto-chain, additional polish

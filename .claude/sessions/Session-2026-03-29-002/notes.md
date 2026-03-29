# Session-2026-03-29-002

## Current State (last updated: end of session)
- **Active document:** CR-110 (IN_EXECUTION v1.1)
- **Current EI:** Pending — CR-110 EI updates still needed
- **Blocking on:** Nothing
- **Next:** CR-110 remaining EIs, SDLC-WFE-RS rewrite

## Progress Log

### OrderedCollection Extraction
- Created `engine/ordered_collection.py` — plain dataclass (not an eigenform) that manages:
  - Items with stable IDs, values, and fixed flag
  - Monotonic ID counter
  - Static and dynamic must_follow ordering constraints
  - Cycle detection (DFS) and topological sort enforcement
  - Constraint-aware move up/down
  - Mutation methods that raise ValueError on failure, return new state dict
- 230 lines of reusable ordering logic extracted from ListForm

### ListForm Refactor
- Delegated all ordering logic to `OrderedCollection(id_prefix="item")`
- Handler branches became thin try/except wrappers around OC mutations
- Zero API change — serialize, affordances, handle all identical
- Removed duplicated `AddConstraintAffordance` (now in affordances.py)

### AddConstraintAffordance Moved
- Moved from `listform.py` to `affordances.py` for shared use by ListForm and TableForm

### TableForm Refactor
- Wraps two `OrderedCollection` instances: `_col_collection` and `_row_collection`
- New internal state format: `{columns: {OC state}, rows_meta: {OC state}, cells: {...}}`
- Legacy format auto-detected and migrated on first read
- New capabilities gained for free:
  - `move_row_up` / `move_row_down` — inline arrow buttons in row ID cell
  - `move_col_left` / `move_col_right` — inline arrow buttons in column headers
  - `fixed_columns` / `fixed_rows` — immutable seed items
  - `row_must_follow` / `col_must_follow` — static ordering constraints on either axis
  - `allow_row_constraints` / `allow_col_constraints` — dynamic constraint affordances (off by default)
- Serialization output unchanged (columns as key/label, rows with _id)
- All existing handle actions preserved

### Verification
- All 16 pages render cleanly in both JSON and HTML
- Legacy migration tested with simulated old-format data
- ListForm constraint behavior (static, dynamic, cycle detection) verified
- TableForm move/add/remove verified on fresh tables

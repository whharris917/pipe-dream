# Session-2026-03-29-001

## Current State (last updated: end of session)
- **Active document:** CR-110 (IN_EXECUTION v1.1)
- **Current EI:** Pending — CR-110 EI updates still needed
- **Blocking on:** Nothing
- **Next:** CR-110 remaining EIs, SDLC-WFE-RS rewrite

## Progress Log

### Inheritance Analysis
- Analyzed whether deeper eigenform inheritance hierarchy would reduce redundancy
- Identified 6 patterns of duplication (~1,180 lines) but concluded most are incidental similarity
- Recommended helpers over hierarchy; Lead agreed to defer refactoring

### Module Reorganization
- Extracted TextForm → textform.py, CheckboxForm → checkboxform.py from eigenforms.py
- Renamed eigenforms.py → eigenform.py (base class only, singular)
- Renamed all 25 eigenform modules to consistent `*form.py` convention
- Updated all imports across engine/, pages/, registry.py, README.md
- Fixed dynamicchoiceform.py content loss from sed (restored from git)
- Fixed missing `from html import escape` in eigenform.py after extraction

### Agent-Facing JSON Cleanup
- Introduced two-tier serialization: `_serialize_full()` (internal, for HTML) and `serialize()` (agent-facing, clean)
- Stripped `form`, `key` from agent JSON — agent doesn't need type hints if eigenforms are self-describing
- Stripped `render_hints` from affordances in agent JSON — HTML-only rendering data
- Stripped `_rendered` from "See JSON" button view — internal bookkeeping
- Updated 7 container overrides (Page, Tab, Chain, Accordion, Group, Switch, Visibility) to override `_serialize_full()` instead of `serialize()`
- All 16 pages render and serialize cleanly

### NumberForm Integer Mode in Affordance
- Added "integer only" to NumberForm affordance instruction when integer=True

### ListForm Fixed Items
- `fixed_items` parameter seeds immutable items (can't edit/remove, can reorder)
- Lazy seeding: items property generates defaults, first mutation persists
- HTML: fixed items render as plain text with matching box model + placeholder gaps
- Gallery: fixed-list-demo added

### Button Alignment (ListForm + RankForm)
- Invisible 24x24 placeholders keep button columns aligned across all items
- RankForm: move buttons rendered left of labels (eliminates variable-width issue)

### ListForm Ordering Constraints
- `must_follow` parameter for static constraints at definition time
- Dynamic constraints via "Add Constraint" affordance (dropdown picker UI)
- "Remove Constraint" inline buttons for dynamic constraints; built-in show "(built-in)"
- Stable topological sort enforcement: adding a constraint cascades reordering
- Transitive cycle detection prevents A→B→C→A
- Constraints serialized in agent-facing JSON
- Removing an item cleans up all dynamic constraints referencing it
- `allow_constraints=False` suppresses Add Constraint affordance and rejects handler
- `allow_constraints=False` suppresses Add Constraint affordance and rejects handler
- Gallery: dedicated "Lists" tab (9 tabs total) with 4 use cases: basic, fixed seeds, static constraints, dynamic constraints

### ID-Based Constraints
- Constraints keyed by item ID instead of value (survives renames)
- Inline constraint UI: per-item add dropdown + prerequisite pills with remove buttons
- Separate constraints section removed; all constraint management is inline
- Transitive cycle detection and stable topological sort enforcement

### ListForm Layout Polish
- Remove button moved to leftmost position
- Item ID labels rendered as monospace pill badges
- Move arrows left of content (matching RankForm pattern)
- "New item" row aligned with invisible pill spacer
- Inline constraint dropdown fixed-width, label "+ Prerequisite"
- All elements use consistent font sizing

### SetForm (eigenform #30)
- Unordered collection of unique string items
- Add/remove by value, duplicates rejected
- Items rendered as vertical pills with [x] remove on left
- Registered in registry, added to Collections tab in gallery

### KeyValueForm Improvements
- API simplified: edit/remove by key instead of internal ID
- Internal IDs stripped from agent-facing JSON
- Key rename via optional `new_key` field in edit action
- Remove button moved to left; header and add row aligned with spacer

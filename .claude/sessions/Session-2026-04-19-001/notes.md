# Session-2026-04-19-001

## Current State (last updated: all work committed)
- **Active document:** None
- **Current EI:** N/A
- **Blocking on:** Nothing
- **Next:** Browser-verify sleek vertical sidebar, consider further workshop or engine work

## Progress Log

### Workshop restructuring
- Restructured `/workshop` from a single page to a hub with sub-pages
- Renamed `workshop.html` → `workshop_page_builder.html` (existing page builder)
- Created `workshop.html` as index page with card grid listing all workshops
- Created `workshop_component_creation.html` stub for future Interactive Component Creation workshop
- Routes: `/workshop` (index), `/workshop/<slug>` (individual), `_WORKSHOPS` registry in routes.py
- Sidebar link unchanged, points to hub

### Workshop page builder improvements
- Added `instruction` field to component model (Identity section in properties panel, rendered as italic gray text on cards, included in JSON export)
- Eliminated UI jumpiness: properties panel input events no longer trigger `renderCanvas()` — data model updates live, canvas syncs on focusout only. Label/instruction patch the card DOM inline.
- Removed card entrance animation (`ws-card-in`) and button press scale transforms that caused bounciness on mock interactions
- Fixed Navigation tab switching in workshop: `containerBody()` now shows only the active tab's child (faithful projection), with "Drop a child into this tab" empty state

### Learning Portal
- Added "Miscellaneous Topics" section below Deep Dives on learn index
- Created first topic: "Anatomy of a Component" (`/learn/anatomy`)
- Annotated SVG diagram of a TextForm showing all parts
- Detailed explanations of each part organized by role (Identity/State/Protocol/Chrome)
- Program analogy (state + instruction set + halt condition)

### Navigation split (backlog item §6)
- Split `Navigation` into three concrete subclasses: `Tabs`, `Sequence`, `Accordion`
- `Navigation` remains as the shared base class (not registered directly)
- `Sequence` has `auto_advance: bool = False` — True replaces old `chain` mode
- Removed `mode` from user-facing API; `set_nav_mode` edit action removed
- Templates still receive `mode` as context (tabs/chain/sequence/accordion) via `render_from_data`
- Registry: `tabs`, `sequence`, `accordion` registered directly; `navigation` alias for Tabs
- Legacy descriptor migration handles old type names (`tab`, `chain`, `navigation` with mode config)
- Updated all 6 page definitions: deepdive, quiz_portal, upgraded_math_test, control_flow_gallery, component_gallery, nested_tabs_test
- Updated routes.py component taxonomy (3 entries replacing 1)
- Removed mode switcher from sleek template (type IS the mode now)

### Post-split fixes
- **CSS selectors**: All `[data-form="navigation"]` in sleek.css and style.css updated to `:is([data-form="tabs"],[data-form="sequence"],[data-form="accordion"])`
- **`_CONTAINER_FORMS`** in component.py: expanded from `"navigation"` to three new names
- **Sleek wrapper template**: `form == "navigation"` → `form in ("tabs", "sequence", "accordion")` — fixed vertical sidebar titlebar rendering
- **`_find_container_children`** in page_mutations.py: updated type check from old names to new
- **`TYPE_CATALOG`** in registry.py: replaced single "navigation" entry with three entries (Tabs, Sequence, Accordion) in mutable page palette
- **Auto-key generation**: `_add_component` (page_mutations.py) and `_add_step` (navigation.py) now use `{type}-{uuid4().hex[:8]}` instead of `{type}-{n}` counter pattern, matching Component.__post_init__

### Test status
- 79/79 tests pass throughout all changes

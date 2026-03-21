# Session-2026-03-21-001

## Current State (last updated: banner unification complete)
- **Active document:** CR-110 (IN_EXECUTION v1.1)
- **Current task:** Awaiting Lead direction
- **Blocking on:** Nothing
- **Next:** Per Lead / PROJECT_STATE forward plan

## Progress Log

### Session Start
- Read previous session notes (Session-2026-03-20-002)
- Previous session completed: Documentation consolidation (README.md + ENGINE.md rewrite, TAXONOMY.md absorbed), AffordanceSource protocol refactoring (500-line monolith → 9 delegated sources), External State Provider framework (protocol, registry, bindings, test provider, end-to-end verification)
- Read PROJECT_STATE.md, SELF.md, QMS docs
- Initialized session

### Documentation Update: ENGINE.md + README.md
- ENGINE.md: 8 fixes — architecture diagram (added affordances/providers modules + table), rewrote Affordance Generation section (AffordanceSource protocol, 10 sources, recursive delegation), added provider_state leaf condition to Expression Language, new External State Providers section (protocol, registration, YAML declaration, node config, URL scheme, caching, condition evaluation), added provider_action to Action Dispatch, updated Extension Points
- README.md: 2 fixes — added affordances.py and providers.py to project structure, updated affordance description to mention AffordanceSource protocol and external providers

### Builder Banner Unification
- Problem: Create Workflow's lifecycle banner rendered in old flat style while all other workflows used schematic style
- Root cause: builder had its own `render_node()` that emitted flat string lifecycle, never called runtime's `_build_lifecycle()`. Banner JS read `state.definition` for schematic rendering, but builder's `definition` contained the workflow-being-built (empty at start), not the builder's own structure.
- Fix (engine/builder.py):
  - Parse builder's YAML into `_BUILDER_DEFN` (WorkflowDef) at module load
  - Inject implicit proceed links between sequential nodes for spine connectivity
  - Use `_build_lifecycle(_BUILDER_DEFN)` for topology-aware lifecycle (typed dicts)
  - Emit `banner_definition` with builder's own serialized structure (separate from `definition` which holds the workflow being constructed)
- Fix (simple-shared.js): Banner reads `banner_definition || definition`; `banner_definition` added to known keys
- Fix (exp-a/b/c.js): All experimental renderers updated to handle typed-dict lifecycle items
- Fix (schematic.js): `_autoCollapse` now keeps first and last spine nodes visible alongside focus node — added `_spineFirstId()` and `_spineLastId()` helpers
- Verified end-to-end: built a simple 2-node workflow via the builder API, banner shows all 4 builder steps in schematic style

### Auto-Collapse First/Last Node Fix
- `_autoCollapse` in schematic.js now protects branch-points on the path to the first and last spine nodes, ensuring start/end context is always visible
- Added `_spineFirstId()` and `_spineLastId()` helpers
- Verified with Comprehensive Change Assessment workflow (router → fork) — banner collapses correctly while keeping endpoints visible

### Condition Label Highlighting
- Router (gate) labels: taken route → green, others → gray
- Fork (split) labels: once fork is reached, all branch labels → green (all branches open)
- Added `sch-cond-active` CSS class (green border/background)
- `_condIsActive()` in renderHybrid: gate checks own line for reached nodes, split checks all sibling lines
- Canvas path also updated for non-hybrid rendering
- Bug fix: `_lineHasReached` must NOT recurse into groups (groups tag sibling membership, not parent-child) — caused all router labels to turn green

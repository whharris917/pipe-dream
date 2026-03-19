# Session-2026-03-19-001

## Current State (last updated: interactive collapse/expand committed)
- **Active document:** CR-110 (IN_EXECUTION v1.1)
- **Current task:** Schematic engine improvements — complete
- **Blocking on:** Nothing
- **Next:** Per PROJECT_STATE forward plan (ENGINE.md updates, flowchart scoping, etc.)

## Progress Log

### Session Start
- Read previous session notes (Session-2026-03-18-002)
- Read PROJECT_STATE.md, SELF.md, QMS docs
- Initialized session

### Schematic engine audit
Examined all consumers of the rendering engine to verify unified layout, content agnosticism, variable node sizes, no overlap, and no hard-coded hacks.

### Fix 1: Remove vestigial `_precomputeHeights` heuristic
- Deleted `_precomputeHeights()` and its call site
- Removed duplicate `naturalH` heuristic in `layout()` step sizing
- Updated header comment documenting the height contract

### Fix 2: Gate hexagon outline (SVG replacement for clip-path)
- `clip-path:polygon(...)` clipped CSS `border`, hiding hexagonal edges
- Replaced with inline SVG polygon (`Schematic.GATE_SVG` constant)
- Updated `_pillNodeRenderer` and `workshopNodeRenderer`

### Fix 3: Wrapper/card size mismatch in detailed flowchart
- Phase 1 measurement now uses `display:flex; flex-direction:column; width:Npx` when `nodeW` is set
- Wrapper CSS changed to `flex-direction:column` for child stretching
- Switched to `getBoundingClientRect()` for sub-pixel accuracy
- Removed explicit `height` and `overflow:hidden` from wrapper — sizes to content

### Fix 4: Completed card opacity → opaque background
- Replaced `opacity:0.85` on `.fc-card-done`/`.sch-node-completed .fc-card` with `background:#f6faf6`
- Prevents topology wires bleeding through semi-transparent cards

### Fix 5: Node handle concept (`handleY` + `handlePx`)
- Added `handleY` (fraction, default 0.5) and `handlePx` (fixed pixels, overrides handleY)
- Wires/bars/condition labels attach at handle point; nodes hang below
- `wireOff(rowH)` helper in `layout()` and `drawSchematic()` picks the right mode
- Detailed flowchart measures `.fc-card-head` height, passes `handlePx = headerH / 2`
- Banner/workshop unchanged (default handleY=0.5)

### Fix 6: Remove purple debug overlay
- Removed `::after` pseudo-elements from `.sch-node-wrap` and `.sch-cond-wrap`

### Feature: Interactive collapse/expand in workshop
- Added `data-node-id` and `data-node-kind` attributes to `.sch-node-wrap` divs in renderHybrid Phase 4
- Workshop: `pruneSpine(spine, collapsed)` deep-clones spine, removing routes/branches for collapsed IDs
- Click handler via event delegation on `[data-node-kind="branch-point"]`
- Visual affordance: `cursor:pointer` on branch-points, `.sch-bp-collapsed` class (dashed border + opacity)

### Engine: Collapse-wire support
- `flattenSpine`: zero-route/branch gates/splits stay on current line with `{ kind: 'collapse-wire' }` element instead of splitting into disconnected lines
- `layout()`: collapse-wire positioned as 3x normal wire width
- `drawSchematic()`: horizontal wires drawn in segments — solid normally, dashed (6,4) through collapse-wire ranges
- Collapsed splits retain merge node on the same line

### Bug fix: _refCounter collision with nested branch-points
- Collapsed branch-points no longer get a `groupId` (they don't branch)
- `treeOrderLines` `find()` now requires `e.groupId` to match, skipping collapsed branch-points
- Prevents expanded branch-point on the same line from being shadowed by a preceding collapsed one

### Commits (this session)
- Submodule `e2b398f`: Engine hardening (heuristic removal, gate SVG, wrapper fix)
- Submodule `8566490`: Node handles, opacity fix, debug overlay removal
- Submodule (pending): Interactive collapse/expand + collapse-wire + groupId fix

# Session-2026-03-19-001

## Current State (last updated: session complete)
- **Active document:** CR-110 (IN_EXECUTION v1.1)
- **Current task:** Session complete
- **Blocking on:** Nothing
- **Next:** Per PROJECT_STATE forward plan (ENGINE.md updates, flowchart scoping, etc.)

## Progress Log

### Session Start
- Read previous session notes (Session-2026-03-18-002)
- Read PROJECT_STATE.md, SELF.md, QMS docs
- Initialized session

### Schematic engine audit
Examined all consumers of the rendering engine to verify unified layout, content agnosticism, variable node sizes, no overlap, and no hard-coded hacks. Found and fixed two issues.

### Fix 1: Remove vestigial `_precomputeHeights` heuristic
- Deleted `_precomputeHeights()` and its call site in `renderWorkflow()`
- Removed duplicate `naturalH` heuristic in `layout()` step sizing
- Updated header comment documenting the height contract

### Fix 2: Gate hexagon outline (SVG replacement for clip-path)
- `clip-path:polygon(...)` clipped CSS `border`, hiding hexagonal < and > edges
- Replaced with inline SVG polygon (`Schematic.GATE_SVG` constant)
- `preserveAspectRatio="none"` + `vector-effect:non-scaling-stroke`
- Updated `_pillNodeRenderer` (agent_observer) and `workshopNodeRenderer` (workshop)

### Fix 3: Wrapper/card size mismatch in detailed flowchart
- Phase 1 measurement now uses `display:flex; flex-direction:column; width:Npx` when `nodeW` is set
- Wrapper CSS changed to `flex-direction:column` for child stretching
- Switched to `getBoundingClientRect()` for sub-pixel accuracy
- Removed explicit `height` and `overflow:hidden` from wrapper — sizes to content

### Fix 4: Completed card opacity → opaque background
- Replaced `opacity:0.85` on completed cards with `background:#f6faf6`
- Prevents topology wires bleeding through semi-transparent cards

### Fix 5: Node handle concept (`handleY` + `handlePx`)
- Added `handleY` (fraction, default 0.5) and `handlePx` (fixed pixels, overrides handleY)
- `wireOff(rowH)` helper in `layout()` and `drawSchematic()`
- Detailed flowchart measures `.fc-card-head` height, passes `handlePx = headerH / 2`
- Wires pass through card headers; card bodies hang below

### Fix 6: Remove purple debug overlay
- Removed `::after` pseudo-elements from `.sch-node-wrap` and `.sch-cond-wrap`

### Feature: Interactive collapse/expand (engine service)
- Added `data-node-id` and `data-node-kind` attributes to `.sch-node-wrap` divs
- `_pruneSpine(spine, collapsed)` deep-clones spine, removing routes/branches for collapsed IDs
- `_setupCollapsible()` attaches one-time delegated click handler on the container
- Collapsible is default-on (`opts.collapsible !== false`)
- Visual affordance: `cursor:pointer` on branch-points, `.sch-bp-collapsed` class (dashed border)
- Workshop simplified to just pass `nodeRenderer` — interactivity is automatic

### Engine: Collapse-wire support
- `flattenSpine`: zero-route/branch gates/splits stay on current line with `{ kind: 'collapse-wire' }`
- Collapsed branch-points get no `groupId` — prevents shadowing expanded branch-points on same line
- `treeOrderLines` `find()` requires `e.groupId`, skipping collapsed nodes
- `layout()`: collapse-wire positioned as 3x normal wire width
- `drawSchematic()`: horizontal wires drawn in segments — solid normally, dashed through collapse-wire ranges
- Collapsed splits retain merge node on the same line

### Feature: Auto-collapse (`focusNode`)
- `_spineContains(spine, targetId, ancestors)` — recursive walk finding ancestor branch-points
- `_allBranchPointIds(spine, out)` — collects every gate/split ID
- `_autoCollapse(spine, focusId)` — collapses all BPs not on the path to focusId
- `renderHybrid` applies auto-collapse before rendering when `opts.focusNode` is set
- Preserves `originalSpine` for click handler so users can expand beyond auto-collapsed state
- Workflow banner passes `focusNode: current` for contextual summary

### Renderer promotion
- Promoted Experimental-D to Simple renderer (4 variants: light/dark × default/verbose)
- Moved Simple block to between Raw and Experimental-A in registration order
- Deleted old Simple renderers (basic HTML, no workflow visualization)
- Deleted Schematic renderer (exp-e) — superseded by Simple's banner
- Updated `_ALL_RENDERERS` in app.py
- Agent Observer now defaults to first renderer after Raw (Simple Light)
- Fixed missing `/*` comment opener after sed block move

### Workshop in sidebar
- Added Workshop link to sidebar navigation in `base.html`

### Commits (this session)
- Submodule `e2b398f`: Engine hardening (heuristic removal, gate SVG, wrapper fix)
- Submodule `8566490`: Node handles, opacity fix, debug overlay removal
- Submodule `dbf8442`: Interactive collapse/expand + collapse-wire + groupId fix
- Submodule `7d27817`: Promote Exp-D to Simple, remove old Simple + Schematic
- Submodule `c9f2032`: Fix missing comment opener
- Submodule `807a93c`: Default to Simple renderer
- Submodule `eb0cb96`: Workshop in sidebar nav

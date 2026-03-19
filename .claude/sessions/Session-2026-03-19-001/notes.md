# Session-2026-03-19-001

## Current State (last updated: schematic fixes committed)
- **Active document:** CR-110 (IN_EXECUTION v1.1)
- **Current task:** Schematic engine audit + fixes — complete
- **Blocking on:** Nothing
- **Next:** Per PROJECT_STATE forward plan (ENGINE.md updates, flowchart scoping, etc.)

## Progress Log

### Session Start
- Read previous session notes (Session-2026-03-18-002)
- Read PROJECT_STATE.md, SELF.md, QMS docs
- Initialized session

### Schematic engine audit
Examined all consumers of the rendering engine (banner, detailed flowchart, exp-e standalone, workshop) to verify:
1. All use the same layout engine (`Schematic.renderHybrid`) — confirmed
2. Engine is content-agnostic (nodeRenderer callback) — confirmed
3. Variable node sizes handled via DOM measurement — confirmed
4. No overlap — confirmed
5. No hard-coded hacks — two issues found and fixed

### Fix 1: Remove vestigial `_precomputeHeights` heuristic
- Deleted `_precomputeHeights()` function and its call site in `renderWorkflow()`
- Removed duplicate `naturalH` heuristic in `layout()` step sizing (same `titleLines.length * 15 + 10` magic numbers)
- Height contract: `renderHybrid` measures DOM heights via `setSpineHeights()`; direct `renderWorkflow` callers must call `setSpineHeights()` themselves or accept uniform `C.stepH` default
- Updated header comment documenting the contract

### Fix 2: Gate hexagon outline (SVG replacement for clip-path)
- **Problem:** `clip-path:polygon(...)` on `.sch-bp-gate` clipped the CSS `border`, making the hexagonal `<` and `>` edges invisible
- **Fix:** Replaced clip-path with inline SVG polygon (`Schematic.GATE_SVG` constant). SVG handles fill + stroke correctly on arbitrary polygons. `preserveAspectRatio="none"` stretches to container; `vector-effect:non-scaling-stroke` keeps stroke constant.
- CSS: `.sch-bp-gate` now transparent background/border; `.sch-bp-gate-bg polygon` handles fill/stroke including execution state colors
- Updated `_pillNodeRenderer` (agent_observer.html) and `workshopNodeRenderer` (workshop.html) to use `Schematic.GATE_SVG`

### Fix 3: Wrapper/card size mismatch in detailed flowchart
- **Problem:** Purple debug overlay (`.sch-node-wrap`) was larger than card content in fixed-width mode (`nodeW: 378`)
- **Root cause 1:** Phase 1 measurement used `display:inline-flex` (shrink-wrap) even when `nodeW` was set. Cards measured at natural width, but rendered at 378px — different text wrapping → different heights.
- **Root cause 2:** Wrapper used `display:flex` (row direction) so children didn't stretch to fill wrapper width.
- **Fix:** Measurement now uses `display:flex; flex-direction:column; width:Npx` when `nodeW` is set, matching the render context. Wrapper CSS changed to `flex-direction:column` so children stretch to fill width.
- Also switched from `offsetHeight`/`offsetWidth` to `getBoundingClientRect()` for sub-pixel accuracy.
- Removed explicit `height` and `overflow:hidden` from wrapper inline style — wrapper now sizes to content, eliminating measurement-vs-render context mismatches entirely.

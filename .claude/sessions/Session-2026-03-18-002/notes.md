# Session-2026-03-18-002

## Current State (last updated: renderHybrid complete + pushed)
- **Active document:** CR-110 (IN_EXECUTION v1.1)
- **Current task:** Unified schematic rendering — complete
- **Blocking on:** Nothing
- **Next:** Remove purple debug overlay, further polish

## Progress Log

### Session Start
- Read previous session notes (Session-2026-03-18-001)
- Read PROJECT_STATE.md, SELF.md, QMS docs
- Initialized session

### Bug Fix: Flowchart rendering (commit 63593f5)
Three fixes for the schematic-based detailed flowchart:
1. **Implicit proceed targets**: `_serialize_definition()` in renderer.py now resolves implicit sequential targets
2. **Opaque card backgrounds**: Added `background:#fff` to base `.fc-card` CSS
3. **wiresOnly mode**: Added `opts.wiresOnly` to `drawSchematic()` for topology-only canvas

### Unified renderHybrid (commit 968be74)
Implemented `Schematic.renderHybrid()` — single entry point for HTML-over-canvas rendering:
- Callers provide `nodeRenderer(item, status)` callback returning HTML
- Engine handles: measure → setSpineHeights → layout → draw canvas wires → position HTML divs
- New public API: `renderHybrid`, `setSpineHeights`, `_nodeStatus`
- Migrated all 4 consumers: banner, detailed flowchart, exp-e standalone, workshop

### Multi-line pill titles (commit b6fa67c)
- Changed `.sch-pill` and `.sch-bp` from `height:30px; white-space:nowrap` to `min-height:30px; white-space:pre-line`
- Newlines in titles now render as actual line breaks, pills grow to fit

### CSS consolidation (commit 80cd646)
- Moved all schematic node CSS from duplicated template-local copies into `schematic.js` as `_CSS`
- Injected once into `document.head` on first `renderHybrid()` call via `_injectCSS()`
- Single source of truth — observer and workshop now render identically

### DOM width measurement (commit 2cacb1c)
- Added width measurement in Phase 1 using `display:inline-flex` for shrink-wrapping
- Phase 2b adjusts item `x`/`w` to center measured width around layout-computed center
- Fixes fork branch-point divs being wider than their rendered content

### Measurement context alignment (commit e0ba1c6)
- Changed measurement wrapper from `display:inline-block` to `display:inline-flex`
- Added `display:flex` to `.sch-node-wrap` CSS
- Both contexts now use flexbox, eliminating inline strut/baseline height discrepancies

### Explicit wrap height (commit 80c04c6)
- Set explicit `height` and `overflow:hidden` on wrap div inline style
- Guarantees wrap matches measured height exactly despite any CSS context differences
- Confirmed via purple debug overlay that no node boxes overlap
- Removed debug `console.log` from renderHybrid

### Commits (this session)
- `63593f5` — Fix flowchart rendering: implicit targets + opaque cards + wiresOnly
- `968be74` — Unified HTML-over-canvas schematic rendering via renderHybrid
- `b6fa67c` — Fix pill nodes to render multi-line titles correctly
- `80cd646` — Move schematic node CSS into schematic.js — single source of truth
- `2cacb1c` — Measure actual DOM widths for node positioning in renderHybrid
- `e0ba1c6` — Fix node overlap: align measurement and render formatting contexts
- `80c04c6` — Fix node wrap height: explicit height + overflow:hidden

# Session-2026-03-15-002

## Current State (last updated: pre-commit)
- **Active document:** CR-110 (IN_EXECUTION v1.1)
- **Current task:** Experimental-D renderer — visual flowchart for workflow definitions
- **Blocking on:** Nothing
- **Next:** Awaiting direction from Lead

## Progress Log

### Session Start
- Read previous session notes (Session-2026-03-15-001)
- Read SELF.md, QMS docs (Policy, START_HERE)
- Initialized session

### Experimental-D Renderer — Visual Flowchart

**Goal:** Replace the text-heavy Simple blueprint renderer with a more visually intuitive, less text-based representation of workflow node definitions. Constraint: bijective map from JSON — all meaning must be projected, even if via non-text signals.

**Iteration 1: HTML cards + CSS (vd-* classes)**
- Created Experimental-D as a copy of Simple (4 variants: default/verbose × light/dark)
- Replaced `wfRenderDefinition` with custom `expDRenderDefinition` using:
  - SVG field type icons (text/boolean/select), color-coded chips
  - Lock/key icons for proceed gates
  - Arrow chips for navigation, checkmark/loop chips for actions
  - Eye icon for show_all_fields flag
  - Instruction text with info-circle icon
  - Empty sections omitted entirely
- Fixed CSS scoping (`_scopeCSS` regex didn't work on concatenated strings — switched to `.vd-` prefix match)

**Iteration 2: Graph layout attempt (HTML + SVG overlay)**
- Changed layout to horizontal flex-wrap with SVG edge overlay
- Built `expDDrawEdges` post-render function measuring DOM positions
- Hit SVG namespace issue (`innerHTML` on SVG elements doesn't work) — fixed with DOMParser, then temp div approach
- Hit JSON attribute escaping issue — fixed with base64 encoding
- Edges rendered but layout was fragile: hardcoded card widths, truncated text, DOM measurement timing issues

**Iteration 3: Pure SVG flowchart (abandoned)**
- Attempted rendering everything as SVG (nodes + edges in one coordinate system)
- Eliminated DOM measurement dependency but introduced worse problem: manually computing pixel positions for every text element
- Fundamentally unscalable — every layout constant change required re-tuning dozens of offsets
- Font sizes inconsistent, text overflow, labels clipped

**Iteration 4: Path B — HTML cards + computed absolute positioning + SVG edge layer (current)**
- Clean rewrite: HTML for node card content (natural text wrapping via CSS), SVG only for edges
- Card positions computed from data and assigned via `position:absolute` + inline `left/top/width`
- Height estimation on first render, then `_fcFixLayout` post-render correction:
  - Measures actual card heights via `offsetHeight`
  - Reflows all card positions
  - Rebuilds edge SVG from scratch with corrected slot positions
- Edges stored as base64 JSON on `data-edges` attribute for post-render access
- Edge types:
  - Forward (green solid): bottom-center → top-center cubic Bézier
  - Back (blue dashed): top-left of source → bottom-left of target, arcing left
  - Goto (purple dashed): right side of source → right side of target, arcing right
- Tuned: card width 630px, margins 140px, uniform opacity 0.6 for secondary text, darker card header backgrounds, back-edge label positioning

**Files changed:**
- `wfe-ui/app.py` — added exp-d renderer IDs to `_ALL_RENDERERS`
- `wfe-ui/templates/agent_observer.html` — Experimental-D renderer (4 variants) with:
  - `expDRenderDefinition()` — flowchart builder
  - `_fcNodeCard()` — HTML card renderer per node
  - `_fcBuildEdgeSvg()` — SVG edge generator
  - `_fcEdges()` — edge collector from node data
  - `_fcFixLayout()` — post-render height correction + SVG rebuild
  - `_expDPage()` — shared page renderer (default/verbose)
  - CSS: `EXP_D_FC_CSS` (structural), `EXP_D_FC_LIGHT`/`EXP_D_FC_DARK` (theme tokens)
  - `_scopeFC()` — CSS scoping helper

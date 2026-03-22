# Session-2026-03-22-001

## Current State (last updated: renderer cleanup + commit)
- **Active document:** CR-110 (IN_EXECUTION v1.1)
- **Blocking on:** Nothing
- **Next:** Continue affordance framework — anchor flow/navigation affordances, implement focus mechanism

## Progress Log

### Session Start
- Read previous session notes (Session-2026-03-21-005)
- Read PROJECT_STATE.md, START_HERE.md, SELF.md

### Design Discussion: Affordance Framework
- Deep-dive into HATEOAS, REST, hypermedia formats, affordance theory (Gibson/Norman), agent-friendly API design
- Developed the "visual cortex for the agent" framing — salience detection, perceptual grouping, gaze management, pre-action verification
- Key concepts: object tree with focus controls, two focus modes (by object, by salience), parameterized affordances vs child objects, sticky focus, snap-to-next, autonomy spectrum
- Documents: `affordance-design-discussion.md`, `affordance-categories.md`

### Implementation 1: Unified Field-Affordance Response
- Each field in `state.fields` now carries its own affordance inline (`field.affordance`)
- Top-level `affordances` retains only non-field affordances
- Labels removed from field affordances (redundant when inline with field)
- Files: renderer.py, affordances.py, app.py, human-renderer.js

### Implementation 2: Table Affordance Anchoring
- Table affordances anchored to objects:
  - Table-level (add_column, add_row, remove_row) → `state.table.affordances`
  - Per-column (rename, set_type, remove, set_cell, type-specific) → `state.table.columns[i].affordances`
  - Properties (set_property) → `state.table.properties.affordances`
- Column-specific affordances decomposed: one parameterized affordance → N per-column affordances with col pre-filled
- Labels removed from table affordances
- Generic `wfRenderAffordances()` function ensures faithful projection — every anchored affordance gets an interactive control
- Files: affordances.py, renderer.py, app.py, human-renderer.js

### Implementation 3: Renderer Cleanup
- Deleted ~160 lines of dead code: `wfRenderPage()` and `wfRenderPageDefault()` (never registered)
- Renamed all Exp-D references:
  - `_expDPage` → `_humanPage`, `expDRenderDefinition` → `humanRenderDefinition`
  - `expDRenderStateProps` → `humanRenderStateProps`, `_expDSchematicFlowchart` → `_schematicFlowchart`
  - `EXP_D_FC_CSS` → `FC_CSS`, `EXP_D_FC_LIGHT` → `FC_LIGHT`
- Merged `simple-shared.js` + `simple.js` → single `human-renderer.js`
- Renamed files: `raw.js` → `agent-renderer.js`, label changed to "Agent"
- Final renderer file structure: `registry.js`, `agent-renderer.js`, `human-renderer.js`, `portal.js`
- All label references in renderers made resilient to missing labels (fallback to URL-derived action name)

### Backlog Addition
- AffordanceSource reorganization: regroup by agent experience (data entry / forward / lateral / terminal / external) rather than YAML primitive type

# Session-2026-03-18-001

## Current State (last updated: detailed flowchart integration)
- **Active document:** CR-110 (IN_EXECUTION v1.1)
- **Current task:** Schematic renderer integration — detailed flowchart working
- **Blocking on:** Nothing
- **Next:** Polish detailed flowchart (width, edge features), commit cycle

## Progress Log

### Session Start
- Read previous session notes (Session-2026-03-16-001)
- Initialized session

### Y-Assignment Redesign (workshop.html)
- Replaced `reorderContinuations` with `treeOrderLines` — recursive tree-based Y-assignment
- Overlapping Y space for sequential BPs on the same spine
- Layout simplified: Y from `_assignedY`, no `nextY` counter
- Convergence anchor fix for BP-first continuations
- Convergence/divergence bar horizontal displacement (driven by widest cond label)
- Group rejoin label stored on tags during flattening (fixes null lookup)
- 4 stress test workflows added + convergence cascade test

### Schematic Module Extraction
- Extracted rendering pipeline from workshop.html into `static/schematic.js`
- `Schematic` namespace: definitionToSpine, flattenSpine, treeOrderLines, layout, drawSchematic, renderWorkflow
- `definitionToSpine()` converter: flat node-list → hierarchical spine with router convergence detection
- Execution state coloring: current (blue), completed (green), pending (gray)
- Node ID propagation through entire pipeline

### Observer Integration
- Registered `exp-e` (Schematic) renderer in agent_observer.html
- Replaced ELK.js lifecycle banner with schematic canvas banner in Exp-D
- Default route label "Default" for routes without when conditions

### Detailed Flowchart (Exp-D)
- Replaced ELK-based layout with schematic spatial arrangement engine
- HTML node cards (`_fcNodeCard`) positioned at schematic-computed coordinates
- Canvas topology layer (same `drawSchematic` engine as workshop) behind cards via z-index
- **Variable row heights**: native support in the layout engine
  - `_rowH` per line computed from tallest element
  - `_precomputeHeights` for multi-line titles
  - Heights propagated through flattener for steps, branch-points, and merge nodes
  - Configurable `lineGap` (16px for cards, 4px default for pills)
- **Measure-first approach**: cards rendered in hidden container to get actual heights, set on spine before layout — correct positions from the first pass, no post-render fixup
- Cards vertically centered in their rows using measured heights
- Continuous horizontal wires (center-to-center through nodes, not edge-to-edge)
- Execution state CSS: `fc-card-current` (blue border + glow), `fc-card-done` (green border)
- Workshop "Variable Row Heights" test workflow + multi-line titles in Pharmaceutical Pipeline

### Key Files Modified
- `wfe-ui/static/schematic.js` — shared module (created, then iteratively enhanced)
- `wfe-ui/templates/workshop.html` — uses shared module, test workflows
- `wfe-ui/templates/agent_observer.html` — exp-e renderer, schematic banner, detailed flowchart
- `wfe-ui/app.py` — added "exp-e" to _ALL_RENDERERS

### Commits
- Submodule: qms-workflow-engine `83dab48` (module extraction + observer integration)
- Parent: pipe-dream `af0ca02`
- Pending: variable row heights + detailed flowchart integration

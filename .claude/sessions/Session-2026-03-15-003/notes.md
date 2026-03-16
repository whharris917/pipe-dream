# Session-2026-03-15-003

## Current State (last updated: second commit)
- **Active document:** CR-110 (IN_EXECUTION v1.1)
- **Current task:** Parallel primitives + Exp-D renderer + ELK banner — COMPLETE
- **Blocking on:** Nothing
- **Next:** ENGINE.md/TAXONOMY.md updates; use builder to create complex workflow

## Progress Log

### Session Start
- Read previous session notes (Session-2026-03-15-002)
- Read SELF.md, PROJECT_STATE.md, QMS docs (Policy, START_HERE)
- Initialized session

### New Engine Primitives (Router, Fork, Merge)

Three new control-flow primitives:
1. `router` — automatic multi-way conditional branching (no agent interaction)
2. `fork` — parallel branch split with branch switching and completion tracking
3. `merge` — implicit convergence via fork.merge reference

**Files changed:** runtime/schema.py, runtime/actions.py, runtime/renderer.py, runtime/__init__.py, builder_handler.py, agent_create_workflow.yaml

**Demo workflow:** parallel-investigation.yaml — exercises all three primitives across Low/Medium-High/Critical severity paths. Distinct node IDs per fork (no sharing between forks).

**Commit:** c28fb75 (submodule)

### Exp-D Renderer — Grid Layout with Orthogonal Edges

Complete rewrite of flowchart visualization:
- Grid-based layout with uniform card widths (378px)
- Row-aligned fork branches
- Orthogonal-only edges (no curves)
- Fork/merge bus bar pattern (trunk + bar + drops, no overlap)
- Per-node Y staggering for right-side edges
- Global channel staggering for back edges (30px separation)
- Router/fork badges and visual distinction on cards
- Select field options rendered vertically

### Edge Visual Language
- Solid green — normal flow (forward, fork, merge)
- Dashed orange — conditional routing (router)
- Dotted purple — jumps (goto/proceed with target)
- Dotted blue — backward navigation (back)

### ELK.js Integration — Banner Flowchart

Integrated ELK.js (Eclipse Layout Kernel) via CDN for the lifecycle banner:
- Sugiyama layered algorithm: automatic layer assignment, crossing minimization, coordinate placement
- Horizontal layout (direction: RIGHT) with orthogonal edge routing
- Fork branches collapsed into single placeholder cards with stacked branch labels (green dashed border)
- Only forward-flow edges fed to ELK (back/goto/router excluded from banner)
- Uniform gray edges in banner (no color/dash complexity)
- Pure SVG rendering (no HTML overlay)
- Async: ELK returns positions via promise, banner fills in after page load
- SVG at native size, overflow:hidden on container (no scrollbars)

### Other Fixes
- Added workflow_title to agent_create_cr.yaml (was showing "Untitled")
- Fixed go_back navigation edge collection inside fork branch nodes
- Fixed UTF-8 encoding issue in parallel-investigation YAML instruction text

### Commit Log
1. c28fb75 — Router/fork/merge primitives + grid Exp-D flowchart
2. 8c7405c — SVG banner + topology-aware lifecycle + edge visual language
3. (current) — ELK.js banner + fork collapse + CR title fix

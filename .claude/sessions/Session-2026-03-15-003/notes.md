# Session-2026-03-15-003

## Current State (last updated: commit)
- **Active document:** CR-110 (IN_EXECUTION v1.1)
- **Current task:** Parallel paths, automatic routing, merge primitives — COMPLETE
- **Blocking on:** Nothing
- **Next:** Use builder to create complex workflow; ENGINE.md/TAXONOMY.md updates

## Progress Log

### Session Start
- Read previous session notes (Session-2026-03-15-002)
- Read SELF.md, PROJECT_STATE.md, QMS docs (Policy, START_HERE)
- Initialized session

### New Engine Primitives (Router, Fork, Merge)

**Three new primitives added to the workflow engine:**

1. `router` — automatic multi-way conditional branching (no agent interaction). Evaluates conditions top-to-bottom, advances to first match. Mutually exclusive with proceed/fork.
2. `fork` — parallel branch split. Agent works one branch at a time, can switch. All branches must complete before merge activates. Mutually exclusive with proceed/router.
3. `merge` — implicit via `fork.merge` reference. Regular node that becomes available when all branches complete.

**Schema (runtime/schema.py):**
- Added `RouteDef`, `BranchDef`, `ForkDef` dataclasses
- Added `router` and `fork` fields to `NodeDef`

**Action dispatch (runtime/actions.py):**
- `_route()` — evaluate router conditions, advance to first match
- `_activate_fork()` — initialize fork_state, activate branches
- `_branch_proceed()` — proceed within fork, complete branches, auto-switch, merge
- `_switch_branch()` — switch between active branches
- `_enter_node()` — handles auto-routing and auto-advance on node entry (recursion limit)
- `_go_back()` updated for fork awareness

**Renderer (runtime/renderer.py):**
- `_serialize_definition()` — serializes WorkflowDef for observer UI (Exp-D flowchart)
- Definition included in rendered state for all workflows
- Fork state exposed in rendered state dict
- Fork affordance + branch switch affordances

**Builder (builder_handler.py):**
- New node modes: standard, router, fork
- Actions: set_node_mode, add_route, remove_route, set_fork_merge, set_fork_label, add_branch, remove_branch, set_fork_gate
- Updated _validate, _publish, _summary for new primitives

**Demo workflow:** `data/custom_workflows/parallel-investigation.yaml`
- Intake → Severity Router → Low/Medium-High/Critical paths
- Medium/High: 2-branch fork (Technical + Compliance)
- Critical: 3-branch fork (Technical + Compliance + Executive)
- All paths converge at Final Review
- Distinct node IDs per fork path (no shared nodes between forks)

### Exp-D Renderer — Grid Layout with Orthogonal Edges

Complete rewrite of the flowchart visualization:

**Layout algorithm:**
- Grid-based: each node gets (row, col) coordinates
- All cards are uniform width (378px)
- Fork branches spread across columns, canvas expands to fit
- Single-column cards centered within canvas
- Row-aligned: cards at same row index across branches share top Y
- Row height determined by tallest card in that row

**Edge routing (orthogonal only — no curves):**
- Forward (same column): straight vertical line
- Forward (cross-column): Z-shaped with right angles
- Fork: trunk + horizontal bus bar + individual vertical drops (no overlap)
- Merge: individual vertical rises + horizontal bus bar + trunk (no overlap)
- Router/goto: route along right margin in stacked channels, staggered Y per node
- Back: route along left margin with right angles

**Per-node Y staggering:** All right-side connections (incoming + outgoing) on a card are distributed across 20%-80% of card height so no two edges share a horizontal segment.

**Labels:** Positioned at arrow endpoints, offset 14px from arrowhead to avoid overlap with marker.

**Card rendering enhancements:**
- Router badge + route listing on router cards
- Fork badge + branch listing on fork cards
- Select field options rendered vertically (not pipe-delimited)

### Testing
- All three severity paths tested end-to-end (Low/Medium/Critical)
- Branch switching verified
- Merge on all-branches-complete verified
- Backward compatibility: all 5 existing workflows load/render correctly
- Builder: router and fork creation tested programmatically
